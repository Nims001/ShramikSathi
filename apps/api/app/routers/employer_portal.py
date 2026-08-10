"""Employer portal: share codes, linking, and dual-consensus log approval.

Flow: a worker generates a unique share code (stored only as a SHA-256 hash)
and shares it with their employer. The employer's portal account enters that
code to create an `EmployerLink`, which unlocks the worker's work logs. Logs
signed by the worker (`pending_employer`) can be approved — the employer
verifies the worker's digital signature and countersigns the same record —
or rejected with a short message the worker sees and can act on.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..deps import current_user
from ..models import Employer, EmployerLink, User, WorkLog, WorkLogSignatureEvent
from ..schemas.employer_portal import (
    EmployeeLog,
    LinkRequest,
    LinkedEmployee,
    PendingLog,
    RejectRequest,
    ShareCodeResponse,
)
from ..security import generate_share_code as _new_share_code
from ..security import hash_share_code
from .. import crypto
from ..services import signing

router = APIRouter(prefix="/api", tags=["employer-portal"])


def _require_employer(user: User) -> None:
    if user.role != "employer":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="This action is only available to employer accounts",
        )


@router.post("/me/share-code", response_model=ShareCodeResponse)
async def generate_share_code(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareCodeResponse:
    """Generate (or rotate) the worker's share code. Returned once, plaintext."""
    if user.role == "employer":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Employer accounts do not share a code",
        )
    code = _new_share_code()
    user.share_code_hash = hash_share_code(code)
    await db.commit()
    return ShareCodeResponse(code=code)


@router.post("/employer-portal/link", response_model=LinkedEmployee, status_code=status.HTTP_201_CREATED)
async def link_employee(
    payload: LinkRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> LinkedEmployee:
    """Add a worker to this employer's portal by their share code."""
    _require_employer(user)

    digest = hash_share_code(payload.code)
    employee = (
        await db.execute(
            select(User).where(User.share_code_hash == digest, User.role != "employer")
        )
    ).scalar_one_or_none()
    if employee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Invalid share code")
    if employee.id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="You cannot link to yourself")

    link = (
        await db.execute(
            select(EmployerLink).where(
                EmployerLink.employer_user_id == user.id,
                EmployerLink.employee_user_id == employee.id,
            )
        )
    ).scalar_one_or_none()
    if link is None:
        link = EmployerLink(
            employer_user_id=user.id,
            employee_user_id=employee.id,
            note=payload.note,
        )
        db.add(link)
        await db.commit()
        await db.refresh(link)

    log_count = await _count_logs(db, employee.id)
    return LinkedEmployee(
        employee_id=employee.id,
        username=employee.username,
        note=link.note,
        linked_at=link.created_at,
        log_count=log_count,
    )


@router.get("/employer-portal/employees", response_model=list[LinkedEmployee])
async def list_linked_employees(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LinkedEmployee]:
    """All workers this employer has linked, with their log counts."""
    _require_employer(user)

    rows = (
        await db.execute(
            select(EmployerLink, User)
            .join(User, User.id == EmployerLink.employee_user_id)
            .where(EmployerLink.employer_user_id == user.id)
            .order_by(EmployerLink.created_at.desc())
        )
    ).all()

    employees: list[LinkedEmployee] = []
    for link, employee in rows:
        employees.append(
            LinkedEmployee(
                employee_id=employee.id,
                username=employee.username,
                note=link.note,
                linked_at=link.created_at,
                log_count=await _count_logs(db, employee.id),
            )
        )
    return employees


@router.get("/employer-portal/employees/{employee_id}/logs", response_model=list[EmployeeLog])
async def employee_logs(
    employee_id: UUID,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EmployeeLog]:
    """Full view of a linked worker's logs (breaks, hours, pay, signatures)."""
    _require_employer(user)
    await _require_link(db, user.id, employee_id)

    rows = (
        await db.execute(
            select(WorkLog, Employer)
            .join(Employer, Employer.id == WorkLog.employer_id)
            .where(WorkLog.user_id == employee_id)
            .order_by(WorkLog.log_date.desc())
        )
    ).all()

    return [_to_employee_log(log, employer) for log, employer in rows]


@router.get("/employer-portal/pending-logs", response_model=list[PendingLog])
async def pending_logs(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PendingLog]:
    """All signed records awaiting this employer's approval, across workers.

    Powers the "pending approvals" inbox on the portal. Oldest records come
    first so the most overdue is reviewed first. The worker's signature is
    re-verified at decision time (approve/reject), so this list stays cheap.
    """
    _require_employer(user)

    rows = (
        await db.execute(
            select(WorkLog, Employer, User)
            .join(EmployerLink, EmployerLink.employee_user_id == WorkLog.user_id)
            .join(Employer, Employer.id == WorkLog.employer_id)
            .join(User, User.id == WorkLog.user_id)
            .where(
                EmployerLink.employer_user_id == user.id,
                WorkLog.approval_status == "pending_employer",
            )
            .order_by(WorkLog.log_date.asc(), WorkLog.created_at.asc())
        )
    ).all()

    return [
        PendingLog(
            **_to_employee_log(log, employer).model_dump(),
            employee_id=log.user_id,
            username=employee.username,
        )
        for log, employer, employee in rows
    ]


