"""Background-calculated values: never asked directly, derived server-side.

These keep the stored record self-contained so the AI-analysis endpoint can
emit a single JSON document without re-deriving anything.
"""

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

WEEKS_PER_MONTH = 4.333


def age_from_dob(dob: date | None) -> int | None:
    """Age from date of birth (store DOB, calculate age in the background)."""
    if not dob:
        return None
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age if 0 <= age <= 120 else None


def _hours(per_day: float | None, days_per_week: float | None, months_per_year: float | None) -> dict[str, float | None]:
    """Derive daily/weekly/monthly hour totals from the parts the user entered.

    monthly = weekly hours × average weeks/month. When the worker gave a
    months-per-year figure we scale by it (e.g. 9 months/year → 75%).
    """
    daily = per_day
    weekly = per_day * days_per_week if per_day is not None and days_per_week is not None else None
    if weekly is None:
        return {"daily": daily, "weekly": None, "monthly": None}
    scale = (months_per_year / 12.0) if months_per_year is not None and months_per_year > 0 else 1.0
    monthly = weekly * WEEKS_PER_MONTH * scale
    return {"daily": daily, "weekly": weekly, "monthly": monthly}


def compute_contracted_totals(data: dict[str, Any]) -> dict[str, float | None]:
    h = _hours(
        _as_float(data.get("contract_hours_per_day")),
        _as_float(data.get("contract_days_per_week")),
        _as_float(data.get("contract_months_per_year")),
    )
    return {
        "contract_daily_hours": h["daily"],
        "contract_weekly_hours": h["weekly"],
        "contract_monthly_hours": h["monthly"],
    }


def compute_actual_totals(data: dict[str, Any]) -> dict[str, float | None]:
    h = _hours(
        _as_float(data.get("actual_hours_per_day")),
        _as_float(data.get("actual_days_per_week")),
        _as_float(data.get("actual_months_per_year")),
    )
    return {
        "actual_daily_hours": h["daily"],
        "actual_weekly_hours": h["weekly"],
        "actual_monthly_hours": h["monthly"],
    }


def compute_monthly_salary(data: dict[str, Any], totals: dict[str, float | None]) -> float | None:
    """Derive monthly salary from pay unit + promised amount.

    hourly: promised × actual weekly hours × weeks/month
    daily:  promised × actual days/week × weeks/month
    weekly: promised × weeks/month
    monthly: promised (as-is)
    """
    unit = data.get("pay_unit")
    wage = _as_float(data.get("promised_wage"))
    if unit is None or wage is None:
        return None
    if unit == "monthly":
        return wage
    if unit == "weekly":
        return round(wage * WEEKS_PER_MONTH, 2)
    if unit == "daily":
        days = _as_float(data.get("actual_days_per_week"))
        if days is None:
            days = _as_float(data.get("contract_days_per_week"))
        if days is None:
            return None
        return round(wage * days * WEEKS_PER_MONTH, 2)
    if unit == "hourly":
        weekly = totals.get("actual_weekly_hours") or totals.get("contract_weekly_hours")
        if weekly is None:
            return None
        return round(wage * weekly * WEEKS_PER_MONTH, 2)
    return None


def compute_employer_background(data: dict[str, Any]) -> dict[str, float | None]:
    """All background-calculated employer fields in one call."""
    out: dict[str, float | None] = {}
    out.update(compute_contracted_totals(data))
    out.update(compute_actual_totals(data))
    out["monthly_salary_calculated"] = compute_monthly_salary(
        data, {"actual_weekly_hours": out["actual_weekly_hours"], "contract_weekly_hours": out["contract_weekly_hours"]}
    )
    return out


def compute_overtime_minutes(scheduled_end: time | None, ended_at: datetime | None, log_date: date | None) -> int:
    """Minutes worked beyond the scheduled end time (same-day; wraps past midnight).

    If the shift ended earlier than scheduled, there is no overtime.
    """
    if scheduled_end is None or ended_at is None or log_date is None:
        return 0
    shift_start = datetime.combine(log_date, scheduled_end, tzinfo=timezone.utc)
    delta = ended_at.astimezone(timezone.utc) - shift_start
    if delta < timedelta(hours=-1):
        # Ended "earlier" — treat as no overtime unless it's clearly the next
        # day (ended between 00:00 and scheduled end on the following day).
        if delta >= timedelta(hours=-23):
            return 0
    if delta < timedelta(0):
        return 0
    return max(0, int(delta.total_seconds() // 60))


def _as_float(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
