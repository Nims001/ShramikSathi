"""Working-hours checks — The Labour Act, 2017, Ch. 7 (§28-31).

Rules are written exactly as the Act sets them out:
  §28(1): max 8 hrs/day and 48 hrs/week.
  §28(2): mandatory 30-minute rest after 5 continuous hours.
  §30(1): overtime capped at 4 hrs/day and 24 hrs/week.
  §31(1): overtime must be paid at 1.5x basic remuneration.
"""

from ..schemas.submission import SubmissionCreate
from .base import Severity, Violation

# The absolute daily cap is 8h of normal work + 4h of max overtime = 12h (§28(1), §30(1)).
ABSOLUTE_DAILY_CAP = 12
# Normal weekly cap (48h) + max weekly overtime (24h) = 72h (§28(1), §30(1)).
ABSOLUTE_WEEKLY_CAP = 72
OVERTIME_RATE = 1.5  # §31(1)


def check_max_daily(ctx: SubmissionCreate) -> list[Violation]:
    """§28(1): more than 8 hrs/day is only lawful as overtime at 1.5x pay,
    and never above 12 hrs/day even as overtime."""
    if ctx.hours_per_day is None:
        return []

    if ctx.hours_per_day > ABSOLUTE_DAILY_CAP:
        return [
            Violation(
                rule_id="hours.max_daily",
                section_reference="§28(1), §30(1)",
                severity=Severity.CRITICAL,
                plain_explanation_en=(
                    f"You worked {ctx.hours_per_day:g} hours/day. The law caps work at 8 hours/day, "
                    "with at most 4 hours/day of overtime — so 12 hours/day is the absolute maximum."
                ),
                plain_explanation_ne=(
                    f"तपाईंले दिनको {ctx.hours_per_day:g} घण्टा काम गर्नुभयो। कानुनले दिनको ८ घण्टा "
                    "कामको सीमा तोकेको छ, र बढीमा दिनको ४ घण्टा ओभरटाइम — त्यसैले दिनको १२ घण्टा नै "
                    "अधिकतम सीमा हो।"
                ),
                suggested_action_en=(
                    "Work beyond 12 hours/day is unlawful. File a complaint with the Labour Office "
                    "within 6 months of the violation."
                ),
                suggested_action_ne=(
                    "दिनको १२ घण्टाभन्दा बढी काम गराउनु कानुनविपरीत हो। उल्लङ्घन भएको ६ महिनाभित्र "
                    "श्रम कार्यालयमा उजुरी दिनुहोस्।"
                ),
            )
        ]

    if ctx.hours_per_day > 8:
        # Over the daily cap but within the overtime allowance — legal only if
        # the employer pays 1.5x overtime (§31(1)).
        if ctx.overtime_rate_paid is None or ctx.overtime_rate_paid < OVERTIME_RATE:
            return [
                Violation(
                    rule_id="hours.max_daily",
                    section_reference="§28(1), §31(1)",
                    severity=Severity.WARNING,
                    plain_explanation_en=(
                        f"You worked {ctx.hours_per_day:g} hours/day, above the 8-hour daily limit. "
                        "Hours above 8 must be paid as overtime at 1.5x your normal wage."
                    ),
                    plain_explanation_ne=(
                        f"तपाईंले दिनको {ctx.hours_per_day:g} घण्टा काम गर्नुभयो, जुन दिनको ८ घण्टाको "
                        "सीमाभन्दा बढी हो। ८ घण्टाभन्दा माथिको समय १.५ गुणा ओभरटाइम दरमा तिर्नुपर्छ।"
                    ),
                    suggested_action_en=(
                        "Ask your employer for the 1.5x overtime rate. If refused, complain to the "
                        "Labour Office within 6 months."
                    ),
                    suggested_action_ne=(
                        "आफ्नो रोजगारदातासँग १.५ गुणा ओभरटाइम दर माग गर्नुहोस्। अस्वीकार भएमा ६ महिनाभित्र "
                        "श्रम कार्यालयमा उजुरी गर्नुहोस्।"
                    ),
                )
            ]

    return []


