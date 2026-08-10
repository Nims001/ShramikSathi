"""Pydantic schema for a detected violation returned to the client."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ..models.violation import Severity


class ViolationOut(BaseModel):
    """One rule-engine finding, with bilingual explanations and actions."""

    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    section_reference: str
    severity: str  # info | warning | critical
    plain_explanation_en: str
    plain_explanation_ne: str
    suggested_action_en: str
    suggested_action_ne: str


class ViolationPersist(ViolationOut):
    """Used internally to store a violation row (adds the FK)."""

    submission_id: UUID
