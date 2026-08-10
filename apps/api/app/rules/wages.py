"""Wage & remuneration checks — The Labour Act, 2017, Ch. 8 (§35-38) and
§106-107 (minimum wage).

  §35(1): short-term/casual work must be paid within 3 days (immediate for casual).
  §35(2): wages must be paid at least monthly.
  §36: annual increment of >= half a day's pay after 1 year of service.
  §37: festival expense = 1 month's basic remuneration/year (proportional if < 1 yr).
  §38: illegal deductions — only the closed §38(1) list is allowed.
  §106-107: minimum wage set by the Minimum Remuneration Fixation Committee.
"""

from ..config import settings
from ..schemas.submission import SubmissionCreate
from .base import Severity, Violation

# Rough conversion used only when the worker gives a daily wage but no monthly
# figure: ~26 working days/month. The Act itself does not fix this number.
DAYS_PER_MONTH = 26.0

# §38(1) whitelist of allowed deduction reasons (in English, lowercased).
ALLOWED_DEDUCTION_KEYWORDS = [
    "tax",
    "pf",
    "provident",
    "court",
    "service",
    "absence",
    "damage",
    "loss",
    "union",
    "loan",
]


def _monthly_wage_estimate(ctx: SubmissionCreate) -> float | None:
    """Combine monthly_wage and daily_wage into one monthly figure."""
    if ctx.monthly_wage is not None:
        return ctx.monthly_wage
    if ctx.daily_wage is not None:
        return ctx.daily_wage * DAYS_PER_MONTH
    return None


def check_minimum_wage(ctx: SubmissionCreate) -> list[Violation]:
    """§106-107: wages below the current statutory minimum are a violation."""
    monthly = _monthly_wage_estimate(ctx)
    if monthly is None:
        return []

    if monthly < settings.minimum_monthly_wage:
        return [
            Violation(
                rule_id="wages.minimum_wage",
                section_reference="§106-107",
                severity=Severity.WARNING,
                plain_explanation_en=(
                    f"Your monthly wage (NPR {monthly:,.0f}) is below the current minimum wage "
                    f"(NPR {settings.minimum_monthly_wage:,.0f}/month)."
                ),
                plain_explanation_ne=(
                    f"तपाईंको मासिक तलब (रु {monthly:,.0f}) हालको न्यूनतम पारिश्रमिक (रु "
                    f"{settings.minimum_monthly_wage:,.0f}/महिना) भन्दा कम छ।"
                ),
                suggested_action_en="Claim the shortfall — employers must repay the difference plus up to 2x compensation.",
                suggested_action_ne="घटी भुक्तानी माग गर्नुहोस् — रोजगारदाताले भिन्नता र बढीमा २ गुणा क्षतिपूर्ति तिर्नुपर्छ।",
            )
        ]

    return []


def check_payment_interval(ctx: SubmissionCreate) -> list[Violation]:
    """§35(2): wages must be paid at least once a month."""
    if ctx.wage_payment_interval_days is None:
        return []

    if ctx.wage_payment_interval_days > 30:
        return [
            Violation(
                rule_id="wages.payment_interval",
                section_reference="§35(2)",
                severity=Severity.WARNING,
                plain_explanation_en=(
                    f"Your wages are paid every {ctx.wage_payment_interval_days:g} days. The law requires "
                    "payment at least once a month."
                ),
                plain_explanation_ne=(
                    f"तपाईंको तलब प्रत्येक {ctx.wage_payment_interval_days:g} दिनमा तिरिन्छ। कानुनले महिनामा "
                    "कम्तीमा एकपटक तिर्नुपर्ने व्यवस्था गरेको छ।"
                ),
                suggested_action_en="Demand monthly payment; report repeated delays to the Labour Office.",
                suggested_action_ne="मासिक भुक्तानी माग गर्नुहोस्; बारम्बार ढिलाइ भएमा श्रम कार्यालयमा रिपोर्ट गर्नुहोस्।",
            )
        ]

    return []


def check_gratuity_deduction(ctx: SubmissionCreate) -> list[Violation]:
    """§38 + §53: gratuity is employer-funded (8.33%/month) — deducting it from
    the worker's pay is an illegal deduction not on the §38(1) list."""
    if ctx.gratuity_deducted is not True:
        return []

    return [
        Violation(
            rule_id="wages.gratuity_deduction",
            section_reference="§38(1), §53",
            severity=Severity.WARNING,
            plain_explanation_en=(
                "Gratuity was deducted from your pay. Gratuity is funded entirely by the employer "
                "(8.33% of basic pay) — it must not come out of your wages."
            ),
            plain_explanation_ne=(
                "तपाईंको तलबबाट उपदान काटिएको छ। उपदान पूर्ण रूपमा रोजगारदाताले तिर्ने व्यवस्था छ "
                "(आधार तलबको ८.३३%) — यो तपाईंको ज्यालाबाट काट्नु हुँदैन।"
            ),
            suggested_action_en="Ask for the deduction to be refunded; report illegal deductions to the Labour Office.",
            suggested_action_ne="काटिएको रकम फिर्ता माग गर्नुहोस्; अवैध कट्टी श्रम कार्यालयमा रिपोर्ट गर्नुहोस्।",
        )
    ]


