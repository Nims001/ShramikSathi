"""Link between an employer-portal account and a worker.

When a worker shares their unique code, an employer with the portal role can
enter it to create an `EmployerLink`. The link gives the employer read-only
visibility into that worker's work logs so both sides have one shared record
of hours and wages worked.
"""

import uuid
from typing import Optional

from sqlalchemy import String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class EmployerLink(TimestampMixin, Base):
    __tablename__ = "employer_links"
    __table_args__ = (
        UniqueConstraint(
            "employer_user_id", "employee_user_id", name="uq_employer_links_employer_employee"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    employer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )
    employee_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )
    note: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
