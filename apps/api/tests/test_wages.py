"""Tests for the wage rules (§35-38, §106-107)."""

from app.rules.engine import run_rules
from app.schemas.submission import EmploymentType, SubmissionCreate


def base(**overrides):
    return SubmissionCreate(employment_type=EmploymentType.REGULAR, **overrides)


def rule_ids(ctx) -> set[str]:
    return {v.rule_id for v in run_rules(ctx)}


def test_above_minimum_wage_ok():
    ctx = base(monthly_wage=30000)
    assert "wages.minimum_wage" not in rule_ids(ctx)


def test_below_minimum_wage_flags():
    ctx = base(monthly_wage=8000)
    assert "wages.minimum_wage" in rule_ids(ctx)


def test_daily_wage_below_minimum_flags():
    # daily_wage * 26 working days is used as the monthly estimate.
    ctx = base(daily_wage=400)
    assert "wages.minimum_wage" in rule_ids(ctx)


def test_payment_interval_over_month_flags():
    # §35(2): payments must be at least monthly.
    ctx = base(wage_payment_interval_days=45)
    assert "wages.payment_interval" in rule_ids(ctx)


def test_gratuity_deduction_is_illegal():
    # §38 + §53: gratuity is employer-funded, deducting it from pay is illegal.
    ctx = base(gratuity_deducted=True)
    assert "wages.gratuity_deduction" in rule_ids(ctx)


def test_unknown_deduction_reason_flags():
    # §38(1) closed whitelist — "phone charges" isn't on it.
    ctx = base(other_deduction_reason="Phone bill deducted from salary")
    assert "wages.illegal_deduction" in rule_ids(ctx)


def test_tax_deduction_is_allowed():
    # Tax is explicitly on the §38(1) whitelist.
    ctx = base(other_deduction_reason="Income tax")
    assert "wages.illegal_deduction" not in rule_ids(ctx)


def test_annual_increment_after_one_year():
    # §36: increment due after 1 year of service.
    ctx = base(years_worked=2, received_annual_increment=False)
    assert "wages.annual_increment" in rule_ids(ctx)

    ok = base(years_worked=2, received_annual_increment=True)
    assert "wages.annual_increment" not in rule_ids(ok)


def test_festival_expense_after_one_month():
    # §37: festival expense proportional even under a year of service.
    ctx = base(months_worked=6, festival_expense_paid=False)
    assert "wages.festival_expense" in rule_ids(ctx)
