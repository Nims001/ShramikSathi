"""ORM model for one daily work log and its weekly presets.

`WorkLog` stores a single day's reported/recorded timings for an employer.
Breaks are kept as a JSON array of `{start, end}` ISO timestamps so the
worker can add/backdate a forgotten break later. `overtime_minutes` is
background-calculated from work_ended_at beyond the scheduled end time.

`WeeklySetting` is the per-employer "this week" preset: which days are the
specified break days, the promised payment day (for non-daily pay), and the
per-day promised wage (for daily-pay employment).
"""

import uuid
from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, Time, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class WeeklySetting(TimestampMixin, Base):
    __tablename__ = "weekly_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    employer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employers.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    week_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # Monday of the week these presets apply to
    break_days_this_week: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)  # weekday ints 0-6
    promised_payment_day: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    daily_promised_wage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class WorkLog(TimestampMixin, Base):
    __tablename__ = "work_logs"
    __table_args__ = (
        # One log per employer per day.
        UniqueConstraint("employer_id", "log_date", name="uq_work_logs_employer_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Employer-specified schedule for the day (all optional).
    report_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    scheduled_end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    scheduled_break_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    scheduled_break_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    # Actual recorded timestamps from the Start / Break / End buttons.
    work_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    work_ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    breaks: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)  # [{start, end}]

    # Background-calculated.
    overtime_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    # Pay for the day (daily-pay nature).
    paid_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    promised_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # Per-piece (work-based) pay: promised_amount = piece_count × piece_rate,
    # computed in the background when both are given.
    piece_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    piece_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deductions: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Dual-consensus signing (Electronic Transactions Act, 2063) ──────────
    # The employee signs a canonical hash of the record (`content_hash`); the
    # log then enters `pending_employer`. The linked employer verifies the
    # worker's signature and countersigns the same hash (`approved`) or rejects
    # with a short message. Editing is locked while pending/approved.
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    approval_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft"
    )  # draft | pending_employer | approved | rejected
    submission_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    employee_signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    employee_signed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    employer_signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    employer_signed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    employer_decision_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class WorkLogSignatureEvent(TimestampMixin, Base):
    """Append-only audit ledger of every signing/rejection on a work log.

    Each row carries the canonical record as signed, its hash, and the base64
    signature — so the full history can be re-verified even after resubmission.
    """

    __tablename__ = "worklog_signatures"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    worklog_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_logs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # employee_sign | employer_approve | employer_reject
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    submission_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    canonical_payload: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
