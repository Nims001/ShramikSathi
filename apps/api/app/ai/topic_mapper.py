"""Determines which Labour Act topics are relevant for one employer's data.

Keeps retrieval focused — e.g. no point pulling "termination" sections for a
worker who was never terminated. Each topic maps to a query string used later
to search the Chroma vectorstore.
"""

from typing import List

from .schemas import Employer


TOPIC_QUERIES = {
    "working_hours": "daily and weekly working hours limits, rest breaks",
    "overtime": "overtime pay rate calculation and consent requirements",
    "wages": "minimum wage, wage payment timing and method, deductions",
    "leave": "weekly off days, public holidays, sick leave, maternity paternity leave",
    "social_security": "provident fund, gratuity, social security fund registration",
    "insurance": "medical insurance and accidental insurance requirements",
    "termination": "termination notice period and retrenchment compensation",
    "contract_and_documentation": "written contract requirements, document withholding, recruitment fees",
    "night_work": "night work conditions and allowance requirements",
}


def determine_relevant_topics(employer: Employer) -> List[str]:
    """Returns the list of topic keys relevant to this employer's data."""
    topics = set()

    # Always relevant — nearly every employment situation touches these
    topics.add("working_hours")
    topics.add("wages")

    if employer.overtime_rule or (
        employer.actual_weekly_hours and employer.contract_weekly_hours
        and employer.actual_weekly_hours > employer.contract_weekly_hours
    ):
        topics.add("overtime")

    if any([
        employer.weekly_off_day_guaranteed is False,
        employer.public_holiday_paid_leave is False,
        employer.sick_leave_denied,
        employer.maternity_leave_denied,
        employer.paternity_leave_denied,
        employer.mourning_leave_denied,
    ]):
        topics.add("leave")

    if any([
        employer.tenure_years and employer.tenure_years >= 1,
        employer.gratuity_deducted is False,
        employer.gratuity_paid_by_employer is False,
        employer.ssf_registered is False,
        employer.pf_deducted,
    ]):
        topics.add("social_security")

    if employer.medical_insurance_provided is False or employer.accidental_insurance_provided is False:
        topics.add("insurance")

    if employer.terminated:
        topics.add("termination")

    if any([
        employer.has_written_contract is False,
        employer.contract_states_wage is False,
        employer.contract_states_hours is False,
        employer.contract_states_leave is False,
        employer.contract_states_termination is False,
        employer.contract_explained_in_own_language is False,
        employer.employer_holds_documents,
        employer.paid_fee_to_get_job,
        employer.wage_withheld_before_start,
    ]):
        topics.add("contract_and_documentation")

    if employer.night_work:
        topics.add("night_work")

    # Free-text clauses are handled separately (each gets its own retrieval).

    return sorted(topics)
