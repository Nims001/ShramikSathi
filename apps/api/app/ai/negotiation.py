"""Generates a polite negotiation script for each employer.

This is the "negotiation script" stretch goal: given the worker's situation and
the retrieved Labour Act sections, Gemini drafts a short, polite script the
worker could use to raise issues with their employer. Output is validated
against a Pydantic schema, and every employer's script is clearly labelled as
an AI-generated suggestion, not legal advice.
"""

from typing import List

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User
from ..services.analysis import build_analysis_document
from .config import MAX_RETRIES, RETRY_BACKOFF_SECONDS
from .gemini_analysis import (
    AiNotConfiguredError,
    format_employer_data,
    format_existing_findings,
    format_free_text_clauses,
    format_retrieved_sections,
    get_gemini_model,
)
from .negotiation_prompt import NEGOTIATION_PROMPT_TEMPLATE
from .retrieval import build_retrieval_context
from .schemas import AnalyseRequest
from .vectorstore import get_vectorstore

import json
import time


class NegotiationScript(BaseModel):
    """Validated shape of one employer's generated script."""

    opening_en: str = ""
    opening_ne: str = ""
    points_en: List[str] = Field(default_factory=list)
    points_ne: List[str] = Field(default_factory=list)
    closing_en: str = ""
    closing_ne: str = ""


def generate_negotiation_script(employer, existing_findings: list, deduped_sections: list, model=None) -> str:
    """Calls Gemini for one employer's negotiation script; returns raw JSON text."""
    if model is None:
        model = get_gemini_model()

    prompt = NEGOTIATION_PROMPT_TEMPLATE.format(
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


def _parse_script(raw_text: str) -> NegotiationScript:
    """Parses Gemini's raw JSON into the validated script shape.

    Raises ValueError if the output cannot be parsed/validated, so a bad script
    never reaches the UI instead of a graceful warning.
    """
    text = raw_text.strip()
    if text.startswith("```"):
        # strip a possible markdown code fence around the JSON
        text = text.strip("`").strip()
        if text.startswith("json"):
            text = text[4:].strip()
    payload = json.loads(text)
    return NegotiationScript.model_validate(payload)


def negotiate_document(document: dict) -> dict:
    """Runs the negotiation-script step over an analysis document (dict).

    Returns {"scripts": [...], "warning": str|None}. Each script groups one
    employer's generated script: {"employer_id", "employer_name", **script}.
    """
    request = AnalyseRequest.model_validate(document)
    if not request.employers:
        return {"scripts": [], "warning": "No employer data provided."}

    vectorstore = get_vectorstore()
    scripts = []
    warning = None

    for employer_block in request.employers:
        employer = employer_block.employer
        existing_findings = employer_block.deterministic_findings or []
        try:
            context = build_retrieval_context(employer, vectorstore=vectorstore)
            raw_response = generate_negotiation_script(employer, existing_findings, context["deduped_sections"])
            script = _parse_script(raw_response)
            scripts.append(
                {
                    "employer_id": employer.id,
                    "employer_name": employer.employer_name or "Unnamed employer",
                    **script.model_dump(),
                }
            )
        except AiNotConfiguredError as e:
            raise e
        except Exception as e:  # noqa: BLE001 — one bad employer shouldn't kill the response
            warning = warning or (
                "One or more scripts could not be generated; the others are shown below."
            )

    return {"scripts": scripts, "warning": warning}


async def run_negotiation(db: AsyncSession, user: User) -> dict:
    """Builds the current user's analysis document and generates scripts."""
    document = await build_analysis_document(db, user)
    return negotiate_document(document)
