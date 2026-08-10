"""Tests for the "Analyse with AI" RAG pipeline.

The validator tests are pure (no model/downloads). The service test mocks both
the vectorstore and the Gemini call so it runs offline and fast.
"""

import json

import pytest
from langchain_core.documents import Document

from app.ai.analysis_schema_validator import parse_and_validate
from app.ai.schemas import AnalyseRequest
from app.ai import service

VALID_RAW = """[
  {
    "rule_id": "ai_generated.excessive_working_hours",
    "section_reference": "§28(1), §29(1)",
    "severity": "critical",
    "plain_explanation_en": "You are contracted to 90 hours/week, above the 48-hour cap.",
    "plain_explanation_ne": "तपाईं हप्तामा ९० घण्टा काम गर्ने सम्झौता गरिएको छ।",
    "suggested_action_en": "Ask your employer to reduce your hours.",
    "suggested_action_ne": "रोजगारदातालाई घण्टा घटाउन भन्नुहोस्।"
  }
]"""


def test_validator_accepts_bilingual_findings():
    data, is_valid, errors = parse_and_validate(VALID_RAW, retrieved_section_numbers=["28", "29"])
    assert is_valid is True
    assert errors == []
    assert data[0]["section_reference"] == "§28(1), §29(1)"
    assert data[0]["plain_explanation_ne"]


def test_validator_rejects_hallucinated_sections():
    data, is_valid, errors = parse_and_validate(VALID_RAW, retrieved_section_numbers=["28"])
    assert is_valid is False
    assert any("not among the retrieved sections" in e for e in errors)


def test_validator_rejects_bad_severity():
    raw = VALID_RAW.replace('"critical"', '"fatal"')
    _, is_valid, errors = parse_and_validate(raw, retrieved_section_numbers=["28", "29"])
    assert is_valid is False
    assert any("severity" in e for e in errors)


def test_validator_rejects_wrong_rule_id_prefix():
    raw = VALID_RAW.replace("ai_generated.excessive_working_hours", "hours.excessive_working_hours")
    _, is_valid, errors = parse_and_validate(raw, retrieved_section_numbers=["28", "29"])
    assert is_valid is False
    assert any("ai_generated." in e for e in errors)


def test_validator_strips_markdown_fences():
    raw = f"```json\n{VALID_RAW}\n```"
    data, is_valid, errors = parse_and_validate(raw, retrieved_section_numbers=["28", "29"])
    assert is_valid is True
    assert len(data) == 1


def test_validator_accepts_empty_array():
    data, is_valid, errors = parse_and_validate("[]", retrieved_section_numbers=["28"])
    assert is_valid is True
    assert data == []


def test_schema_parses_current_analysis_document():
    """The app's GET /api/analysis output must parse into the AI request schema."""
    doc = {
        "meta": {
            "generated_at": "2026-08-07T20:21:13.857343+00:00",
            "law_framework": "The Labour Act, 2017 (Nepal)",
            "analysis_mode": "flag anything",
        },
        "user": {"id": "u1", "age": None, "gender": "male", "language": "en"},
        "employers": [
            {
                "employer": {
                    "id": "e1",
                    "employer_name": "sudeep",
                    "industry": "it",
                    "employment_type": "regular",
                    "actual_weekly_hours": 48,
                    "contract_weekly_hours": 48,
                    "weekly_leave_days_per_week": 1,
                    "other_clauses": ["i should work 90 hours per week"],
                },
                "weekly_setting": None,
                "logs": [],
                "deterministic_findings": [
                    {
                        "rule_id": "hours.rest_break",
                        "section_reference": "§28(2)",
                        "severity": "warning",
                        "plain_explanation_en": "The law requires a rest break.",
                        "plain_explanation_ne": "कानुनले विश्राम अनिवार्य गरेको छ।",
                        "suggested_action_en": "Request it.",
                        "suggested_action_ne": "माग गर्नुहोस्।",
                    }
                ],
            }
        ],
        "stats": {},
    }
    request = AnalyseRequest.model_validate(doc)
    assert len(request.employers) == 1
    assert request.employers[0].employer.other_clauses == ["i should work 90 hours per week"]
    assert request.employers[0].deterministic_findings[0].rule_id == "hours.rest_break"


def _fake_vectorstore(monkeypatch):
    """Stub the Chroma store with canned documents so tests stay offline."""
    def fake_get_vectorstore():
        return FakeVectorstore()
    monkeypatch.setattr(service, "get_vectorstore", fake_get_vectorstore)


class FakeVectorstore:
    def similarity_search(self, query, k=5):
        number = "28" if "hour" in query or "leave" in query else "30"
        return [
            Document(
                page_content=f"{number}. Fake section text about {query}.",
                metadata={"section": number, "chapter": "X", "section_part": 1},
            )
            for _ in range(3)
        ]


@pytest.fixture
def sample_document():
    return {
        "meta": {"generated_at": "2026-08-07T20:21:13+00:00"},
        "user": {"id": "u1", "age": 26, "language": "en"},
        "employers": [
            {
                "employer": {
                    "id": "e1",
                    "employer_name": "sudeep",
                    "other_clauses": ["i should work 90 hours per week"],
                },
                "deterministic_findings": [],
            }
        ],
        "stats": {},
    }


def test_service_returns_grouped_ai_findings(monkeypatch, sample_document):
    _fake_vectorstore(monkeypatch)

    def fake_analyse(employer, existing_findings, deduped_sections, model=None):
        assert deduped_sections, "expected retrieved sections to be passed"
        return json.dumps(
            [
                {
                    "rule_id": "ai_generated.excessive_weekly_hours",
                    "section_reference": "§28(1)",
                    "severity": "critical",
                    "plain_explanation_en": "Over the legal cap.",
                    "suggested_action_en": "Ask to reduce hours.",
                }
            ]
        )

    monkeypatch.setattr(service, "analyse_with_ai", fake_analyse)

    result = service.analyse_document(sample_document)
    assert result["warning"] is None
    assert len(result["ai_findings"]) == 1
    group = result["ai_findings"][0]
    assert group["employer_id"] == "e1"
    assert group["employer_name"] == "sudeep"
    assert group["findings"][0]["rule_id"].startswith("ai_generated.")


def test_service_survives_gemini_failure(monkeypatch, sample_document):
    _fake_vectorstore(monkeypatch)

    def boom(employer, existing_findings, deduped_sections, model=None):
        raise RuntimeError("Gemini is down")

    monkeypatch.setattr(service, "analyse_with_ai", boom)

    result = service.analyse_document(sample_document)
    assert result["ai_findings"] == []
    assert result["warning"]  # a warning is surfaced, the request doesn't fail
    assert result["validation_errors"]


def test_service_handles_no_employers():
    result = service.analyse_document({"employers": []})
    assert result["ai_findings"] == []
    assert result["warning"]
