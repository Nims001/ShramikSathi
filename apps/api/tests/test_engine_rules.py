"""Tests for leave (§40-51), social security (§52-55), contract, and termination
(§144-148) rules, plus engine-level aggregation."""

from app.rules.engine import run_rules
from app.schemas.submission import EmploymentType, SubmissionCreate


def base(**overrides):
    return SubmissionCreate(employment_type=EmploymentType.REGULAR, **overrides)


def rule_ids(ctx) -> set[str]:
    return {v.rule_id for v in run_rules(ctx)}


# ---- Leave (§40-51) -------------------------------------------------------

def test_weekly_leave_below_one_day_flags():
    ctx = base(weekly_leave_taken_per_month=0.5)
    assert "leave.weekly_leave" in rule_ids(ctx)


def test_sick_leave_denied_is_a_right():
    # §44: sick leave is a right — cannot be refused.
    ctx = base(sick_leave_denied=True)
    assert "leave.sick_leave" in rule_ids(ctx)


def test_maternity_leave_denied_flags():
    ctx = base(maternity_leave_denied=True)
    assert "leave.maternity_leave" in rule_ids(ctx)


def test_paternity_leave_denied_flags():
    ctx = base(paternity_leave_denied=True)
    assert "leave.paternity_leave" in rule_ids(ctx)


def test_mourning_leave_denied_flags():
    ctx = base(mourning_leave_denied=True)
    assert "leave.mourning_leave" in rule_ids(ctx)


# ---- Social security (§52-55) ---------------------------------------------

def test_pf_deducted_but_not_deposited_is_critical():
    # §52(6): employer owes the cash amount directly.
    ctx = base(pf_deducted=True, pf_deposited=False)
    v = next(v for v in run_rules(ctx) if v.rule_id == "social.pf_not_deposited")
    assert v.severity == "critical"


def test_pf_deposited_is_ok():
    ctx = base(pf_deducted=True, pf_deposited=True)
    assert "social.pf_not_deposited" not in rule_ids(ctx)


def test_gratuity_not_paid_after_one_year_flags():
    ctx = base(years_worked=2, gratuity_paid_by_employer=False)
    assert "social.gratuity_not_paid" in rule_ids(ctx)


def test_missing_insurance_flags():
    ctx = base(medical_insurance_provided=False, accidental_insurance_provided=False)
    ids = rule_ids(ctx)
    assert "social.medical_insurance_missing" in ids
    assert "social.accidental_insurance_missing" in ids


# ---- Contract -------------------------------------------------------------

def test_no_written_contract_flags():
    ctx = base(has_written_contract=False)
    assert "contract.no_written_contract" in rule_ids(ctx)


def test_written_contract_is_ok():
    ctx = base(has_written_contract=True)
    assert "contract.no_written_contract" not in rule_ids(ctx)


# ---- Termination (§144-148) -----------------------------------------------

def test_no_termination_triggers_nothing():
    # An on-going job must not fire termination rules.
    ctx = base(termination_occurred=False, notice_given_days=0)
    ids = rule_ids(ctx)
    assert not any(i.startswith("termination.") for i in ids)


def test_short_notice_after_long_service_flags():
    # §144: >1yr service needs 30 days notice; 5 days is too short.
    ctx = base(termination_occurred=True, months_worked=24, notice_given_days=5)
    assert "termination.notice_period" in rule_ids(ctx)


def test_full_notice_is_ok():
    ctx = base(termination_occurred=True, months_worked=24, notice_given_days=30)
    assert "termination.notice_period" not in rule_ids(ctx)


def test_retrenchment_compensation_shortfall_is_critical():
    # §145(7): 1 month's pay per year of service. 2 years -> 2 months; only 0.5 paid.
    ctx = base(
        termination_occurred=True,
        months_worked=24,
        retrenchment_compensation_months_paid=0.5,
    )
    v = next(v for v in run_rules(ctx) if v.rule_id == "termination.retrenchment_compensation")
    assert v.severity == "critical"


def test_final_settlement_within_15_days():
    ctx = base(termination_occurred=True, final_settlement_within_15_days=False)
    assert "termination.final_settlement" in rule_ids(ctx)


# ---- Engine-level behavior -------------------------------------------------

def test_act_prevails_note_only_when_violations_exist():
    # §3(2) reminder should appear alongside findings, never alone.
    clean = base(hours_per_day=8, hours_per_week=40, monthly_wage=30000)
    assert "general.act_prevails" not in rule_ids(clean)

    dirty = base(hours_per_day=10, overtime_rate_paid=1.0)
    assert "general.act_prevails" in rule_ids(dirty)


def test_violations_are_bilingual():
    # Every finding must carry English + Nepali explanations and actions.
    ctx = base(hours_per_day=13)
    for v in run_rules(ctx):
        assert v.plain_explanation_en and v.plain_explanation_ne
        assert v.suggested_action_en and v.suggested_action_ne


def test_no_llm_imports_in_engine():
    # Determinism guard: the rule engine must not depend on an LLM client.
    import app.rules.engine as engine

    source = __import__("inspect").getsource(engine)
    assert "openai" not in source.lower()
    assert "anthropic" not in source.lower()
