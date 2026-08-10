"""ORM model for one employer record attached to a user.

This replaces the old anonymized `submissions` flow for logged-in workers:
every field from the "add employer" intake form lands here. Numeric/derived
columns computed in the background (contracted/actual hour totals, monthly
salary) are stored alongside user-entered values so the AI-analysis endpoint
can consume one self-contained JSON document.
"""

import uuid
from datetime import date, time
from typing import Optional

from sqlalchemy import Boolean, Date, Float, String, Text, Time, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class Employer(TimestampMixin, Base):
    __tablename__ = "employers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )

    # ---- Employment -------------------------------------------------
    employer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    work_province: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    work_district: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    work_address: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    skill_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # skilled | semi_skilled | unskilled
    industry: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    employment_type: Mapped[str] = mapped_column(String(20), nullable=False)  # §10 types
    job_title: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    hiring_channel: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # direct | labor_contractor | manpower_agency
    contractor_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    tenure_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # बर्ष
    tenure_months: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # महिना
    on_probation: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    probation_since: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # ---- Contracted work time ----------------------------------------
    contract_hours_per_day: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    contract_break_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    contract_break_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    contract_break_unspecified: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    contract_days_per_week: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    contract_break_days: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    contract_break_days_unspecified: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    contract_months_per_year: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    contract_break_months: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    # background-calculated
    contract_daily_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    contract_weekly_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    contract_monthly_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ---- Actual work time ---------------------------------------------
    actual_hours_per_day: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_break_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    actual_break_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    actual_break_unspecified: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    actual_days_per_week: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_break_days: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    actual_break_days_unspecified: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    actual_months_per_year: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_break_months: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    # background-calculated
    actual_daily_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_weekly_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_monthly_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ---- Overtime ------------------------------------------------------
    overtime_rule: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    overtime_hours_per_unit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overtime_unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # day | week | month | dont_know
    overtime_rate: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # 100 | 150 | other
    overtime_rate_other: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overtime_consent: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # forced | voluntary | dont_know
    night_work: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    night_allowance: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # ---- Pay -------------------------------------------------------------
    pay_unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # hourly | daily | weekly | monthly | per_piece
    promised_wage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # amount per pay_unit
    payment_frequency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # daily | weekly | monthly
    payment_method: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # cash | cheque | bank_transfer | unknown
    # background-calculated
    monthly_salary_calculated: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    received_annual_increment: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    festival_expense_paid: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    other_deduction_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # ---- Leave -----------------------------------------------------------
    weekly_leave_days_per_week: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weekly_off_day_guaranteed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    worked_off_day_paid_and_replaced: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    public_holiday_paid_leave: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    sick_leave_denied: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    pregnant_or_maternity_last_year: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    maternity_leave_denied: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    paternity_leave_denied: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    mourning_leave_denied: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # ---- Contract ----------------------------------------------------------
    has_written_contract: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    contract_states_wage: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    contract_states_hours: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    contract_states_leave: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    contract_states_termination: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    contract_explained_in_own_language: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # ---- Social security -----------------------------------------------------
    ssf_registered: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    pf_deducted: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    pf_deposited: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    gratuity_deducted: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    gratuity_paid_by_employer: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    medical_insurance_provided: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    accidental_insurance_provided: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # ---- Recruitment & documents ------------------------------------------------
    paid_fee_to_get_job: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    wage_withheld_before_start: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    employer_holds_documents: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # ---- Safety & treatment ------------------------------------------------------
    free_to_leave_during_off_hours: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    abuse_experienced: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # ---- Termination ------------------------------------------------------------
    terminated: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    notice_given_days: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    retrenchment_compensation_months: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_settlement_within_15_days: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # ---- Other clauses -----------------------------------------------------------
    other_clauses: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
