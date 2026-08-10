"""Pydantic models for the "Analyse with AI" request.

This mirrors the JSON document produced by `GET /api/analysis` (and the
reference pipeline's `AnalyseRequest`). Every field is optional/defaulted so
parsing the current app's documents never fails on a missing value — retrieval
simply skips checks the data can't support.
"""

from datetime import date, datetime, time
from typing import List, Optional
from pydantic import BaseModel


class Meta(BaseModel):
    generated_at: Optional[datetime] = None
    law_framework: Optional[str] = None
    analysis_mode: Optional[str] = None


class User(BaseModel):
    id: str = ""
    age: Optional[int] = None
    gender: Optional[str] = None
    ethnicity: Optional[str] = None
    education_level: Optional[str] = None
    language: Optional[str] = None


class Employer(BaseModel):
    id: str = ""
    employer_name: Optional[str] = None
    work_province: Optional[str] = None
    work_district: Optional[str] = None
    work_address: Optional[str] = None
    skill_level: Optional[str] = None
    industry: Optional[str] = None
    employment_type: Optional[str] = None
    job_title: Optional[str] = None
    hiring_channel: Optional[str] = None
    contractor_name: Optional[str] = None

    tenure_years: Optional[int] = None
    tenure_months: Optional[int] = None
    on_probation: Optional[bool] = None
    probation_since: Optional[date] = None

    # Contract terms
    contract_hours_per_day: Optional[float] = None
    contract_break_start: Optional[time] = None
    contract_break_end: Optional[time] = None
    contract_break_unspecified: Optional[bool] = None
    contract_days_per_week: Optional[int] = None
    contract_break_days: Optional[List[str]] = None
    contract_break_days_unspecified: Optional[bool] = None
    contract_months_per_year: Optional[int] = None
    contract_break_months: Optional[List[str]] = None
    contract_daily_hours: Optional[float] = None
    contract_weekly_hours: Optional[float] = None
    contract_monthly_hours: Optional[float] = None

    # Actual worked conditions
    actual_hours_per_day: Optional[float] = None
    actual_break_start: Optional[time] = None
    actual_break_end: Optional[time] = None
    actual_break_unspecified: Optional[bool] = None
    actual_days_per_week: Optional[int] = None
    actual_break_days: Optional[List[str]] = None
    actual_break_days_unspecified: Optional[bool] = None
    actual_months_per_year: Optional[int] = None
    actual_break_months: Optional[List[str]] = None
    actual_daily_hours: Optional[float] = None
    actual_weekly_hours: Optional[float] = None
    actual_monthly_hours: Optional[float] = None

    # Overtime
    overtime_rule: Optional[bool] = None
    overtime_hours_per_unit: Optional[float] = None
    overtime_unit: Optional[str] = None
    overtime_rate: Optional[str] = None
    overtime_rate_other: Optional[str] = None
    overtime_consent: Optional[str] = None

    night_work: Optional[bool] = None
    night_allowance: Optional[bool] = None

    # Pay
    pay_unit: Optional[str] = None
    promised_wage: Optional[float] = None
    monthly_salary_calculated: Optional[float] = None
    monthly_wage_received: Optional[float] = None
    payment_frequency: Optional[str] = None
    payment_method: Optional[str] = None
    wage_payment_days_after_month_end: Optional[int] = None
    received_annual_increment: Optional[bool] = None
    festival_expense_paid: Optional[bool] = None
    other_deduction_reason: Optional[str] = None

    # Leave
    weekly_leave_days_per_month: Optional[int] = None
    weekly_off_day_guaranteed: Optional[bool] = None
    worked_off_day_paid_and_replaced: Optional[bool] = None
    public_holiday_paid_leave: Optional[bool] = None
    sick_leave_denied: Optional[bool] = None
    pregnant_or_maternity_last_year: Optional[bool] = None
    maternity_leave_denied: Optional[bool] = None
    paternity_leave_denied: Optional[bool] = None
    mourning_leave_denied: Optional[bool] = None

    # Contract & documentation
    has_written_contract: Optional[bool] = None
    contract_states_wage: Optional[bool] = None
    contract_states_hours: Optional[bool] = None
    contract_states_leave: Optional[bool] = None
    contract_states_termination: Optional[bool] = None
    contract_explained_in_own_language: Optional[bool] = None

    # Social security / insurance
    ssf_registered: Optional[bool] = None
    pf_deducted: Optional[bool] = None
    pf_deposited: Optional[bool] = None
    gratuity_deducted: Optional[bool] = None
    gratuity_paid_by_employer: Optional[bool] = None
    medical_insurance_provided: Optional[bool] = None
    accidental_insurance_provided: Optional[bool] = None

    # Recruitment / documents / freedom
    paid_fee_to_get_job: Optional[bool] = None
    wage_withheld_before_start: Optional[bool] = None
    employer_holds_documents: Optional[bool] = None
    free_to_leave_during_off_hours: Optional[bool] = None
    abuse_experienced: Optional[bool] = None

    # Termination
    terminated: Optional[bool] = None
    notice_given_days: Optional[int] = None
    retrenchment_compensation_months: Optional[float] = None
    final_settlement_within_15_days: Optional[bool] = None

    # Free-text clauses the user typed manually — the whole point of the
    # RAG step, since these can't be checked by a deterministic rule.
    other_clauses: Optional[List[str]] = None


class WeeklySetting(BaseModel):
    id: str = ""
    employer_id: str = ""
    week_start: Optional[date] = None
    break_days_this_week: Optional[List[str]] = None
    promised_payment_day: Optional[date] = None
    daily_promised_wage: Optional[float] = None
    created_at: Optional[datetime] = None


class WorkLog(BaseModel):
    id: str = ""
    user_id: str = ""
    employer_id: str = ""
    log_date: Optional[date] = None
    report_time: Optional[time] = None
    scheduled_end_time: Optional[time] = None
    scheduled_break_start: Optional[time] = None
    scheduled_break_end: Optional[time] = None
    work_started_at: Optional[datetime] = None
    work_ended_at: Optional[datetime] = None
    breaks: Optional[List[dict]] = None
    overtime_minutes: Optional[int] = None
    paid_amount: Optional[float] = None
    promised_amount: Optional[float] = None
    deductions: Optional[list] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None


class DeterministicFinding(BaseModel):
    rule_id: str = ""
    section_reference: str = ""
    severity: str = "info"
    plain_explanation_en: str = ""
    plain_explanation_ne: Optional[str] = None
    suggested_action_en: Optional[str] = None
    suggested_action_ne: Optional[str] = None


class EmployerBlock(BaseModel):
    employer: Employer
    weekly_setting: Optional[WeeklySetting] = None
    logs: Optional[List[WorkLog]] = None
    deterministic_findings: Optional[List[DeterministicFinding]] = None


class StatsPeriod(BaseModel):
    days_worked: Optional[int] = None
    overtime_minutes: Optional[int] = None
    overtime_hours_rounded: Optional[float] = None
    paid_amount: Optional[float] = None
    promised_amount: Optional[float] = None
    amount_due: Optional[float] = None


class Stats(BaseModel):
    today: Optional[StatsPeriod] = None
    last_7_days: Optional[StatsPeriod] = None
    last_30_days: Optional[StatsPeriod] = None
    last_90_days: Optional[StatsPeriod] = None
    employer_count: Optional[int] = None


class AnalyseRequest(BaseModel):
    meta: Optional[Meta] = None
    user: Optional[User] = None
    employers: List[EmployerBlock]
    stats: Optional[Stats] = None
