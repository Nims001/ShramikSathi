"""GET /api/dashboard/stats — anonymized aggregate counts for the public page."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import Submission, Violation

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class CountItem(BaseModel):
    key: str
    count: int


class DashboardStats(BaseModel):
    total_submissions: int
    total_violations: int
    by_rule: list[CountItem]
    by_sector: list[CountItem]
    by_province: list[CountItem]
    by_severity: list[CountItem]


async def _count_grouped(db: AsyncSession, column) -> list[CountItem]:
    """Run one GROUP BY count over a nullable text column, skipping NULLs."""
    rows = await db.execute(
        select(column, func.count()).group_by(column).where(column.is_not(None))
    )
    out = []
    for k, c in rows.all():
        # SQLAlchemy re-coerces enum columns back into Python enum members on
        # read-back, so unwrap .value to get the stored string (e.g. "info").
        key = str(k.value) if hasattr(k, "value") else str(k)
        out.append(CountItem(key=key, count=c))
    return out


@router.get("/stats", response_model=DashboardStats)
async def stats(db: AsyncSession = Depends(get_db)) -> DashboardStats:
    """Aggregate counts used by the public dashboard charts."""
    total_submissions = (await db.execute(select(func.count()).select_from(Submission))).scalar_one()
    total_violations = (await db.execute(select(func.count()).select_from(Violation))).scalar_one()

    by_rule = await _count_grouped(db, Violation.rule_id)
    by_sector = await _count_grouped(db, Submission.sector)
    by_province = await _count_grouped(db, Submission.province)
    by_severity = await _count_grouped(db, Violation.severity)

    return DashboardStats(
        total_submissions=total_submissions,
        total_violations=total_violations,
        by_rule=by_rule,
        by_sector=by_sector,
        by_province=by_province,
        by_severity=by_severity,
    )
