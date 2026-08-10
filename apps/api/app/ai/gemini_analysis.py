"""Formats the worker's data and calls Gemini via LangChain.

The raw text response is expected to be a JSON array string — validate it with
analysis_schema_validator before trusting it.
"""

import json
import time

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from .config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    MAX_RETRIES,
    RETRY_BACKOFF_SECONDS,
)
from .analysis_prompt import ANALYSIS_PROMPT_TEMPLATE
from .schemas import Employer


class AiNotConfiguredError(RuntimeError):
    """Raised when Gemini cannot be used (missing API key / dependency)."""


def format_employer_data(employer: Employer) -> str:
    """Structured fields as a readable text block, excluding nulls and other_clauses."""
    data = employer.model_dump(exclude_none=True, exclude={"other_clauses"})
    lines = [f"- {key}: {value}" for key, value in data.items()]
    return "\n".join(lines)


def format_free_text_clauses(clauses) -> str:
    if not clauses:
        return "(none provided)"
    return "\n".join(f'- "{c}"' for c in clauses)


def format_existing_findings(findings) -> str:
    if not findings:
        return "(none)"
    lines = []
    for f in findings:
        rule_id = getattr(f, "rule_id", None) or (f.get("rule_id") if isinstance(f, dict) else None)
        section = getattr(f, "section_reference", None) or (f.get("section_reference") if isinstance(f, dict) else None)
        explanation = getattr(f, "plain_explanation_en", None) or (f.get("plain_explanation_en") if isinstance(f, dict) else None)
        lines.append(f"- [{rule_id}] {section}: {explanation}")
    return "\n".join(lines)


def format_retrieved_sections(deduped_sections) -> str:
    """deduped_sections is a list of LangChain Documents from retrieval.py."""
    return "\n\n".join(
        f"Section {doc.metadata.get('section')} (Chapter {doc.metadata.get('chapter')}):\n{doc.page_content}"
        for doc in deduped_sections
    )


def get_gemini_model():
    if not GEMINI_API_KEY:
        raise AiNotConfiguredError(
            "GEMINI_API_KEY is not set. The AI analysis is disabled; "
            "deterministic findings are still shown."
        )
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
    )


def analyse_with_ai(employer: Employer, existing_findings: list, deduped_sections: list, model=None) -> str:
    """Calls Gemini with the full assembled context and returns the raw text."""
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
    import json
    from pathlib import Path

    from .schemas import AnalyseRequest
    from .retrieval import build_retrieval_context

    sample = Path(__file__).resolve().parents[3] / ".." / "Labour_Contract_Compliance" / "tests" / "sample_data" / "user.json"
    with open(sample, encoding="utf-8") as f:
        parsed = AnalyseRequest.model_validate(json.load(f))

    employer_block = parsed.employers[0]
    context = build_retrieval_context(employer_block.employer, vectorstore=None)
    raw_response = analyse_with_ai(employer_block.employer, employer_block.deterministic_findings or [], context["deduped_sections"])
    print(raw_response)
