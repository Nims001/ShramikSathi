"""Work-log summary series for the personal dashboard.

Aggregates a user's work logs into daily / weekly / monthly buckets plus a
per-employer hour split, so the dashboard fetches one small payload instead of
every log row. The pure helpers are unit-tested; `build_summary` is the thin
DB wrapper used by the router.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Employer, WorkLog

Period = Literal["daily", "weekly", "monthly"]

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
_WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def worked_hours(log: WorkLog) -> float:
    """Hours logged for one day: actual timestamps preferred, else the schedule."""
    if log.work_started_at is not None and log.work_ended_at is not None:
        delta = log.work_ended_at - log.work_started_at
        return max(0.0, delta.total_seconds() / 3600.0)
    if log.report_time is not None and log.scheduled_end_time is not None:
        start = log.report_time.hour * 60 + log.report_time.minute
        end = log.scheduled_end_time.hour * 60 + log.scheduled_end_time.minute
        minutes = end - start
        if minutes < 0:
            minutes += 24 * 60
        return minutes / 60.0
    return 0.0


def week_start(d: date) -> date:
    """Monday of the week containing `d` (week starts Monday, §28)."""
    return d - timedelta(days=d.weekday())


def bucket_key(log_date: date, period: str) -> str:
    """The series key a log belongs to for a given period."""
    if period == "weekly":
        return week_start(log_date).isoformat()
    if period == "monthly":
        return log_date.isoformat()[:7]
    return log_date.isoformat()


def label_for(key: str, period: str) -> str:
    """Short chart label for a series key.

    Daily shows the weekday + day ("Mon 3") over the past-7-day window; weekly
    shows the bucket's range ("Jun 22 - Jun 28"); monthly shows month + full
    year ("Jun 2026").
    """
    if period == "daily":
        d = date.fromisoformat(key)
        return f"{_WEEKDAYS[d.weekday()]} {d.day}"
    if period == "weekly":
        start = date.fromisoformat(key)
        end = start + timedelta(days=6)
        return f"{_MONTHS[start.month - 1]} {start.day} - {_MONTHS[end.month - 1]} {end.day}"
    if period == "monthly":
        year, month = key.split("-")
        return f"{_MONTHS[int(month) - 1]} {year}"
    d = date.fromisoformat(key)
    return f"{_MONTHS[d.month - 1]} {d.day}"


def _empty_row(key: str, period: str) -> dict[str, Any]:
    return {
        "key": key,
        "label": label_for(key, period),
        "hours": 0.0,
        "overtime": 0.0,
        "promised": 0.0,
        "paid": 0.0,
        "days": 0,
    }


def window_keys(today: date, period: str) -> list[str]:
    """The full series window: last 7 days, last 8 week-starts, or last 6 months."""
    if period == "daily":
        return [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    if period == "weekly":
        return [week_start(today - timedelta(days=i * 7)).isoformat() for i in range(7, -1, -1)]
    keys = []
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        keys.append(f"{y}-{m:02d}")
    return keys


def aggregate(logs: list[WorkLog], employers: list[Employer], period: str, today: date) -> dict[str, Any]:
    """Bucket logs into the window and return the dashboard payload."""
    name_of = {e.id: e.employer_name for e in employers}

    buckets: dict[str, dict[str, Any]] = {}
    by_employer: dict[str, dict[str, Any]] = {}
    for log in logs:
        key = bucket_key(log.log_date, period)
        row = buckets.get(key)
        if row is None:
            row = _empty_row(key, period)
            buckets[key] = row
        hours = worked_hours(log)
        row["hours"] += hours
        row["overtime"] += float(log.overtime_minutes or 0) / 60.0
        row["promised"] += float(log.promised_amount or 0)
        row["paid"] += float(log.paid_amount or 0)
        row["days"] += 1

        slice_ = by_employer.get(log.employer_id)
        if slice_ is None:
            slice_ = {"name": name_of.get(log.employer_id, "—"), "value": 0.0}
            by_employer[log.employer_id] = slice_
        slice_["value"] += hours

    rows = [dict(buckets.get(key) or _empty_row(key, period)) for key in window_keys(today, period)]
    for row in rows:
        row["hours"] = round(row["hours"], 2)
        row["overtime"] = round(row["overtime"], 2)
        row["promised"] = round(row["promised"], 2)
        row["paid"] = round(row["paid"], 2)

    by_employer_rows = [
        {"name": slice_["name"], "value": round(slice_["value"], 2)}
        for slice_ in sorted(by_employer.values(), key=lambda s: s["value"], reverse=True)
        if slice_["value"] > 0
    ]

    return {
        "period": period,
        "rows": rows,
        "by_employer": by_employer_rows,
        "total_logs": len(logs),
    }


async def build_summary(db: AsyncSession, user, period: str, tz_offset_minutes: int = 0) -> dict[str, Any]:
    """Load the user's logs + employers and aggregate them for `period`.

    `tz_offset_minutes` lets the caller's "today" (client timezone) drive the
    window instead of the server's clock.
    """
    logs = list(
        (
            await db.execute(
                select(WorkLog)
                .where(WorkLog.user_id == user.id)
                .order_by(WorkLog.log_date)
            )
        ).scalars()
    )
    employers = list(
        (await db.execute(select(Employer).where(Employer.user_id == user.id))).scalars()
    )
    today = (datetime.now(timezone.utc) + timedelta(minutes=tz_offset_minutes)).date()
    return aggregate(logs, employers, period, today)
