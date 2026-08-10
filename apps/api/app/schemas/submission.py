"""Pydantic schemas for the intake submission.

Mirrors the `submissions` table. Every numeric field is optional because
informal-sector workers may not know all figures — rules skip checks when the
data they need is missing.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .violation import ViolationOut


class EmploymentType(str, Enum):
    """§10 employment types — first thing the app asks."""

    REGULAR = "regular"
    WORK_BASED = "work_based"
    TIME_BASED = "time_based"
    CASUAL = "casual"
    PART_TIME = "part_time"


class SubmissionCreate(BaseModel):
    """Payload from the intake form (anonymized, no name/phone)."""

    model_config = ConfigDict(extra="forbid")

    employment_type: EmploymentType = Field(description="§10 employment type")

    sector: Optional[str] = Field(default=None, max_length=80)
    province: Optional[str] = Field(default=None, max_length=40)
    gender: Optional[str] = Field(default=None, max_length=20)

    # Working hours (§28-31)
    hours_per_day: Optional[float] = Field(default=None, ge=0, le=24)
    hours_per_week: Optional[float] = Field(default=None, ge=0, le=168)
    worked_over_5h_without_break: Optional[bool] = None
    overtime_hours_per_week: Optional[float] = Field(default=None, ge=0, le=168)
    overtime_rate_paid: Optional[float] = Field(default=None, ge=0, le=10)

    # Wages (§35-38, §106-107)
    daily_wage: Optional[float] = Field(default=None, ge=0)
    monthly_wage: Optional[float] = Field(default=None, ge=0)
    wage_payment_interval_days: Optional[float] = Field(default=None, ge=1, le=365)
    months_worked: Optional[float] = Field(default=None, ge=0)
    years_worked: Optional[float] = Field(default=None, ge=0)
    received_annual_increment: Optional[bool] = None
    festival_expense_paid: Optional[bool] = None
    other_deduction_reason: Optional[str] = Field(default=None, max_length=200)

    # Leave (§40-51)
    weekly_leave_taken_per_month: Optional[float] = Field(default=None, ge=0, le=31)
    sick_leave_denied: Optional[bool] = None
    maternity_leave_denied: Optional[bool] = None
    paternity_leave_denied: Optional[bool] = None
    mourning_leave_denied: Optional[bool] = None

    # Contract
    has_written_contract: Optional[bool] = None

    # Social security (§52-55)
    pf_deducted: Optional[bool] = None
    pf_deposited: Optional[bool] = None
    gratuity_deducted: Optional[bool] = None
    gratuity_paid_by_employer: Optional[bool] = None
    medical_insurance_provided: Optional[bool] = None
    accidental_insurance_provided: Optional[bool] = None

    # Termination (§144-148)
    termination_occurred: Optional[bool] = None
    notice_given_days: Optional[float] = Field(default=None, ge=0, le=365)
    retrenchment_compensation_months_paid: Optional[float] = Field(default=None, ge=0)
    final_settlement_within_15_days: Optional[bool] = None


class SubmissionResult(BaseModel):
    """POST /api/submissions response — the submission plus detected violations."""

    submission_id: UUID
    created_at: datetime
    violations: list[ViolationOut]
