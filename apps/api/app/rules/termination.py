"""Termination, notice & retrenchment checks — The Labour Act, 2017, Ch. 21
(§143-148).

  §144: notice period — 1 day (<4 weeks employment) / 7 days (4 weeks-1 year) /
        30 days (>1 year). If no notice given, employer owes pay equal to the
        notice-period remuneration (§144(2)).
  §145(7): retrenchment compensation = 1 month's basic pay per year of service
        (pro-rated if <1 year).
  §148: all final dues must be settled within 15 days of termination.

These checks only run when the worker says a termination happened; an on-going
job with no termination triggers nothing here.
"""

from ..schemas.submission import SubmissionCreate
from .base import Severity, Violation

MONTHS_IN_YEAR = 12.0


def _required_notice_days(months_worked: float) -> int:
    """§144: notice tiers by length of service."""
    if months_worked < 1:
        return 1
    if months_worked <= MONTHS_IN_YEAR:
        return 7
    return 30


def check_notice_period(ctx: SubmissionCreate) -> list[Violation]:
    """§144: employer must give the notice period owed, or pay for it (§144(2))."""
    if ctx.termination_occurred is not True:
        return []
    if ctx.months_worked is None or ctx.notice_given_days is None:
        return []

    required = _required_notice_days(ctx.months_worked)
    if ctx.notice_given_days >= required:
        return []

    return [
        Violation(
            rule_id="termination.notice_period",
            section_reference="§144(1), §144(2)",
            severity=Severity.WARNING,
            plain_explanation_en=(
                f"With {ctx.months_worked:g} month(s) of service you were entitled to {required} day(s) "
                f"of notice, but only {ctx.notice_given_days:g} day(s) was given. If no proper notice was "
                "given, the employer must pay you the notice-period remuneration."
            ),
            plain_explanation_ne=(
                f"{ctx.months_worked:g} महिना सेवा अनुसार तपाईं {required} दिन सूचनाको हकदार हुनुहुन्थ्यो, "
                f"तर {ctx.notice_given_days:g} दिन मात्र दिइयो। उचित सूचना नदिएमा रोजगारदाताले सूचना अवधिको "
                "ज्याला तिर्नुपर्छ।"
            ),
            suggested_action_en=(
                "Claim the notice-period pay owed to you under §144(2); complain to the Labour Office if unpaid."
            ),
            suggested_action_ne=(
                "§144(2) अनुसार सूचना अवधिको ज्याला माग गर्नुहोस्; नतिरेमा श्रम कार्यालयमा उजुरी गर्नुहोस्।"
            ),
        )
    ]


def check_retrenchment_compensation(ctx: SubmissionCreate) -> list[Violation]:
    """§145(7): retrenchment compensation = 1 month's basic pay per year of
    service, pro-rated for partial years."""
    if ctx.termination_occurred is not True:
        return []
    if ctx.months_worked is None or ctx.retrenchment_compensation_months_paid is None:
        return []

    # Entitlement in months of pay (pro-rated below one full year of service).
    entitlement = max(ctx.months_worked / MONTHS_IN_YEAR, ctx.months_worked / MONTHS_IN_YEAR)
    if ctx.retrenchment_compensation_months_paid >= entitlement - 0.001:
        return []

    return [
        Violation(
            rule_id="termination.retrenchment_compensation",
            section_reference="§145(7)",
            severity=Severity.CRITICAL,
            plain_explanation_en=(
                f"On termination after {ctx.months_worked:g} month(s) of service you were entitled to "
                f"{entitlement:g} month(s) of basic pay as compensation, but received only "
                f"{ctx.retrenchment_compensation_months_paid:g} month(s)."
            ),
            plain_explanation_ne=(
                f"{ctx.months_worked:g} महिना सेवापछि बर्खास्त हुँदा तपाईं {entitlement:g} महिनाको आधार "
                f"तलब क्षतिपूर्ति पाउन हकदार हुनुहुन्थ्यो, तर {ctx.retrenchment_compensation_months_paid:g} "
                "महिना मात्र पाउनुभयो।"
            ),
            suggested_action_en=(
                "Claim the unpaid compensation difference; the Labour Court route is available if the "
                "employer refuses."
            ),
            suggested_action_ne=(
                "नतिरिएको क्षतिपूर्तिको भिन्नता माग गर्नुहोस्; रोजगारदाताले अस्वीकार गरेमा श्रम अदालतको "
                "मार्ग उपलब्ध छ।"
            ),
        )
    ]


def check_final_settlement(ctx: SubmissionCreate) -> list[Violation]:
    """§148: all dues must be settled within 15 days of termination."""
    if ctx.termination_occurred is not True:
        return []
    if ctx.final_settlement_within_15_days is False:
        return [
            Violation(
                rule_id="termination.final_settlement",
                section_reference="§148",
                severity=Severity.WARNING,
                plain_explanation_en=(
                    "Your final settlement (all dues) was not paid within 15 days of termination. "
                    "The law requires settlement within 15 days."
                ),
                plain_explanation_ne=(
                    "बर्खास्ती भएको १५ दिनभित्र तपाईंको अन्तिम भुक्तानी (सबै बक्यौता) तिरिएको छैन। "
                    "कानुनले १५ दिनभित्र भुक्तानी गर्नुपर्ने व्यवस्था गरेको छ।"
                ),
                suggested_action_en="Demand your final settlement; complain to the Labour Office if it stays unpaid.",
                suggested_action_ne="अन्तिम भुक्तानी माग गर्नुहोस्; नतिरेको अवस्थामा श्रम कार्यालयमा उजुरी गर्नुहोस्।",
            )
        ]

    return []


ALL_RULES = [
    check_notice_period,
    check_retrenchment_compensation,
    check_final_settlement,
]


def run(ctx: SubmissionCreate) -> list[Violation]:
    return [v for fn in ALL_RULES for v in fn(ctx)]
