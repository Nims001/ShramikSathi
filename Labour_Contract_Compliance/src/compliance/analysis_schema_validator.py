"""
JSON Schema validator for the "Analyse with AI" Gemini output — a list
of new findings, meant to be combined with the existing
deterministic_findings for the frontend report.
"""

import json
from jsonschema import Draft202012Validator


FINDING_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "rule_id", "section_reference", "severity",
        "plain_explanation_en", "suggested_action_en",
    ],
    "properties": {
        "rule_id": {"type": "string", "minLength": 1},
        "section_reference": {"type": "string", "minLength": 1},
        "severity": {"type": "string", "enum": ["info", "warning", "critical"]},
        "plain_explanation_en": {"type": "string", "minLength": 1},
        "suggested_action_en": {"type": "string", "minLength": 1},
    },
}

FINDINGS_LIST_SCHEMA = {
    "type": "array",
    "items": FINDING_SCHEMA,
}


def validate_ai_findings(data, retrieved_section_numbers=None):
    """
    Validates the parsed list of AI findings.

    Args:
        data: the parsed JSON (expected to be a list of finding dicts)
        retrieved_section_numbers: optional list of section numbers that
            were actually retrieved, for hallucination checking

    Returns:
        (is_valid: bool, errors: list[str])
    """
    validator = Draft202012Validator(FINDINGS_LIST_SCHEMA)
    errors = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = " -> ".join(str(p) for p in err.path) or "(root)"
        errors.append(f"[{path}] {err.message}")

    if errors:
        return False, errors

    if retrieved_section_numbers is not None:
        errors.extend(_check_citation_hallucination(data, retrieved_section_numbers))

    if any(f["rule_id"].startswith("ai_generated.") is False for f in data):
        errors.append(
            "One or more findings have a rule_id not prefixed with 'ai_generated.' "
            "— expected all AI findings to use this prefix to distinguish them "
            "from deterministic findings."
        )

    return len(errors) == 0, errors


def _check_citation_hallucination(findings, retrieved_section_numbers):
    """
    section_reference can contain multiple sections, e.g. '§28(1), §29(1), §30(1)'.
    Extracts the bare numbers and checks each against what was retrieved.
    """
    import re
    retrieved_set = {str(s) for s in retrieved_section_numbers}
    issues = []

    for finding in findings:
        cited_numbers = re.findall(r'§(\d+)', finding["section_reference"])
        hallucinated = [n for n in cited_numbers if n not in retrieved_set]
        if hallucinated:
            issues.append(
                f"Finding '{finding['rule_id']}' cites section(s) {hallucinated} "
                f"that were not among the retrieved sections."
            )

    return issues


def parse_and_validate(raw_text, retrieved_section_numbers=None):
    """
    Strips markdown code fences if present (Gemini sometimes wraps JSON
    in ```json ... ``` despite instructions not to), parses, and validates.
    """
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return None, False, [f"JSON parse error: {e}"]

    is_valid, errors = validate_ai_findings(data, retrieved_section_numbers)
    return data, is_valid, errors


if __name__ == "__main__":
    example_raw = '''```json
[
  {
    "rule_id": "ai_generated.excessive_working_hours",
    "section_reference": "§28(1), §29(1)",
    "severity": "critical",
    "plain_explanation_en": "Test explanation.",
    "suggested_action_en": "Test action."
  }
]
```'''

    retrieved = ["28", "29", "30", "31", "41", "52"]
    data, is_valid, errors = parse_and_validate(example_raw, retrieved)
    print("Valid:", is_valid)
    print("Parsed:", data)
    if errors:
        for e in errors:
            print(" -", e)
