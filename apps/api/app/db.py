"""Async SQLAlchemy setup — engine, session factory, and FastAPI dependency.

The engine is created lazily so tests can override DATABASE_URL before the
first connection is made.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import settings

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields one DB session per request."""
    async with SessionLocal() as session:
        yield session
