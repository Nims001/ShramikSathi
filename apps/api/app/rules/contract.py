"""Contract-related checks.

  §163 penalty table: failing to give a written appointment letter/contract can
  be fined up to NPR 500,000 (NPR 10,000 per labour).
"""

from ..schemas.submission import SubmissionCreate
from .base import Severity, Violation


def check_written_contract(ctx: SubmissionCreate) -> list[Violation]:
    """§163: a written contract/appointment letter is required."""
    if ctx.has_written_contract is False:
        return [
            Violation(
                rule_id="contract.no_written_contract",
                section_reference="§163",
                severity=Severity.WARNING,
                plain_explanation_en=(
                    "You have no written contract or appointment letter. Employers can be fined up to "
                    "NPR 500,000 for this."
                ),
                plain_explanation_ne=(
                    "तपाईंसँग लिखित सम्झौता वा नियुक्ति पत्र छैन। यसका लागि रोजगारदातालाई रु ५,००,००० "
                    "सम्म जरिवाना हुन सक्छ।"
                ),
                suggested_action_en=(
                    "Ask for a written appointment letter stating your wage, hours, and leave — and keep a copy."
                ),
                suggested_action_ne=(
                    "ज्याला, कामका घण्टा र बिदा उल्लेख गरेको लिखित नियुक्ति पत्र माग गर्नुहोस् — र एउटा प्रति "
                    "राख्नुहोस्।"
                ),
            )
        ]

    return []


ALL_RULES = [check_written_contract]


def run(ctx: SubmissionCreate) -> list[Violation]:
    return [v for fn in ALL_RULES for v in fn(ctx)]
