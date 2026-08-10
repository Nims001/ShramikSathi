"""Pydantic schemas for work logs and weekly settings."""

from datetime import date, datetime, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WeeklySettingIn(BaseModel):
    """Per-employer "this week" presets."""

    model_config = ConfigDict(extra="ignore")

    week_start: Optional[date] = None  # Monday of the week these presets apply to
    break_days_this_week: Optional[list] = None
    promised_payment_day: Optional[date] = None
    daily_promised_wage: Optional[float] = Field(default=None, ge=0)


class WeeklySettingOut(WeeklySettingIn):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employer_id: UUID
    created_at: datetime


class WorkLogCreate(BaseModel):
    """One day's log. All timings are optional; at least one should be set.

    `breaks` is a JSON array of `{"start": iso, "end": iso}`.
    """

    model_config = ConfigDict(extra="ignore")

    employer_id: UUID
    log_date: date
    report_time: Optional[time] = None
    scheduled_end_time: Optional[time] = None
    scheduled_break_start: Optional[time] = None
    scheduled_break_end: Optional[time] = None
    work_started_at: Optional[datetime] = None
    work_ended_at: Optional[datetime] = None
    breaks: Optional[list] = None
    paid_amount: Optional[float] = Field(default=None, ge=0)
    promised_amount: Optional[float] = Field(default=None, ge=0)
    piece_count: Optional[int] = Field(default=None, ge=0)
    piece_rate: Optional[float] = Field(default=None, ge=0)
    deductions: Optional[list] = None
    note: Optional[str] = None

    @model_validator(mode="after")
    def _at_least_one_value(self) -> "WorkLogCreate":
        timing = any(
            v is not None
            for v in (
                self.report_time,
                self.scheduled_end_time,
                self.scheduled_break_start,
                self.scheduled_break_end,
                self.work_started_at,
                self.work_ended_at,
                self.breaks,
            )
        )
        pay = any(
            v is not None
            for v in (
                self.paid_amount,
                self.promised_amount,
                self.piece_count,
                self.piece_rate,
                self.deductions,
            )
        )
        if not timing and not pay:
            raise ValueError("At least one time or pay field must be set")
        for b in self.breaks or []:
            if not isinstance(b, dict) or not b.get("start"):
                raise ValueError("Each break must have a start timestamp")
        return self


class WorkLogUpdate(WorkLogCreate):
    """Same shape as create; all fields optional for partial updates."""

    employer_id: Optional[UUID] = None
    log_date: Optional[date] = None

    @model_validator(mode="after")
    def _allow_partial(self) -> "WorkLogUpdate":
        # Partial updates may change a single field, so skip the
        # "at least one field" check that applies on create.
        return self


class SummaryRow(BaseModel):
    key: str
    label: str
    hours: float
    overtime: float
    promised: float
    paid: float
    days: int


class SummaryEmployerSlice(BaseModel):
    name: str
    value: float


class WorkLogSummary(BaseModel):
    period: str
    rows: list[SummaryRow]
    by_employer: list[SummaryEmployerSlice]
    total_logs: int


class WorkLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    employer_id: UUID
    log_date: date
    report_time: Optional[time] = None
    scheduled_end_time: Optional[time] = None
    scheduled_break_start: Optional[time] = None
    scheduled_break_end: Optional[time] = None
    work_started_at: Optional[datetime] = None
    work_ended_at: Optional[datetime] = None
    breaks: Optional[list] = None
    overtime_minutes: int = 0
    paid_amount: Optional[float] = None
    promised_amount: Optional[float] = None
    piece_count: Optional[int] = None
    piece_rate: Optional[float] = None
    deductions: Optional[list] = None
    note: Optional[str] = None
    created_at: datetime

    # Dual-consensus signing state.
    content_hash: Optional[str] = None
    approval_status: str = "draft"
    submission_version: int = 0
    employee_signature: Optional[str] = None
    employee_signed_at: Optional[datetime] = None
    employer_signature: Optional[str] = None
    employer_signed_at: Optional[datetime] = None
    employer_decision_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


class WorkLogVerifyOut(BaseModel):
    """Result of re-hashing + re-verifying the stored signatures.

    `content_hash_matches` proves the record's columns are unchanged since
    signing; the two `*_signature_valid` flags prove each signature really was
    made by the corresponding party's public key.
    """

    worklog_id: UUID
    approval_status: str
    stored_content_hash: str
    recomputed_content_hash: str
    content_hash_matches: bool
    employee_signature_valid: bool = False
    employer_signature_valid: bool = False
    employee_signed_at: Optional[datetime] = None
    employer_signed_at: Optional[datetime] = None
