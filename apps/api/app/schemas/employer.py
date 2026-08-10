"""Pydantic schemas for the employer record (the "add employer" form)."""

from datetime import date, datetime, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EmployerBase(BaseModel):
    """All user-entered fields from the employer intake form.

    Background-calculated fields (hour totals, monthly salary) are computed
    server-side and returned in `EmployerOut`, not accepted from the client.
    """

    model_config = ConfigDict(extra="ignore")

    # Employment
    employer_name: str = Field(min_length=1, max_length=120)
    work_province: Optional[str] = Field(default=None, max_length=40)
    work_district: Optional[str] = Field(default=None, max_length=40)
    work_address: Optional[str] = Field(default=None, max_length=160)
    skill_level: Optional[str] = Field(default=None, max_length=20)
    industry: Optional[str] = Field(default=None, max_length=40)
    employment_type: str = Field(min_length=1, max_length=20)
    job_title: Optional[str] = Field(default=None, max_length=120)
    hiring_channel: Optional[str] = Field(default=None, max_length=20)
    contractor_name: Optional[str] = Field(default=None, max_length=120)
    tenure_years: Optional[float] = Field(default=None, ge=0)
    tenure_months: Optional[float] = Field(default=None, ge=0, le=12)
    on_probation: Optional[bool] = None
    probation_since: Optional[date] = None

    # Contracted work time
    contract_hours_per_day: Optional[float] = Field(default=None, ge=0, le=24)
    contract_break_start: Optional[time] = None
    contract_break_end: Optional[time] = None
    contract_break_unspecified: Optional[bool] = None
    contract_days_per_week: Optional[float] = Field(default=None, ge=0, le=7)
    contract_break_days: Optional[list] = None
    contract_break_days_unspecified: Optional[bool] = None
    contract_months_per_year: Optional[float] = Field(default=None, ge=0, le=12)
    contract_break_months: Optional[list] = None

    # Actual work time
    actual_hours_per_day: Optional[float] = Field(default=None, ge=0, le=24)
    actual_break_start: Optional[time] = None
    actual_break_end: Optional[time] = None
    actual_break_unspecified: Optional[bool] = None
    actual_days_per_week: Optional[float] = Field(default=None, ge=0, le=7)
    actual_break_days: Optional[list] = None
    actual_break_days_unspecified: Optional[bool] = None
    actual_months_per_year: Optional[float] = Field(default=None, ge=0, le=12)
    actual_break_months: Optional[list] = None

    # Overtime
    overtime_rule: Optional[bool] = None
    overtime_hours_per_unit: Optional[float] = Field(default=None, ge=0)
    overtime_unit: Optional[str] = Field(default=None, max_length=20)
    overtime_rate: Optional[str] = Field(default=None, max_length=10)
    overtime_rate_other: Optional[float] = Field(default=None, ge=0)
    overtime_consent: Optional[str] = Field(default=None, max_length=20)
    night_work: Optional[bool] = None
    night_allowance: Optional[bool] = None

    # Pay
    pay_unit: Optional[str] = Field(default=None, max_length=20)
    promised_wage: Optional[float] = Field(default=None, ge=0)
    payment_frequency: Optional[str] = Field(default=None, max_length=20)
    payment_method: Optional[str] = Field(default=None, max_length=20)
    received_annual_increment: Optional[bool] = None
    festival_expense_paid: Optional[bool] = None
    other_deduction_reason: Optional[str] = Field(default=None, max_length=200)

    # Leave
    weekly_leave_days_per_week: Optional[float] = Field(default=None, ge=0, le=7)
    weekly_off_day_guaranteed: Optional[bool] = None
    worked_off_day_paid_and_replaced: Optional[bool] = None
    public_holiday_paid_leave: Optional[bool] = None
    sick_leave_denied: Optional[bool] = None
    pregnant_or_maternity_last_year: Optional[bool] = None
    maternity_leave_denied: Optional[bool] = None
    paternity_leave_denied: Optional[bool] = None
    mourning_leave_denied: Optional[bool] = None

    # Contract
    has_written_contract: Optional[bool] = None
    contract_states_wage: Optional[bool] = None
    contract_states_hours: Optional[bool] = None
    contract_states_leave: Optional[bool] = None
    contract_states_termination: Optional[bool] = None
    contract_explained_in_own_language: Optional[bool] = None

    # Social security
    ssf_registered: Optional[bool] = None
    pf_deducted: Optional[bool] = None
    pf_deposited: Optional[bool] = None
    gratuity_deducted: Optional[bool] = None
    gratuity_paid_by_employer: Optional[bool] = None
    medical_insurance_provided: Optional[bool] = None
    accidental_insurance_provided: Optional[bool] = None

    # Recruitment & documents
    paid_fee_to_get_job: Optional[bool] = None
    wage_withheld_before_start: Optional[bool] = None
    employer_holds_documents: Optional[bool] = None

    # Safety & treatment
    free_to_leave_during_off_hours: Optional[bool] = None
    abuse_experienced: Optional[bool] = None

    # Termination
    terminated: Optional[bool] = None
    notice_given_days: Optional[float] = Field(default=None, ge=0, le=365)
    retrenchment_compensation_months: Optional[float] = Field(default=None, ge=0)
    final_settlement_within_15_days: Optional[bool] = None

    # Other clauses (free-text list the worker wants flagged in the AI analysis)
    other_clauses: Optional[list] = None


class EmployerCreate(EmployerBase):
    pass


class EmployerUpdate(EmployerBase):
    """Same shape as create; all fields optional so a partial edit is fine."""

    employer_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    employment_type: Optional[str] = Field(default=None, min_length=1, max_length=20)


class EmployerOut(EmployerBase):
    """Employer + server-computed background fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    contract_daily_hours: Optional[float] = None
    contract_weekly_hours: Optional[float] = None
    contract_monthly_hours: Optional[float] = None
    actual_daily_hours: Optional[float] = None
    actual_weekly_hours: Optional[float] = None
    actual_monthly_hours: Optional[float] = None
    monthly_salary_calculated: Optional[float] = None
