"""
Formats the worker's employment data, free-text clauses, existing
deterministic findings, and retrieved Labour Act sections into the
analysis prompt, then calls Gemini via LangChain to get back new
AI-generated findings.
"""

import json
import time

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from src.config import GEMINI_API_KEY, GEMINI_MODEL, MAX_RETRIES, RETRY_BACKOFF_SECONDS
from src.compliance.analysis_prompt import ANALYSIS_PROMPT_TEMPLATE
from src.intake.schema import Employer, DeterministicFinding


def format_employer_data(employer: Employer) -> str:
    """
    Converts the employer's structured fields into a readable text block
    for the prompt. Excludes null/None fields to keep the prompt focused
    on what's actually known, and excludes other_clauses (handled
    separately) to avoid duplicating it in the prompt.
    """
    data = employer.model_dump(exclude_none=True, exclude={"other_clauses"})
    lines = [f"- {key}: {value}" for key, value in data.items()]
    return "\n".join(lines)


def format_free_text_clauses(clauses: list) -> str:
    if not clauses:
        return "(none provided)"
    return "\n".join(f'- "{c}"' for c in clauses)


def format_existing_findings(findings: list) -> str:
    if not findings:
        return "(none)"
    lines = []
    for f in findings:
        rule_id = f.rule_id if isinstance(f, DeterministicFinding) else f.get("rule_id")
        section = f.section_reference if isinstance(f, DeterministicFinding) else f.get("section_reference")
        explanation = f.plain_explanation_en if isinstance(f, DeterministicFinding) else f.get("plain_explanation_en")
        lines.append(f"- [{rule_id}] {section}: {explanation}")
    return "\n".join(lines)


def format_retrieved_sections(deduped_sections: list) -> str:
    """
    deduped_sections is a list of LangChain Document objects from
    src/intake/retrieval.py's build_retrieval_context().
    """
    return "\n\n".join(
        f"Section {doc.metadata.get('section')} (Chapter {doc.metadata.get('chapter')}):\n{doc.page_content}"
        for doc in deduped_sections
    )


def get_gemini_model():
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
    )


def analyse_with_ai(employer: Employer, existing_findings: list, deduped_sections: list,
                     model=None) -> str:
    """
    Calls Gemini with the full assembled context and returns the raw
    text response (expected to be a JSON array string) — validate it
    with compliance_schema_validator before trusting it.
    """
    if model is None:
        model = get_gemini_model()

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        employer_data=format_employer_data(employer),
        free_text_clauses=format_free_text_clauses(employer.other_clauses),
        existing_findings=format_existing_findings(existing_findings),
        retrieved_sections=format_retrieved_sections(deduped_sections),
    )

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = model.invoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
            else:
                raise last_error


if __name__ == "__main__":
    from src.intake.schema import AnalyseRequest
    from src.intake.retrieval import build_retrieval_context

    with open("tests/sample_data/user.json", encoding="utf-8") as f:
        data = json.load(f)

    parsed = AnalyseRequest(**data)
    employer_block = parsed.employers[0]
    employer = employer_block.employer
    existing_findings = employer_block.deterministic_findings or []

    context = build_retrieval_context(employer)

    print(f"Calling Gemini with {len(context['deduped_sections'])} retrieved sections...")
    raw_response = analyse_with_ai(employer, existing_findings, context["deduped_sections"])

    print("\n--- Raw Gemini response ---")
    print(raw_response)