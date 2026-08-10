"""Pydantic schemas for the employer portal (share codes + employee logs)."""

from datetime import date, datetime, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ShareCodeResponse(BaseModel):
    code: str


class LinkRequest(BaseModel):
    code: str
    note: Optional[str] = None


class LinkedEmployee(BaseModel):
    employee_id: UUID
    username: str
    note: Optional[str] = None
    linked_at: datetime
    log_count: int = 0


class EmployeeLog(BaseModel):
    """One work log as seen by the linked employer — workplace context added."""

    model_config = ConfigDict(from_attributes=True)

    log_id: UUID
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
    workplace_name: Optional[str] = None
    workplace_district: Optional[str] = None

    # Dual-consensus signing state.
    approval_status: str = "draft"
    submission_version: int = 0
    content_hash: Optional[str] = None
    employee_signature: Optional[str] = None
    employee_signed_at: Optional[datetime] = None
    employer_signature: Optional[str] = None
    employer_signed_at: Optional[datetime] = None
    employer_decision_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


class PendingLog(EmployeeLog):
    """A signed record awaiting this employer's approval, with worker context."""

    employee_id: UUID
    username: str


class RejectRequest(BaseModel):
    """Short message the worker sees when their log is not approved."""

    reason: str = Field(min_length=3, max_length=500)
