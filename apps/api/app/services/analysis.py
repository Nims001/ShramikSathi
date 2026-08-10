"""Analysis: assemble one JSON document describing a worker's situation.

The document is structured so that either the deterministic rule engine (below)
or a prompting AI can find violations citing The Labour Act, 2017 (Nepal). It
ships the raw employer + log data plus derived statistics and the engine's own
findings — everything the dashboard and any AI explainer need.
"""

import json
from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Employer, User, WeeklySetting, WorkLog
from ..rules.engine import ALL_CHECKS
from ..schemas.submission import SubmissionCreate

WEEKS_PER_MONTH = 4.333


async def build_analysis_document(db: AsyncSession, user: User) -> dict:
    employers = list(
        (
            await db.execute(
                select(Employer).where(Employer.user_id == user.id).order_by(Employer.created_at)
            )
        ).scalars()
    )
    settings = list(
        (
            await db.execute(
                select(WeeklySetting)
                .where(WeeklySetting.employer_id.in_([e.id for e in employers]))
                if employers
                else select(WeeklySetting).where(1 == 0)
            )
        ).scalars()
    ) if employers else []
    logs = list(
        (
            await db.execute(
                select(WorkLog)
                .where(WorkLog.user_id == user.id)
                .order_by(WorkLog.log_date.desc())
            )
        ).scalars()
    ) if employers else []

    employers_out = []
    for employer in employers:
        employer_out = {
            k: _serialize(getattr(employer, k))
            for k in (
                "id",
                "employer_name",
                "work_province",
                "work_district",
                "work_address",
                "skill_level",
                "industry",
                "employment_type",
                "job_title",
                "hiring_channel",
                "contractor_name",
                "tenure_years",
                "tenure_months",
                "on_probation",
                "probation_since",
                "contract_hours_per_day",
                "contract_break_start",
                "contract_break_end",
                "contract_break_unspecified",
                "contract_days_per_week",
                "contract_break_days",
                "contract_break_days_unspecified",
                "contract_months_per_year",
                "contract_break_months",
                "contract_daily_hours",
                "contract_weekly_hours",
                "contract_monthly_hours",
                "actual_hours_per_day",
                "actual_break_start",
                "actual_break_end",
                "actual_break_unspecified",
                "actual_days_per_week",
                "actual_break_days",
                "actual_break_days_unspecified",
                "actual_months_per_year",
                "actual_break_months",
                "actual_daily_hours",
                "actual_weekly_hours",
                "actual_monthly_hours",
                "overtime_rule",
                "overtime_hours_per_unit",
                "overtime_unit",
                "overtime_rate",
                "overtime_rate_other",
                "overtime_consent",
                "night_work",
                "night_allowance",
                "pay_unit",
                "promised_wage",
                "monthly_salary_calculated",
                "payment_frequency",
                "payment_method",
                "received_annual_increment",
                "festival_expense_paid",
                "other_deduction_reason",
                "weekly_leave_days_per_week",
                "weekly_off_day_guaranteed",
                "worked_off_day_paid_and_replaced",
                "public_holiday_paid_leave",
                "sick_leave_denied",
                "pregnant_or_maternity_last_year",
                "maternity_leave_denied",
                "paternity_leave_denied",
                "mourning_leave_denied",
                "has_written_contract",
                "contract_states_wage",
                "contract_states_hours",
                "contract_states_leave",
                "contract_states_termination",
                "contract_explained_in_own_language",
                "ssf_registered",
                "pf_deducted",
                "pf_deposited",
                "gratuity_deducted",
                "gratuity_paid_by_employer",
                "medical_insurance_provided",
                "accidental_insurance_provided",
                "paid_fee_to_get_job",
                "wage_withheld_before_start",
                "employer_holds_documents",
                "free_to_leave_during_off_hours",
                "abuse_experienced",
                "terminated",
                "notice_given_days",
                "retrenchment_compensation_months",
                "final_settlement_within_15_days",
                "other_clauses",
            )
        }
        employers_out.append(
            {
                "employer": employer_out,
                "weekly_setting": _serialize_weekly_setting(
                    next((s for s in settings if s.employer_id == employer.id), None)
                ),
                "logs": [_serialize(l) for l in logs if l.employer_id == employer.id],
                "deterministic_findings": _run_deterministic(user, employer),
            }
        )

    return {
        "meta": {
            "generated_at": _now_iso(),
            "law_framework": "The Labour Act, 2017 (Nepal) and the Minimum Remuneration Fixation, 2081 (2024).",
            "analysis_mode": "Combine the fields below with the Act. Flag any field that suggests a rights violation and cite the section.",
        },
        "user": {
            "id": str(user.id),
            "age": user.age,
            "gender": user.gender,
            "ethnicity": user.ethnicity,
            "education_level": user.education_level,
            "language": user.language,
        },
        "employers": employers_out,
        "stats": _compute_stats(logs, employers),
    }


