"""OCR + text-to-fields parsing for contract photos.

The OCR step is *never* a violation determination — it only produces candidate
form fields that the user confirms before the rule engine runs. Using an LLM
here is allowed by the brief, but plain regex keeps this MVP dependency-light.
"""

import io
import re

from PIL import Image

# pytesseract is imported lazily so the app still boots on machines without it.
try:
    import pytesseract

    _HAS_TESSERACT = True
except Exception:  # pragma: no cover - depends on local install
    _HAS_TESSERACT = False


def _ocr_text(image_bytes: bytes) -> str:
    """Run tesseract OCR over the image and return raw text."""
    if not _HAS_TESSERACT:
        return ""
    image = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(image)


def _parse_number(text: str) -> float | None:
    """Extract the first number from a string (supports 1.5, 15,000 formats)."""
    match = re.search(r"(\d+(?:[.,]\d+)?)", text.replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


# Money keywords used with word boundaries so "rs" doesn't match inside "hours".
# The optional trailing dot is outside the boundary check to accept "Rs. 800".
_MONEY = r"\b(?:rs|npr|rup(?:ee|ees)?|salary|wage)\b\.?"


def extract_fields_from_image(image_bytes: bytes) -> dict:
    """OCR a contract photo into candidate form fields for user confirmation.

    Returns a dict of *candidate* values (plus the raw text). The UI must show
    these to the user for confirmation before they go to the rule engine.
    """
    raw_text = _ocr_text(image_bytes)
    low = raw_text.lower()
    one_line = " ".join(raw_text.split())  # OCR drops spaces; normalize whitespace
    low_line = one_line.lower()

    fields: dict = {"_raw_ocr_text": raw_text[:5000]}

    # Candidate monthly wage: "Rs. 25000 per month" or "monthly salary 25000".
    if "month" in low_line and ("salary" in low_line or "rs" in low_line or "npr" in low_line):
        m = re.search(rf"{_MONEY}\s*([\d,]+(?:\.\d+)?)\s*(?:per|a|/)?\s*month", one_line, re.I)
        if m:
            fields["monthly_wage"] = _parse_number(m.group(1))
        else:
            m = re.search(rf"\bmonth(?:ly)?\s*(?:salary|wage)?\s*[:.]?\s*([\d,]+(?:\.\d+)?)", one_line, re.I)
            if m:
                fields["monthly_wage"] = _parse_number(m.group(1))
        if "monthly_wage" not in fields:
            # Loose fallback for garbled OCR: any 4+ digit figure on the same
            # line as "month" (e.g. "Wonthlysalary. s 25000 ps month").
            m = re.search(rf"\b([\d,]+(?:\.\d+)?)\b[^\n]*?month", one_line, re.I)
            if m:
                fields["monthly_wage"] = _parse_number(m.group(1))

    # Candidate daily wage: "Rs. 800 per day".
    if "day" in low_line and ("rs" in low_line or "npr" in low_line or "wage" in low_line):
        m = re.search(rf"{_MONEY}\s*([\d,]+(?:\.\d+)?)\s*(?:per|a|/)?\s*day", one_line, re.I)
        if m:
            fields["daily_wage"] = _parse_number(m.group(1))

    # Candidate hours per day/week, allowing "X hours" or "hours X" order.
    for unit, key in (("day", "hours_per_day"), ("week", "hours_per_week")):
        m = re.search(
            rf"(?:(?:hours?|hrs?)\s*[:.]?\s*([\d]+)|([\d]+)\s*(?:hours?|hrs?))\s*"
            rf"(?:a|per|/)?\s*{unit}",
            low_line,
        )
        if m:
            fields[key] = float(m.group(1) or m.group(2))

    # Mention of leave → surface a flag for the user to check manually.
    if any(word in low_line for word in ["leave", "bida", "बिदा"]):
        fields["_mentions_leave"] = True

    # Mention of overtime and rate, e.g. "overtime 1.5x".
    m = re.search(r"\bovertime\b[^.\n]*?([\d.]+)\s*[x×]", low_line)
    if m:
        fields["overtime_rate_paid"] = float(m.group(1))

    return fields
