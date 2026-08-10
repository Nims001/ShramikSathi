"""FastAPI dependencies for authenticated routes.

A bearer token from the `Authorization: Bearer <token>` header resolves the
current user; expired or unknown tokens are rejected with 401.
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_db
from .models import Session, User
from .security import generate_token


async def current_user(
    authorization: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    result = await db.execute(
        select(Session).where(Session.token == token, Session.expires_at.is_not(None))
    )
    session = result.scalar_one_or_none()
    if session is None or session.is_expired():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")

    user = await db.get(User, session.user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def create_session(user_id) -> tuple[str, object]:
    """Return (token, Session) — caller persists it. Session needs a db.add."""
    token = generate_token()
    session = Session(user_id=user_id, token=token, expires_at=Session.default_expiry())
    return token, session