def check_other_deductions(ctx: SubmissionCreate) -> list[Violation]:
    """§38: any deduction not matching the closed §38(1) whitelist is illegal."""
    if not ctx.other_deduction_reason:
        return []

    reason = ctx.other_deduction_reason.lower()
    # If the stated reason doesn't match any whitelisted item, treat it as illegal.
    if any(kw in reason for kw in ALLOWED_DEDUCTION_KEYWORDS):
        return []

    return [
        Violation(
            rule_id="wages.illegal_deduction",
            section_reference="§38(1)",
            severity=Severity.WARNING,
            plain_explanation_en=(
                f"A deduction was taken for \"{ctx.other_deduction_reason}\", which is not on the "
                "law's allowed list of deductions (§38(1))."
            ),
            plain_explanation_ne=(
                f"\"{ctx.other_deduction_reason}\" भन्ने कारणबाट कट्टी गरिएको छ, जुन कानुनले स्वीकार गरेको "
                "कट्टीको सूची (§38(1)) मा पर्दैन।"
            ),
            suggested_action_en="Challenge the deduction; illegal deductions must be repaid.",
            suggested_action_ne="कट्टीलाई चुनौती दिनुहोस्; अवैध कट्टी फिर्ता गर्नुपर्छ।",
        )
    ]


def check_annual_increment(ctx: SubmissionCreate) -> list[Violation]:
    """§36: after 1 year of service the worker is entitled to an increment of
    at least half a day's remuneration per year."""
    if ctx.years_worked is None or ctx.years_worked < 1:
        return []
    if ctx.received_annual_increment is False:
        return [
            Violation(
                rule_id="wages.annual_increment",
                section_reference="§36",
                severity=Severity.WARNING,
                plain_explanation_en=(
                    f"You have worked {ctx.years_worked:g} year(s) but received no annual increment. "
                    "After 1 year of service you are entitled to at least half a day's pay as an increment."
                ),
                plain_explanation_ne=(
                    f"तपाईंले {ctx.years_worked:g} वर्ष काम गर्नुभयो तर वार्षिक वृद्धि पाउनुभएन। १ वर्ष "
                    "सेवापछि कम्तीमा आधा दिनको ज्याला बराबर वार्षिक वृद्धि पाउने हक छ।"
                ),
                suggested_action_en="Claim your annual increment; refusal is a reportable violation.",
                suggested_action_ne="वार्षिक वृद्धि माग गर्नुहोस्; अस्वीकार उल्लङ्घन हो।",
            )
        ]

    return []


def check_festival_expense(ctx: SubmissionCreate) -> list[Violation]:
    """§37: festival expense = 1 month's basic remuneration/year, proportional
    if the worker has served less than a year."""
    if ctx.months_worked is None or ctx.months_worked < 1:
        return []
    if ctx.festival_expense_paid is False:
        return [
            Violation(
                rule_id="wages.festival_expense",
                section_reference="§37",
                severity=Severity.WARNING,
                plain_explanation_en=(
                    "You did not receive festival expense. The law requires 1 month's basic pay per year "
                    "(proportional if you've served less than a year)."
                ),
                plain_explanation_ne=(
                    "तपाईंले चाडपर्व खर्च पाउनुभएन। कानुनले वर्षभरिको आधार तलब बराबर चाडपर्व खर्च दिनुपर्ने "
                    "व्यवस्था गरेको छ (१ वर्षभन्दा कम सेवामा समानुपातिक)।"
                ),
                suggested_action_en="Claim your festival expense for the current year.",
                suggested_action_ne="चालु वर्षको चाडपर्व खर्च माग गर्नुहोस्।",
            )
        ]

    return []


ALL_RULES = [
    check_minimum_wage,
    check_payment_interval,
    check_gratuity_deduction,
    check_other_deductions,
    check_annual_increment,
    check_festival_expense,
]


def run(ctx: SubmissionCreate) -> list[Violation]:
    return [v for fn in ALL_RULES for v in fn(ctx)]