@router.post(
    "/employer-portal/employees/{employee_id}/logs/{log_id}/approve",
    response_model=EmployeeLog,
)
async def approve_log(
    employee_id: UUID,
    log_id: UUID,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> EmployeeLog:
    """Employer approves a signed record and countersigns the same hash.

    The worker's signature is re-verified first (recomputed hash + public key),
    so an altered or forged record can never be approved. The employer's own
    RSA-2048 signature is then added, completing the dual-consensus record.
    """
    _require_employer(user)
    await _require_link(db, user.id, employee_id)

    log = await _owned_employee_log(db, log_id, employee_id)
    if log.approval_status != "pending_employer":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Only records awaiting employer approval can be approved",
        )

    employee = await db.get(User, log.user_id)
    if employee is None or not signing.verify_log_signature(log, employee):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="The worker's signature on this record could not be verified",
        )

    await signing.ensure_signing_keys(db, user)
    log.employer_signature = crypto.sign(log.content_hash, user.signing_private_key_enc)
    log.employer_signed_at = datetime.now(timezone.utc)
    log.employer_decision_at = log.employer_signed_at
    log.approval_status = "approved"
    log.rejection_reason = None

    db.add(
        WorkLogSignatureEvent(
            worklog_id=log.id,
            kind="employer_approve",
            actor_user_id=user.id,
            submission_version=log.submission_version,
            content_hash=log.content_hash,
            signature=log.employer_signature,
            canonical_payload=signing.worklog_signing_dict(log),
        )
    )
    await db.commit()
    await db.refresh(log)
    employer = await db.get(Employer, log.employer_id)
    return _to_employee_log(log, employer)


@router.post(
    "/employer-portal/employees/{employee_id}/logs/{log_id}/reject",
    response_model=EmployeeLog,
)
async def reject_log(
    employee_id: UUID,
    log_id: UUID,
    payload: RejectRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> EmployeeLog:
    """Employer rejects a signed record with a short message to the worker.

    The worker can then edit the record (e.g. fix a mistake) and resubmit,
    which creates a new submission version with a fresh employee signature.
    """
    _require_employer(user)
    await _require_link(db, user.id, employee_id)

    log = await _owned_employee_log(db, log_id, employee_id)
    if log.approval_status != "pending_employer":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Only records awaiting employer approval can be rejected",
        )

    reason = payload.reason.strip()
    if len(reason) < 3:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please add a short reason for the rejection",
        )

    log.approval_status = "rejected"
    log.rejection_reason = reason
    log.employer_decision_at = datetime.now(timezone.utc)

    db.add(
        WorkLogSignatureEvent(
            worklog_id=log.id,
            kind="employer_reject",
            actor_user_id=user.id,
            submission_version=log.submission_version,
            content_hash=log.content_hash,
            rejection_reason=reason,
            canonical_payload=signing.worklog_signing_dict(log),
        )
    )
    await db.commit()
    await db.refresh(log)
    employer = await db.get(Employer, log.employer_id)
    return _to_employee_log(log, employer)


def _to_employee_log(log: WorkLog, employer: Employer | None) -> EmployeeLog:
    return EmployeeLog(
        log_id=log.id,
        log_date=log.log_date,
        report_time=log.report_time,
        scheduled_end_time=log.scheduled_end_time,
        scheduled_break_start=log.scheduled_break_start,
        scheduled_break_end=log.scheduled_break_end,
        work_started_at=log.work_started_at,
        work_ended_at=log.work_ended_at,
        breaks=log.breaks,
        overtime_minutes=log.overtime_minutes,
        paid_amount=log.paid_amount,
        promised_amount=log.promised_amount,
        piece_count=log.piece_count,
        piece_rate=log.piece_rate,
        deductions=log.deductions,
        note=log.note,
        workplace_name=employer.employer_name if employer else None,
        workplace_district=employer.work_district if employer else None,
        approval_status=log.approval_status,
        submission_version=log.submission_version,
        content_hash=log.content_hash,
        employee_signature=log.employee_signature,
        employee_signed_at=log.employee_signed_at,
        employer_signature=log.employer_signature,
        employer_signed_at=log.employer_signed_at,
        employer_decision_at=log.employer_decision_at,
        rejection_reason=log.rejection_reason,
    )


async def _require_link(db: AsyncSession, employer_user_id: UUID, employee_id: UUID) -> EmployerLink:
    link = (
        await db.execute(
            select(EmployerLink).where(
                EmployerLink.employer_user_id == employer_user_id,
                EmployerLink.employee_user_id == employee_id,
            )
        )
    ).scalar_one_or_none()
    if link is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Employee not linked")
    return link


async def _owned_employee_log(db: AsyncSession, log_id: UUID, employee_id: UUID) -> WorkLog:
    log = await db.get(WorkLog, log_id)
    if log is None or log.user_id != employee_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Work log not found")
    return log


async def _count_logs(db: AsyncSession, user_id: UUID) -> int:
    count = await db.execute(
        select(func.count(WorkLog.id)).where(WorkLog.user_id == user_id)
    )
    return int(count.scalar_one() or 0)