def _run_deterministic(user: User, employer: Employer) -> list[dict]:
    """Bridge the employer record into the existing SubmissionCreate engine."""
    actual_weekly = employer.actual_weekly_hours or employer.contract_weekly_hours
    overtime_weekly = None
    if employer.actual_weekly_hours is not None and employer.contract_weekly_hours is not None:
        overtime_weekly = max(0.0, employer.actual_weekly_hours - employer.contract_weekly_hours)

    over_5h_no_break = None
    if (employer.actual_hours_per_day or employer.contract_hours_per_day) is not None:
        if (employer.actual_hours_per_day or employer.contract_hours_per_day) > 5:
            over_5h_no_break = bool(
                employer.actual_break_unspecified or employer.contract_break_unspecified
            )

    ctx = SubmissionCreate(
        employment_type=employer.employment_type or "regular",
        sector=employer.industry,
        province=employer.work_province,
        gender=user.gender,
        hours_per_day=employer.actual_hours_per_day or employer.contract_hours_per_day,
        hours_per_week=actual_weekly,
        worked_over_5h_without_break=over_5h_no_break,
        overtime_hours_per_week=overtime_weekly,
        overtime_rate_paid=_rate_float(employer.overtime_rate),
        daily_wage=employer.promised_wage if employer.pay_unit == "daily" else None,
        monthly_wage=employer.monthly_salary_calculated,
        wage_payment_interval_days=_payment_interval_days(employer.payment_frequency),
        months_worked=employer.tenure_months,
        years_worked=employer.tenure_years,
        received_annual_increment=employer.received_annual_increment,
        festival_expense_paid=employer.festival_expense_paid,
        other_deduction_reason=employer.other_deduction_reason,
        weekly_leave_taken_per_month=employer.weekly_leave_days_per_week,
        sick_leave_denied=employer.sick_leave_denied,
        maternity_leave_denied=employer.maternity_leave_denied,
        paternity_leave_denied=employer.paternity_leave_denied,
        mourning_leave_denied=employer.mourning_leave_denied,
        has_written_contract=employer.has_written_contract,
        pf_deducted=employer.pf_deducted,
        pf_deposited=employer.pf_deposited,
        gratuity_deducted=employer.gratuity_deducted,
        gratuity_paid_by_employer=employer.gratuity_paid_by_employer,
        medical_insurance_provided=employer.medical_insurance_provided,
        accidental_insurance_provided=employer.accidental_insurance_provided,
        termination_occurred=employer.terminated,
        notice_given_days=employer.notice_given_days,
        retrenchment_compensation_months_paid=employer.retrenchment_compensation_months,
        final_settlement_within_15_days=employer.final_settlement_within_15_days,
    )
    findings = []
    for check in ALL_CHECKS:
        try:
            findings.extend(check(ctx))
        except Exception:
            continue
    return [f.model_dump() for f in findings]


def _rate_float(rate: str | None) -> float | None:
    """Overtime rate percent → multiplier expected by the rules engine (≤10)."""
    if rate == "100":
        return 1.0
    if rate == "150":
        return 1.5
    return None


def _payment_interval_days(frequency: str | None) -> float | None:
    """payment_frequency → days between wage payments for the §35(2) check."""
    return {"daily": 1.0, "weekly": 7.0, "monthly": 30.0}.get(frequency)


def _compute_stats(logs: list[WorkLog], employers: list[Employer]) -> dict:
    """Daily / weekly / monthly aggregates over the work logs."""
    today = date.today()

    def covered(days: int) -> list[WorkLog]:
        return [l for l in logs if (today - l.log_date).days <= days]

    def totals(logs_subset: list[WorkLog]) -> dict:
        overtime = sum(l.overtime_minutes or 0 for l in logs_subset)
        paid = sum(l.paid_amount or 0 for l in logs_subset)
        promised = sum(l.promised_amount or 0 for l in logs_subset)
        return {
            "days_worked": len(logs_subset),
            "overtime_minutes": overtime,
            "overtime_hours_rounded": round(overtime / 60, 1),
            "paid_amount": paid,
            "promised_amount": promised,
            "amount_due": max(0.0, promised - paid),
        }

    return {
        "today": totals(covered(0)),
        "last_7_days": totals(covered(7)),
        "last_30_days": totals(covered(30)),
        "last_90_days": totals(covered(90)),
        "employer_count": len(employers),
    }


def _serialize(value) -> str | int | float | bool | list | dict | None:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    if hasattr(value, "__table__"):
        columns = value.__table__.columns.keys()
        return {k: _serialize(getattr(value, k)) for k in columns}
    if hasattr(value, "model_dump"):
        return value.model_dump()
    try:
        return json.loads(json.dumps(value, default=str))
    except (TypeError, ValueError):
        return str(value)


def _serialize_weekly_setting(setting) -> dict | None:
    """Serialize a WeeklySetting, normalizing break days to weekday strings.

    The app stores `break_days_this_week` as strings "0".."6" (see the logging
    UI and the AI request schema), but older rows may hold ints. The AI request
    validation requires strings, so coerce them here.
    """
    out = _serialize(setting) if setting is not None else None
    if out:
        break_days = out.get("break_days_this_week")
        if break_days:
            out["break_days_this_week"] = [str(d) for d in break_days]
    return out


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
