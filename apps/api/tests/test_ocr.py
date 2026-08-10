"""Tests for the OCR field-extraction parser.

tesseract is not required to run these — we monkeypatch the raw-text step and
exercise the regex parsing directly. The extraction only produces *candidate*
fields for user confirmation; it never determines violations.
"""

import pytest

from app.ocr.extract import extract_fields_from_image


@pytest.fixture
def fake_tesseract(monkeypatch):
    """Force the parser to use a canned OCR text result."""
    def _fake(ocr_text: str):
        monkeypatch.setattr("app.ocr.extract._ocr_text", lambda image_bytes: ocr_text)
        return extract_fields_from_image(b"fake-image-bytes")
    return _fake


def test_monthly_wage_and_hours(fake_tesseract):
    text = "Employment Contract\nMonthly salary Rs. 25000 per month\nWorking hours 9 hours a day, 50 hours a week\n"
    fields = fake_tesseract(text)
    assert fields["monthly_wage"] == 25000
    assert fields["hours_per_day"] == 9
    assert fields["hours_per_week"] == 50


def test_monthly_wage_does_not_match_rs_inside_hours(fake_tesseract):
    # Regression: "rs" inside "hours" must not be treated as a currency marker.
    text = "Hours are long. 25000 per month salary."
    fields = fake_tesseract(text)
    assert fields.get("monthly_wage") == 25000


def test_daily_wage(fake_tesseract):
    text = "Daily wage: Rs. 800 per day"
    fields = fake_tesseract(text)
    assert fields["daily_wage"] == 800


def test_leave_mention_sets_flag(fake_tesseract):
    text = "Employee is entitled to 12 days of leave."
    fields = fake_tesseract(text)
    assert fields["_mentions_leave"] is True


def test_overtime_rate(fake_tesseract):
    text = "Overtime is paid at 1.5x the normal rate."
    fields = fake_tesseract(text)
    assert fields["overtime_rate_paid"] == 1.5


def test_garbage_text_returns_empty(fake_tesseract):
    fields = fake_tesseract("lorem ipsum dolor sit amet")
    assert fields == {"_raw_ocr_text": "lorem ipsum dolor sit amet"}
