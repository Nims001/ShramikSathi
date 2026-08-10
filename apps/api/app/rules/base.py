"""Shared types for the deterministic rule engine.

Every check function receives the form data and returns a list of `Violation`
objects. Nothing here uses an LLM — determinations are pure, testable code.
"""

from pydantic import BaseModel


class Severity:
    """How urgently the worker should act. Not legal weight — just UX triage."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Violation(BaseModel):
    """One rule-engine finding, fully bilingual.

    `section_reference` is the Act citation shown to the user (e.g. "§28(1)").
    """

    rule_id: str
    section_reference: str
    severity: str
    plain_explanation_en: str
    plain_explanation_ne: str
    suggested_action_en: str
    suggested_action_ne: str
