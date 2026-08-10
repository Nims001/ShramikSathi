"""Leave checks — The Labour Act, 2017, Ch. 9 (§40-51).

Important distinction from §51: sick leave, maternity leave, and mourning leave
are *rights* that cannot be refused; most other leave is a "facility" the
employer can withhold with a stated reason. Denials of rights are flagged here.
"""

from ..schemas.submission import SubmissionCreate
from .base import Severity, Violation


def check_weekly_leave(ctx: SubmissionCreate) -> list[Violation]:
    """§40: at least 1 day of weekly leave per week."""
    if ctx.weekly_leave_taken_per_month is None:
        return []

    if ctx.weekly_leave_taken_per_month < 1:
        return [
            Violation(
                rule_id="leave.weekly_leave",
                section_reference="§40",
                severity=Severity.WARNING,
                plain_explanation_en=(
                    f"You get {ctx.weekly_leave_taken_per_month:g} day(s) of leave per week. "
                    "The law guarantees at least 1 day/week."
                ),
                plain_explanation_ne=(
                    f"तपाईंले हप्तामा {ctx.weekly_leave_taken_per_month:g} दिन बिदा पाउनुहुन्छ। "
                    "कानुनले हप्तामा कम्तीमा १ दिनको सुनिश्चित गरेको छ।"
                ),
                suggested_action_en="Ask for your weekly leave day; refusal can be reported.",
                suggested_action_ne="आफ्नो साप्ताहिक बिदा माग गर्नुहोस्; अस्वीकार रिपोर्ट गर्न सकिन्छ।",
            )
        ]

    return []


def _denied_right_violation(
    rule_id: str,
    section: str,
    leave_name_en: str,
    leave_name_ne: str,
    details_en: str,
    details_ne: str,
) -> Violation:
    """§51: sick/maternity/mourning leave are rights and cannot be refused —
    build the violation message once, reuse for each leave type."""
    return Violation(
        rule_id=rule_id,
        section_reference=section,
        severity=Severity.WARNING,
        plain_explanation_en=(
            f"{leave_name_en} was denied. {details_en} This is a legal right that the employer "
            "cannot refuse."
        ),
        plain_explanation_ne=(
            f"{leave_name_ne} अस्वीकार गरियो। {details_ne} यो कानुनी हक हो जुन रोजगारदाताले अस्वीकार "
            "गर्न सक्दैन।"
        ),
        suggested_action_en=(
            "Submit a written request first (§113), then complain to the Labour Office within 6 months "
            "if refused."
        ),
        suggested_action_ne=(
            "पहिले लिखित निवेदन दिनुहोस् (§113), अस्वीकार भएमा ६ महिनाभित्र श्रम कार्यालयमा उजुरी गर्नुहोस्।"
        ),
    )


def check_sick_leave_denied(ctx: SubmissionCreate) -> list[Violation]:
    """§44: 12 days/year sick leave, a right (certificate needed only if >3 days)."""
    if ctx.sick_leave_denied is not True:
        return []
    return [
        _denied_right_violation(
            "leave.sick_leave",
            "§44",
            "Sick leave",
            "बिरामी बिदा",
            "You are entitled to 12 days/year of sick leave.",
            "तपाईं वर्षको १२ दिन बिरामी बिदा पाउन हकदार हुनुहुन्छ।",
        )
    ]


def check_maternity_leave_denied(ctx: SubmissionCreate) -> list[Violation]:
    """§45: 14 weeks maternity leave, a right; full pay for 60 days."""
    if ctx.maternity_leave_denied is not True:
        return []
    return [
        _denied_right_violation(
            "leave.maternity_leave",
            "§45",
            "Maternity leave",
            "प्रसूति बिदा",
            "You are entitled to 14 weeks of maternity leave, with full pay for 60 days.",
            "तपाईं १४ हप्ता प्रसूति बिदा पाउन हकदार हुनुहुन्छ, ६० दिन पूरा तलब सहित।",
        )
    ]


def check_paternity_leave_denied(ctx: SubmissionCreate) -> list[Violation]:
    """§45(7): 15 days paid paternity leave for a male worker when the wife delivers."""
    if ctx.paternity_leave_denied is not True:
        return []
    return [
        _denied_right_violation(
            "leave.paternity_leave",
            "§45(7)",
            "Paternity leave",
            "पितृत्व बिदा",
            "You are entitled to 15 days of paid paternity leave.",
            "तपाईं १५ दिन तलबी पितृत्व बिदा पाउन हकदार हुनुहुन्छ।",
        )
    ]


def check_mourning_leave_denied(ctx: SubmissionCreate) -> list[Violation]:
    """§48: 13 days mourning leave with full pay, a right."""
    if ctx.mourning_leave_denied is not True:
        return []
    return [
        _denied_right_violation(
            "leave.mourning_leave",
            "§48",
            "Mourning leave",
            "शोक बिदा",
            "You are entitled to 13 days of mourning leave with full pay.",
            "तपाईं १३ दिन पूरा तलब सहित शोक बिदा पाउन हकदार हुनुहुन्छ।",
        )
    ]


ALL_RULES = [
    check_weekly_leave,
    check_sick_leave_denied,
    check_maternity_leave_denied,
    check_paternity_leave_denied,
    check_mourning_leave_denied,
]


def run(ctx: SubmissionCreate) -> list[Violation]:
    return [v for fn in ALL_RULES for v in fn(ctx)]
