"""Work logs and weekly per-employer settings."""

from datetime import date, datetime, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crypto
from ..db import get_db
from ..deps import current_user
from ..models import Employer, User, WeeklySetting, WorkLog, WorkLogSignatureEvent
from ..schemas.worklog import (
    WeeklySettingIn,
    WeeklySettingOut,
    WorkLogCreate,
    WorkLogOut,
    WorkLogSummary,
    WorkLogUpdate,
    WorkLogVerifyOut,
)
from ..services import signing
from ..services.calculations import compute_overtime_minutes
from ..services.summary import build_summary, week_start

router = APIRouter(prefix="/api", tags=["worklogs"])

# Statuses that lock a record against further editing until the employer
# decides. A signed-but-pending record must not be silently overwritten.
_LOCKED_STATUSES = ("pending_employer", "approved")


@router.get("/weekly-settings", response_model=list[WeeklySettingOut])
async def list_weekly_settings(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WeeklySetting]:
    result = await db.execute(
        select(WeeklySetting)
        .join(Employer, Employer.id == WeeklySetting.employer_id)
        .where(Employer.user_id == user.id)
    )
    return list(result.scalars().all())


@router.put("/employers/{employer_id}/weekly-settings", response_model=WeeklySettingOut)
async def upsert_weekly_settings(
    employer_id: UUID,
    payload: WeeklySettingIn,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> WeeklySetting:
    await _owned_employer(db, employer_id, user.id)
    setting = (
        await db.execute(select(WeeklySetting).where(WeeklySetting.employer_id == employer_id))
    ).scalar_one_or_none()
    if setting is None:
        setting = WeeklySetting(employer_id=employer_id)
        db.add(setting)
    data = payload.model_dump(exclude_none=True)
    data.setdefault("week_start", week_start(date.today()))
    for field, value in data.items():
        setattr(setting, field, value)
    await db.commit()
    await db.refresh(setting)
    return setting


@router.get("/worklogs", response_model=list[WorkLogOut])
async def list_worklogs(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WorkLog]:
    result = await db.execute(
        select(WorkLog)
        .join(Employer, Employer.id == WorkLog.employer_id)
        .where(Employer.user_id == user.id)
        .order_by(WorkLog.log_date.desc())
    )
    return list(result.scalars().all())


@router.get("/worklogs/summary", response_model=WorkLogSummary)
async def worklog_summary(
    period: Literal["daily", "weekly", "monthly"] = Query("daily"),
    tz_offset: int = Query(0, ge=-14 * 60, le=14 * 60),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkLogSummary:
    """Dashboard series aggregated server-side from the user's logs.

    `tz_offset` is the client's UTC offset in minutes so the window ("today",
    "this week", "this month") matches the caller's timezone.
    """
    return await build_summary(db, user, period, tz_offset)


@router.post("/worklogs", response_model=WorkLogOut, status_code=status.HTTP_201_CREATED)
async def create_worklog(
    payload: WorkLogCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkLog:
    await _owned_employer(db, payload.employer_id, user.id)
    # One log per employer per day: reuse the existing log for that date so
    # re-saving today's entry updates it instead of creating a duplicate.
    log = (
        await db.execute(
            select(WorkLog).where(
                WorkLog.user_id == user.id,
                WorkLog.employer_id == payload.employer_id,
                WorkLog.log_date == payload.log_date,
            )
        )
    ).scalar_one_or_none()
    if log is None:
        log = WorkLog(user_id=user.id, employer_id=payload.employer_id)
        db.add(log)
    else:
        _require_editable(log)
    _apply(log, payload)
    await db.commit()
    await db.refresh(log)
    return log


@router.get("/worklogs/{worklog_id}", response_model=WorkLogOut)
async def get_worklog(
    worklog_id: UUID,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkLog:
    return await _owned_log(db, worklog_id, user.id)


@router.patch("/worklogs/{worklog_id}", response_model=WorkLogOut)
async def update_worklog(
    worklog_id: UUID,
    payload: WorkLogUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkLog:
    log = await _owned_log(db, worklog_id, user.id)
    _require_editable(log)
    data = payload.model_dump(exclude_none=True)
    if data.get("employer_id") is not None:
        await _owned_employer(db, data["employer_id"], user.id)
    _apply(log, payload)
    await db.commit()
    await db.refresh(log)
    return log


@router.delete("/worklogs/{worklog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_worklog(
    worklog_id: UUID,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    log = await _owned_log(db, worklog_id, user.id)
    if log.approval_status == "approved":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="This record is approved and signed by both parties; it cannot be deleted",
        )
    await db.delete(log)
    await db.commit()


@router.post("/worklogs/{worklog_id}/sign", response_model=WorkLogOut)
async def sign_worklog(
    worklog_id: UUID,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkLog:
    """Employee signs the record and submits it for employer approval.

    Computes the canonical content hash, signs it with the employee's private
    key (RSA-2048 / SHA-256 — Electronic Transactions Act, 2063), stores the
    hash + signature, and moves the log to `pending_employer`. The record is
    then locked until the employer approves or rejects it.
    """
    log = await _owned_log(db, worklog_id, user.id)
    if log.approval_status not in ("draft", "rejected"):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="This record is already awaiting employer approval or approved",
        )

    await signing.ensure_signing_keys(db, user)
    content_hash = signing.log_content_hash(log)
    signature = crypto.sign(content_hash, user.signing_private_key_enc)

    log.content_hash = content_hash
    log.employee_signature = signature
    log.employee_signed_at = datetime.now(timezone.utc)
    log.submission_version = (log.submission_version or 0) + 1
    log.approval_status = "pending_employer"
    # A fresh submission supersedes any earlier decision.
    log.employer_signature = None
    log.employer_signed_at = None
    log.employer_decision_at = None
    log.rejection_reason = None

    db.add(
        WorkLogSignatureEvent(
            worklog_id=log.id,
            kind="employee_sign",
            actor_user_id=user.id,
            submission_version=log.submission_version,
            content_hash=content_hash,
            signature=signature,
            canonical_payload=signing.worklog_signing_dict(log),
        )
    )
    await db.commit()
    await db.refresh(log)
    return log


@router.get("/worklogs/{worklog_id}/verify", response_model=WorkLogVerifyOut)
async def verify_worklog(
    worklog_id: UUID,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkLogVerifyOut:
    """Re-hash the record and re-verify both stored signatures.

    The worker can run this any time to prove the record is intact; it is also
    what the employer's approval path performs before countersigning.
    """
    log = await _owned_log(db, worklog_id, user.id)
    employee = await db.get(User, log.user_id)

    # The employer account that approved/… is not the worker's Employer row —
    # it is whoever signed the current approval, found via the audit ledger.
    approver_event = (
        await db.execute(
            select(WorkLogSignatureEvent)
            .where(
                WorkLogSignatureEvent.worklog_id == log.id,
                WorkLogSignatureEvent.kind == "employer_approve",
            )
            .order_by(WorkLogSignatureEvent.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    employer_user = await db.get(User, approver_event.actor_user_id) if approver_event else None

    stored_hash = log.content_hash or ""
    recomputed = signing.log_content_hash(log)
    return WorkLogVerifyOut(
        worklog_id=log.id,
        approval_status=log.approval_status,
        stored_content_hash=stored_hash,
        recomputed_content_hash=recomputed,
        content_hash_matches=stored_hash == recomputed,
        employee_signature_valid=bool(
            log.employee_signature
            and stored_hash == recomputed
            and employee is not None
            and employee.signing_public_key_pem
            and crypto.verify(stored_hash, log.employee_signature, employee.signing_public_key_pem)
        ),
        employer_signature_valid=bool(
            log.employer_signature
            and stored_hash == recomputed
            and employer_user is not None
            and employer_user.signing_public_key_pem
            and crypto.verify(stored_hash, log.employer_signature, employer_user.signing_public_key_pem)
        ),
        employee_signed_at=log.employee_signed_at,
        employer_signed_at=log.employer_signed_at,
    )


def _require_editable(log: WorkLog) -> None:
    if log.approval_status in _LOCKED_STATUSES:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="This record is awaiting employer approval or already approved; "
            "it cannot be edited. If it was rejected, edit and resubmit.",
        )


def _apply(log: WorkLog, payload) -> None:
    data = payload.model_dump(exclude_none=True)
    for field, value in data.items():
        setattr(log, field, value)
    log.overtime_minutes = compute_overtime_minutes(
        log.scheduled_end_time, log.work_ended_at, log.log_date
    )
    # Background pay: for piece work the promised amount is pieces × rate, so
    # the worker never has to compute it themselves. Only used when no explicit
    # promised amount is supplied for this request.
    if (
        log.piece_count is not None
        and log.piece_rate is not None
        and data.get("promised_amount") is None
    ):
        log.promised_amount = round(log.piece_count * log.piece_rate, 2)


async def _owned_employer(db: AsyncSession, employer_id: UUID, user_id: UUID) -> Employer:
    employer = await db.get(Employer, employer_id)
    if employer is None or employer.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Employer not found")
    return employer


async def _owned_log(db: AsyncSession, worklog_id: UUID, user_id: UUID) -> WorkLog:
    log = await db.get(WorkLog, worklog_id)
    if log is None or log.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Work log not found")
    return log
