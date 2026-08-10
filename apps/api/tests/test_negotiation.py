"""Tests for the negotiation-script stretch feature.

The parser tests are pure. The service tests mock both the vectorstore and the
Gemini call so they run offline and fast, matching the test_ai.py pattern.
"""

import json

import pytest
from langchain_core.documents import Document

from app.ai import negotiation
from app.ai.negotiation import NegotiationScript, _parse_script

VALID_SCRIPT = {
    "opening_en": "Thank you for your time today.",
    "opening_ne": "आजको समयका लागि धन्यवाद।",
    "points_en": ["Could we review my weekly hours?", "I would like the paid leave I asked for."],
    "points_ne": ["हामी मेरो साप्ताहिक घण्टा समीक्षा गर्न सक्छौं?", "मैले मागेको पैसासहितको बिदा चाहन्छु।"],
    "closing_en": "I appreciate your help with this.",
    "closing_ne": "यसमा सहयोग गर्नुभएकोमा धन्यवाद।",
}


def test_parse_script_accepts_valid_json():
    script = _parse_script(json.dumps(VALID_SCRIPT))
    assert isinstance(script, NegotiationScript)
    assert script.opening_en == VALID_SCRIPT["opening_en"]
    assert len(script.points_en) == 2
    assert script.closing_ne == VALID_SCRIPT["closing_ne"]


def test_parse_script_strips_markdown_fence():
    raw = f"```json\n{json.dumps(VALID_SCRIPT)}\n```"
    script = _parse_script(raw)
    assert script.opening_en == VALID_SCRIPT["opening_en"]


def test_parse_script_rejects_bad_json():
    with pytest.raises(ValueError):
        _parse_script("not json at all")


def test_parse_script_rejects_wrong_shape():
    with pytest.raises(ValueError):
        _parse_script(json.dumps({"points_en": "not a list"}))


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
                "deterministic_findings": [
                    {
                        "rule_id": "hours.excessive_weekly_hours",
                        "section_reference": "§28(1)",
                        "severity": "critical",
                        "plain_explanation_en": "Over the cap.",
                        "plain_explanation_ne": "सीमाभन्दा बढी।",
                        "suggested_action_en": "Ask to reduce hours.",
                        "suggested_action_ne": "घण्टा घटाउन भन्नुहोस्।",
                    }
                ],
            }
        ],
        "stats": {},
    }


def _fake_vectorstore(monkeypatch):
    def fake_get_vectorstore():
        return FakeVectorstore()
    monkeypatch.setattr(negotiation, "get_vectorstore", fake_get_vectorstore)


class FakeVectorstore:
    def similarity_search(self, query, k=5):
        return [
            Document(
                page_content=f"28. Fake section text about {query}.",
                metadata={"section": "28", "chapter": "X", "section_part": 1},
            )
            for _ in range(3)
        ]


def test_negotiate_document_returns_grouped_scripts(monkeypatch, sample_document):
    _fake_vectorstore(monkeypatch)

    def fake_generate(employer, existing_findings, deduped_sections, model=None):
        assert deduped_sections, "expected retrieved sections to be passed"
        assert existing_findings, "expected deterministic findings to be passed"
        return json.dumps(VALID_SCRIPT)

    monkeypatch.setattr(negotiation, "generate_negotiation_script", fake_generate)

    result = negotiation.negotiate_document(sample_document)
    assert result["warning"] is None
    assert len(result["scripts"]) == 1
    script = result["scripts"][0]
    assert script["employer_id"] == "e1"
    assert script["employer_name"] == "sudeep"
    assert script["points_en"] == VALID_SCRIPT["points_en"]


def test_negotiate_document_survives_gemini_failure(monkeypatch, sample_document):
    _fake_vectorstore(monkeypatch)

    def boom(employer, existing_findings, deduped_sections, model=None):
        raise RuntimeError("Gemini is down")

    monkeypatch.setattr(negotiation, "generate_negotiation_script", boom)

    result = negotiation.negotiate_document(sample_document)
    assert result["scripts"] == []
    assert result["warning"]


def test_negotiate_document_handles_no_employers():
    result = negotiation.negotiate_document({"employers": []})
    assert result["scripts"] == []
    assert result["warning"]
