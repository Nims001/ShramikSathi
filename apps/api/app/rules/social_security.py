"""Social-security checks — The Labour Act, 2017, Ch. 10 (§52-55).

  §52: Provident Fund — employer deducts 10% of basic pay from the labour and
       adds a 10% employer match, depositing both to the Social Security Fund.
       Non-deposit: employer owes the labour the cash amount directly (§52(6)).
  §53: Gratuity — 8.33% of basic pay/month, funded entirely by the employer.
       Non-payment: employer owes the labour the cash amount (§53(6)).
  §54: Medical insurance — minimum NPR 100,000/year, premium split pro rata.
  §55: Accidental insurance — minimum NPR 700,000, fully employer-funded.
"""

from ..schemas.submission import SubmissionCreate
from .base import Severity, Violation


def check_pf_deposit(ctx: SubmissionCreate) -> list[Violation]:
    """§52: if PF is deducted from the worker but never deposited, the employer
    owes the equivalent cash amount directly (§52(6))."""
    if ctx.pf_deducted is not True:
        return []
    if ctx.pf_deposited is False:
        return [
            Violation(
                rule_id="social.pf_not_deposited",
                section_reference="§52, §52(6)",
                severity=Severity.CRITICAL,
                plain_explanation_en=(
                    "Provident Fund (10% of your basic pay) is being deducted from your wages but is not "
                    "being deposited to the Social Security Fund. The employer must pay you the equivalent "
                    "cash amount directly."
                ),
                plain_explanation_ne=(
                    "तपाईंको तलबबाट सञ्चय कोष (आधार तलबको १०%) काटिन्छ तर सामाजिक सुरक्षा कोषमा "
                    "जम्मा गरिँदैन। रोजगारदाताले तपाईंलाई सोही बराबरको रकम सिधै तिर्नुपर्छ।"
                ),
                suggested_action_en=(
                    "Ask for proof of deposit to the Social Security Fund. If not provided, complain to "
                    "the Labour Office within 6 months."
                ),
                suggested_action_ne=(
                    "सामाजिक सुरक्षा कोषमा जम्मा भएको प्रमाण माग गर्नुहोस्। नदिएमा ६ महिनाभित्र श्रम "
                    "कार्यालयमा उजुरी गर्नुहोस्।"
                ),
            )
        ]

    return []


def check_gratuity_payment(ctx: SubmissionCreate) -> list[Violation]:
    """§53: gratuity is employer-funded (8.33%/month). Not paying it at all after
    1+ years of service means the employer owes the cash amount (§53(6))."""
    if ctx.years_worked is None or ctx.years_worked < 1:
        return []
    # If gratuity is being deducted from pay, that's covered by wages.gratuity_deduction.
    if ctx.gratuity_deducted is True:
        return []
    if ctx.gratuity_paid_by_employer is False:
        return [
            Violation(
                rule_id="social.gratuity_not_paid",
                section_reference="§53, §53(6)",
                severity=Severity.WARNING,
                plain_explanation_en=(
                    "You have worked 1+ year(s) but your employer is not paying gratuity (8.33% of basic "
                    "pay/month, funded by the employer). The employer owes you the equivalent cash amount."
                ),
                plain_explanation_ne=(
                    "तपाईंले १ वर्षभन्दा बढी काम गर्नुभयो तर रोजगारदाताले उपदान तिरिरहेको छैन (आधार तलबको "
                    "८.३३%/महिना, रोजगारदाताको दायित्व)। रोजगारदाताले बराबरको नगद रकम तिर्नुपर्छ।"
                ),
                suggested_action_en="Claim gratuity; complain to the Labour Office if unpaid.",
                suggested_action_ne="उपदान माग गर्नुहोस्; नतिरेमा श्रम कार्यालयमा उजुरी गर्नुहोस्।",
            )
        ]

    return []


def check_medical_insurance(ctx: SubmissionCreate) -> list[Violation]:
    """§54: employer must provide medical insurance of at least NPR 100,000/year."""
    if ctx.medical_insurance_provided is False:
        return [
            Violation(
                rule_id="social.medical_insurance_missing",
                section_reference="§54",
                severity=Severity.WARNING,
                plain_explanation_en=(
                    "Your employer does not provide medical insurance. The law requires at least "
                    "NPR 100,000/year coverage."
                ),
                plain_explanation_ne=(
                    "तपाईंको रोजगारदाताले स्वास्थ्य बिमा उपलब्ध गराएको छैन। कानुनले कम्तीमा रु १,००,०००/वर्ष "
                    "को बिमा गराउनुपर्ने व्यवस्था गरेको छ।"
                ),
                suggested_action_en="Ask your employer to enroll you in health insurance.",
                suggested_action_ne="रोजगारदातासँग स्वास्थ्य बिमामा सहभागी गराउन माग गर्नुहोस्।",
            )
        ]

    return []


def check_accidental_insurance(ctx: SubmissionCreate) -> list[Violation]:
    """§55: employer must provide accidental insurance of at least NPR 700,000,
    fully paid by the employer."""
    if ctx.accidental_insurance_provided is False:
        return [
            Violation(
                rule_id="social.accidental_insurance_missing",
                section_reference="§55",
                severity=Severity.WARNING,
                plain_explanation_en=(
                    "Your employer does not provide accidental insurance. The law requires at least "
                    "NPR 700,000 coverage, fully paid by the employer."
                ),
                plain_explanation_ne=(
                    "तपाईंको रोजगारदाताले दुर्घटना बिमा उपलब्ध गराएको छैन। कानुनले कम्तीमा रु ७,००,००० "
                    "बिमा रोजगारदाताको पूरा खर्चमा गराउनुपर्ने व्यवस्था गरेको छ।"
                ),
                suggested_action_en="Ask your employer to provide accidental insurance.",
                suggested_action_ne="रोजगारदातासँग दुर्घटना बिमा गराउन माग गर्नुहोस्।",
            )
        ]

    return []


ALL_RULES = [
    check_pf_deposit,
    check_gratuity_payment,
    check_medical_insurance,
    check_accidental_insurance,
]


def run(ctx: SubmissionCreate) -> list[Violation]:
    return [v for fn in ALL_RULES for v in fn(ctx)]