def check_max_weekly(ctx: SubmissionCreate) -> list[Violation]:
    """§28(1): more than 48 hrs/week is only lawful as paid overtime,
    and never above 72 hrs/week (48h + 24h max overtime)."""
    if ctx.hours_per_week is None:
        return []

    if ctx.hours_per_week > ABSOLUTE_WEEKLY_CAP:
        return [
            Violation(
                rule_id="hours.max_weekly",
                section_reference="§28(1), §30(1)",
                severity=Severity.CRITICAL,
                plain_explanation_en=(
                    f"You worked {ctx.hours_per_week:g} hours/week. The absolute weekly maximum is "
                    "72 hours (48 normal + 24 overtime)."
                ),
                plain_explanation_ne=(
                    f"तपाईंले हप्ताको {ctx.hours_per_week:g} घण्टा काम गर्नुभयो। हप्ताको अधिकतम सीमा ७२ "
                    "घण्टा हो (४८ सामान्य + २४ ओभरटाइम)।"
                ),
                suggested_action_en="This is unlawful. Complain to the Labour Office within 6 months.",
                suggested_action_ne="यो कानुनविपरीत हो। ६ महिनाभित्र श्रम कार्यालयमा उजुरी गर्नुहोस्।",
            )
        ]

    if ctx.hours_per_week > 48:
        # Above 48h but within the overtime window — requires 1.5x pay (§31(1)).
        if ctx.overtime_rate_paid is None or ctx.overtime_rate_paid < OVERTIME_RATE:
            return [
                Violation(
                    rule_id="hours.max_weekly",
                    section_reference="§28(1), §31(1)",
                    severity=Severity.WARNING,
                    plain_explanation_en=(
                        f"You worked {ctx.hours_per_week:g} hours/week, above the 48-hour weekly limit. "
                        "Everything above 48 hours must be paid at 1.5x."
                    ),
                    plain_explanation_ne=(
                        f"तपाईंले हप्ताको {ctx.hours_per_week:g} घण्टा काम गर्नुभयो, जुन हप्ताको ४८ घण्टाको "
                        "सीमाभन्दा बढी हो। ४८ घण्टाभन्दा माथिको सबै समय १.५ गुणा दरमा तिर्नुपर्छ।"
                    ),
                    suggested_action_en="Ask for 1.5x overtime pay; if refused, complain to the Labour Office.",
                    suggested_action_ne="१.५ गुणा ओभरटाइम दर माग गर्नुहोस्; अस्वीकार भएमा श्रम कार्यालयमा उजुरी गर्नुहोस्।",
                )
            ]

    return []


def check_rest_break(ctx: SubmissionCreate) -> list[Violation]:
    """§28(2): a 30-minute rest break is mandatory after 5 continuous hours."""
    if ctx.worked_over_5h_without_break is not True:
        return []

    return [
        Violation(
            rule_id="hours.rest_break",
            section_reference="§28(2)",
            severity=Severity.WARNING,
            plain_explanation_en=(
                "The law requires a 30-minute rest break after 5 continuous hours of work."
            ),
            plain_explanation_ne=(
                "कानुनले लगातार ५ घण्टा कामपछि ३० मिनेट आराम अनिवार्य गरेको छ।"
            ),
            suggested_action_en="Request your rest break; a denial is a violation you can report.",
            suggested_action_ne="आरामको ब्रेक माग गर्नुहोस्; अस्वीकार गर्नु उल्लङ्घन हो जुन तपाईंले रिपोर्ट गर्न सक्नुहुन्छ।",
        )
    ]


def check_overtime_cap(ctx: SubmissionCreate) -> list[Violation]:
    """§30(1): overtime above 24 hrs/week is unlawful even if fully paid."""
    if ctx.overtime_hours_per_week is None:
        return []

    if ctx.overtime_hours_per_week > 24:
        return [
            Violation(
                rule_id="hours.overtime_cap",
                section_reference="§30(1)",
                severity=Severity.CRITICAL,
                plain_explanation_en=(
                    f"You reported {ctx.overtime_hours_per_week:g} hours/week of overtime. The law caps "
                    "overtime at 24 hours/week — more is unlawful even if paid."
                ),
                plain_explanation_ne=(
                    f"तपाईंले हप्ताको {ctx.overtime_hours_per_week:g} घण्टा ओभरटाइम जनाउनुभयो। कानुनले "
                    "ओभरटाइमलाई हप्ताको २४ घण्टामा सीमित गरेको छ — त्यसभन्दा बढी तिरे पनि कानुनविपरीत हुन्छ।"
                ),
                suggested_action_en="Refuse excessive overtime and report to the Labour Office within 6 months.",
                suggested_action_ne="अत्यधिक ओभरटाइम अस्वीकार गर्नुहोस् र ६ महिनाभित्र श्रम कार्यालयमा रिपोर्ट गर्नुहोस्।",
            )
        ]

    return []


def check_overtime_pay(ctx: SubmissionCreate) -> list[Violation]:
    """§31(1): overtime must be paid at 1.5x basic remuneration."""
    if ctx.overtime_hours_per_week is None or ctx.overtime_hours_per_week <= 0:
        return []

    if ctx.overtime_rate_paid is None or ctx.overtime_rate_paid < OVERTIME_RATE:
        return [
            Violation(
                rule_id="hours.overtime_pay",
                section_reference="§31(1)",
                severity=Severity.WARNING,
                plain_explanation_en=(
                    "You worked overtime but were not paid at the required 1.5x rate."
                ),
                plain_explanation_ne=(
                    "तपाईंले ओभरटाइम गर्नुभयो तर कानुनले तोकेको १.५ गुणा दरमा भुक्तानी पाउनुभएन।"
                ),
                suggested_action_en="Claim the unpaid overtime difference; complain to the Labour Office if refused.",
                suggested_action_ne="नतिरिएको ओभरटाइम भिन्नता माग गर्नुहोस्; अस्वीकार भएमा श्रम कार्यालयमा उजुरी गर्नुहोस्।",
            )
        ]

    return []


ALL_RULES = [
    check_max_daily,
    check_max_weekly,
    check_rest_break,
    check_overtime_cap,
    check_overtime_pay,
]


def run(ctx: SubmissionCreate) -> list[Violation]:
    return [v for fn in ALL_RULES for v in fn(ctx)]
