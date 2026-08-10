"""Tests for the working-hours rules (§28-31)."""

from app.rules.engine import run_rules
from app.schemas.submission import EmploymentType, SubmissionCreate


def base(**overrides):
    return SubmissionCreate(employment_type=EmploymentType.REGULAR, **overrides)


def rule_ids(ctx) -> set[str]:
    return {v.rule_id for v in run_rules(ctx)}


def test_eight_hours_day_is_ok():
    # §28(1): exactly 8 hrs/day, 48 hrs/week with proper overtime pay -> no hours violations.
    ctx = base(hours_per_day=8, hours_per_week=48, overtime_rate_paid=1.5)
    assert not {"hours.max_daily", "hours.max_weekly"} & rule_ids(ctx)


def test_nine_hours_without_overtime_pay_flags_daily_limit():
    # §28(1) + §31(1): >8h/day but overtime not paid at 1.5x.
    ctx = base(hours_per_day=9, hours_per_week=45, overtime_rate_paid=1.0)
    assert "hours.max_daily" in rule_ids(ctx)


def test_nine_hours_with_1_5x_pay_is_legal_overtime():
    # 9h/day paid at 1.5x is permitted overtime (8 + 1 <= 12).
    ctx = base(hours_per_day=9, hours_per_week=45, overtime_rate_paid=1.5)
    assert "hours.max_daily" not in rule_ids(ctx)


def test_thirteen_hours_is_always_critical():
    # §30(1): 8 + 4 max overtime = 12, so 13 hours/day is unlawful even if paid.
    ctx = base(hours_per_day=13, overtime_rate_paid=1.5)
    ids = rule_ids(ctx)
    assert "hours.max_daily" in ids
    v = next(v for v in run_rules(ctx) if v.rule_id == "hours.max_daily")
    assert v.severity == "critical"


def test_weekly_over_48_without_1_5x_flags_weekly_limit():
    ctx = base(hours_per_week=50, hours_per_day=7, overtime_rate_paid=1.0)
    assert "hours.max_weekly" in rule_ids(ctx)


def test_weekly_over_72_is_critical():
    ctx = base(hours_per_week=75, hours_per_day=10)
    v = next(v for v in run_rules(ctx) if v.rule_id == "hours.max_weekly")
    assert v.severity == "critical"


def test_overtime_cap_24_hours_per_week():
    # §30(1): 24h/week overtime is fine; 25h is unlawful even if paid.
    ok = base(overtime_hours_per_week=24, overtime_rate_paid=1.5)
    assert "hours.overtime_cap" not in rule_ids(ok)

    bad = base(overtime_hours_per_week=25, overtime_rate_paid=1.5)
    assert "hours.overtime_cap" in rule_ids(bad)


def test_overtime_paid_below_1_5_flags_pay_issue():
    # §31(1): overtime worked but paid only 1.0x.
    ctx = base(overtime_hours_per_week=5, overtime_rate_paid=1.0)
    assert "hours.overtime_pay" in rule_ids(ctx)


def test_rest_break_violation():
    # §28(2): no 30-min break after 5 continuous hours.
    ctx = base(worked_over_5h_without_break=True)
    assert "hours.rest_break" in rule_ids(ctx)


def test_missing_hours_data_no_violations():
    # If the worker doesn't know hours, no hours rule should fire (skip, don't guess).
    ctx = base()
    ids = rule_ids(ctx)
    assert not any(i.startswith("hours.") for i in ids)
