"""ORM model for one detected violation tied to a submission.

`severity` is one of info / warning / critical. Explanations and suggested
actions are stored in both English and Nepali so the UI can toggle languages
without re-hitting the API.
"""

import uuid
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Severity(str, PyEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Violation(TimestampMixin, Base):
    __tablename__ = "violations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # FK back to the anonymized submission that produced this violation.
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False
    )
    # rule_id matches the rule engine function's id, e.g. "hours.max_daily".
    rule_id: Mapped[str] = mapped_column(String(80), nullable=False)
    # Act citation shown to the user, e.g. "§28(1)".
    section_reference: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(
        Enum(Severity, name="severity", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    plain_explanation_en: Mapped[str] = mapped_column(Text, nullable=False)
    plain_explanation_ne: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_action_en: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_action_ne: Mapped[str] = mapped_column(Text, nullable=False)

    submission = relationship("Submission", back_populates="violations")
