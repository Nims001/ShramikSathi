"""Session model — opaque bearer token for "logged in" requests.

MVP auth: username/password → random token stored here with an expiry. This is
deliberately simple; the Nagarik app SSO button is a placeholder stub.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin

SESSION_TTL_DAYS = 30


class Session(TimestampMixin, Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    @staticmethod
    def default_expiry() -> datetime:
        return datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)

    @staticmethod
    def active_filter():
        from sqlalchemy import func  # noqa: PLC0415

        return Session.expires_at > func.now()

    def is_expired(self) -> bool:
        return self.expires_at < datetime.now(timezone.utc)
