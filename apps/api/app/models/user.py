"""User account model — the logged-in identity behind employers and work logs.

Unlike the old anonymized `submissions` table, a user is created through the
onboarding signup form. Identity & demographics (gender, date of birth, age,
ethnicity, education) are stored once here because they are the same across
all of a worker's employers.
"""

import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # worker | employer. Employers run the portal account that links to
    # workers by their share code.
    role: Mapped[str] = mapped_column(String(10), nullable=False, server_default="worker")

    # SHA-256 of the worker's share code (never stored in plaintext). When set,
    # an employer can link to this worker by typing the code.
    share_code_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Digital-signature keys (Electronic Transactions Act, 2063 — asymmetric
    # cryptosystem). Public PEM is safe to expose; the private half is stored
    # AES-256-GCM encrypted with the server SIGNING_SECRET (see crypto.py).
    signing_public_key_pem: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    signing_private_key_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    signing_key_fingerprint: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Identity & demographics (same across all employers).
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # Background-calculated from date_of_birth; never asked directly.
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ethnicity: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    education_level: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)

    language: Mapped[str] = mapped_column(String(5), nullable=False, server_default="en")
