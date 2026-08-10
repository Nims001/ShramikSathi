"""Orchestrates the "Analyse with AI" flow.

The current app's analysis document (`GET /api/analysis`) is already shaped like
the reference pipeline's AnalyseRequest, so we parse it straight into the AI
schemas, run retrieval + Gemini per employer, validate the output, and return a
response the frontend can render grouped by employer.
"""

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User
from ..services.analysis import build_analysis_document
from .analysis_schema_validator import parse_and_validate
from .gemini_analysis import AiNotConfiguredError, analyse_with_ai
from .retrieval import build_retrieval_context
from .schemas import AnalyseRequest
from .vectorstore import get_vectorstore


def analyse_document(document: dict) -> dict:
    """Runs the RAG pipeline over an analysis document (dict).

    Returns {"ai_findings": [...], "warning": str|None, "validation_errors": [...]}.
    Each item in ai_findings groups one employer's new AI findings:
      {"employer_id", "employer_name", "findings": [ ... ]}
    """
    request = AnalyseRequest.model_validate(document)
    if not request.employers:
        return {"ai_findings": [], "warning": "No employer data provided.", "validation_errors": []}

    vectorstore = get_vectorstore()
    ai_findings = []
    warning = None
    validation_errors: List[str] = []

    for employer_block in request.employers:
        employer = employer_block.employer
        existing_findings = employer_block.deterministic_findings or []
        try:
            context = build_retrieval_context(employer, vectorstore=vectorstore)
            retrieved_numbers = [doc.metadata.get("section") for doc in context["deduped_sections"]]

            raw_response = analyse_with_ai(employer, existing_findings, context["deduped_sections"])
            findings, is_valid, errors = parse_and_validate(raw_response, retrieved_numbers)

            if not is_valid:
                validation_errors.extend(errors or ["AI output failed validation."])
                warning = (
                    "AI analysis could not be validated for one or more employers; "
                    "showing deterministic findings only."
                )
                continue

            ai_findings.append(
                {
                    "employer_id": employer.id,
                    "employer_name": employer.employer_name or "Unnamed employer",
                    "findings": findings,
                }
            )
        except AiNotConfiguredError as e:
            raise e
        except Exception as e:  # noqa: BLE001 — one employer failing shouldn't kill the whole response
            validation_errors.append(f"{employer.employer_name or employer.id}: {e}")
            warning = (
                "The AI analysis could not be completed for one or more employers; "
                "deterministic findings are still shown below."
            )

    return {
        "ai_findings": ai_findings,
        "warning": warning,
        "validation_errors": validation_errors,
    }


async def run_ai_analysis(db: AsyncSession, user: User) -> dict:
    """Builds the current user's analysis document and runs the AI pipeline."""
    document = await build_analysis_document(db, user)
    return analyse_document(document)
