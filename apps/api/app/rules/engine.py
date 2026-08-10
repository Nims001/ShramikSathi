"""Rule engine — runs every deterministic rule module and aggregates results.

This is the only place violation *determinations* are made. No LLM is ever
consulted here; the LLM is only for explaining results and generating scripts.
"""

from ..schemas.submission import SubmissionCreate
from .base import Severity, Violation
from .contract import check_written_contract
from .hours import (
    check_max_daily,
    check_max_weekly,
    check_overtime_cap,
    check_overtime_pay,
    check_rest_break,
)
from .leave import (
    check_maternity_leave_denied,
    check_mourning_leave_denied,
    check_paternity_leave_denied,
    check_sick_leave_denied,
    check_weekly_leave,
)
from .social_security import (
    check_accidental_insurance,
    check_gratuity_payment,
    check_medical_insurance,
    check_pf_deposit,
)
from .termination import (
    check_final_settlement,
    check_notice_period,
    check_retrenchment_compensation,
)
from .wages import (
    check_annual_increment,
    check_festival_expense,
    check_gratuity_deduction,
    check_minimum_wage,
    check_other_deductions,
    check_payment_interval,
)

# Every check function in one flat list — easy to audit, easy to test.
ALL_CHECKS = [
    # Hours (§28-31)
    check_max_daily,
    check_max_weekly,
    check_rest_break,
    check_overtime_cap,
    check_overtime_pay,
    # Wages (§35-38, §106-107)
    check_minimum_wage,
    check_payment_interval,
    check_gratuity_deduction,
    check_other_deductions,
    check_annual_increment,
    check_festival_expense,
    # Leave (§40-51)
    check_weekly_leave,
    check_sick_leave_denied,
    check_maternity_leave_denied,
    check_paternity_leave_denied,
    check_mourning_leave_denied,
    # Social security (§52-55)
    check_pf_deposit,
    check_gratuity_payment,
    check_medical_insurance,
    check_accidental_insurance,
    # Contract
    check_written_contract,
    # Termination (§144-148)
    check_notice_period,
    check_retrenchment_compensation,
    check_final_settlement,
]


def act_prevails_note() -> Violation:
    """§3(2): any contract term below what the Act guarantees is automatically
    void. Surfaced whenever violations are found — "even if your contract says
    otherwise, the law wins"."""
    return Violation(
        rule_id="general.act_prevails",
        section_reference="§3(2)",
        severity=Severity.INFO,
        plain_explanation_en=(
            "Even if your contract says something less than the Act guarantees, that term is void — "
            "the law wins. Anything your employer deducted or denied under such a term must be corrected."
        ),
        plain_explanation_ne=(
            "तपाईंको सम्झौतामा कानुनले दिएको भन्दा कम अधिकार लेखिएको भए पनि त्यो शर्त अमान्य हुन्छ — "
            "कानुन नै लागू हुन्छ। यस्तो शर्तका आधारमा रोजगारदाताले काटेको वा अस्वीकार गरेको सबै सच्याउनुपर्छ।"
        ),
        suggested_action_en="Reference §3(2) in any written demand you make to your employer.",
        suggested_action_ne="रोजगारदातासँगको कुनै पनि लिखित मागमा §3(2) को सन्दर्भ दिनुहोस्।",
    )


def run_rules(ctx: SubmissionCreate) -> list[Violation]:
    """Run all checks for one submission and return the ordered findings.

    If anything was flagged, append the §3(2) reminder as an info item so the
    worker knows their contract cannot override the law.
    """
    violations: list[Violation] = []
    for check in ALL_CHECKS:
        violations.extend(check(ctx))

    if violations:
        violations.append(act_prevails_note())

    return violations
