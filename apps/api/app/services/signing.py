"""Signing service: canonical log serialisation + per-user signing keys.

The signed record is a canonical dictionary built from the `WorkLog` columns
that constitute the day's facts (times, breaks, overtime, pay, deductions,
note). `worklog_signing_dict` normalises every value so the resulting hash is
stable and reproducible, which is what makes the stored signatures meaningful:
editing any one of those columns after signing invalidates the hash.

Each user (worker or employer) gets a lazily-created RSA-2048 key pair whose
private half is encrypted at rest (see `crypto.py`). Signing always happens
server-side on behalf of the authenticated user.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from .. import crypto
from ..models import User, WorkLog


def worklog_signing_dict(log: WorkLog) -> dict:
    """The canonical, deterministic record the signatures bind to."""
    return {
        "log_id": str(log.id),
        "employer_id": str(log.employer_id),
        "log_date": log.log_date.isoformat(),
        "report_time": log.report_time.isoformat() if log.report_time else None,
        "scheduled_end_time": log.scheduled_end_time.isoformat() if log.scheduled_end_time else None,
        "scheduled_break_start": log.scheduled_break_start.isoformat() if log.scheduled_break_start else None,
        "scheduled_break_end": log.scheduled_break_end.isoformat() if log.scheduled_break_end else None,
        "work_started_at": log.work_started_at.isoformat() if log.work_started_at else None,
        "work_ended_at": log.work_ended_at.isoformat() if log.work_ended_at else None,
        "breaks": [
            {"start": b.get("start"), "end": b.get("end")} for b in (log.breaks or [])
        ],
        "overtime_minutes": log.overtime_minutes or 0,
        "paid_amount": _round(log.paid_amount),
        "promised_amount": _round(log.promised_amount),
        "piece_count": log.piece_count,
        "piece_rate": _round(log.piece_rate),
        "deductions": [
            {"label": d.get("label"), "amount": _round(d.get("amount"))}
            for d in (log.deductions or [])
        ],
        "note": log.note,
    }


def log_content_hash(log: WorkLog) -> str:
    """SHA-256 hash of the canonical record; what the signatures sign."""
    return crypto.content_hash(worklog_signing_dict(log))


def verify_log_signature(log: WorkLog, user: User) -> bool:
    """Check the current employee signature against the stored content hash.

    Recomputing the hash and re-verifying on every approval means a tampered
    record can never be countersigned by the employer.
    """
    if not log.employee_signature or not user.signing_public_key_pem:
        return False
    if log.content_hash != log_content_hash(log):
        return False
    return crypto.verify(log.content_hash, log.employee_signature, user.signing_public_key_pem)


async def ensure_signing_keys(db: AsyncSession, user: User) -> None:
    """Create the user's RSA-2048 key pair on first use, then flush."""
    if user.signing_public_key_pem and user.signing_private_key_enc:
        return
    public_pem, private_enc, fp = crypto.generate_keypair()
    user.signing_public_key_pem = public_pem
    user.signing_private_key_enc = private_enc
    user.signing_key_fingerprint = fp
    await db.flush()


def _round(value) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)
