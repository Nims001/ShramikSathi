"""ORM model for one intake form submission.

Deliberately anonymized: no name, phone, or national ID is stored, so the
table cannot be traced back to an individual. The five employment types are
the ones defined by §10 of the Act.
"""

import uuid
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Boolean, Enum, Float, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class EmploymentType(str, PyEnum):
    """§10 employment-type enum as a plain Python enum."""

    REGULAR = "regular"
    WORK_BASED = "work_based"
    TIME_BASED = "time_based"
    CASUAL = "casual"
    PART_TIME = "part_time"


class Submission(TimestampMixin, Base):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )

    employment_type: Mapped[str] = mapped_column(
        Enum(EmploymentType, name="employment_type", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    sector: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    province: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Working hours (§28-31)
    hours_per_day: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hours_per_week: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    worked_over_5h_without_break: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    overtime_hours_per_week: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overtime_rate_paid: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Wages (§35-38, §106-107)
    daily_wage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    monthly_wage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wage_payment_interval_days: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    months_worked: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    years_worked: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    received_annual_increment: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    festival_expense_paid: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    other_deduction_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Leave (§40-51)
    weekly_leave_taken_per_month: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sick_leave_denied: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    maternity_leave_denied: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    paternity_leave_denied: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    mourning_leave_denied: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Contract
    has_written_contract: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Social security (§52-55)
    pf_deducted: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    pf_deposited: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    gratuity_deducted: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    gratuity_paid_by_employer: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    medical_insurance_provided: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    accidental_insurance_provided: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Termination (§144-148)
    termination_occurred: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    notice_given_days: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    retrenchment_compensation_months_paid: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_settlement_within_15_days: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    violations = relationship("Violation", back_populates="submission", cascade="all, delete-orphan")
