"""
Quick end-to-end test: retrieval -> Gemini call -> validation, all in one run.
"""

import json
from src.intake.schema import AnalyseRequest
from src.intake.retrieval import build_retrieval_context
from src.compliance.gemini_analysis import analyse_with_ai
from src.compliance.analysis_schema_validator import parse_and_validate

with open("tests/sample_data/user.json", encoding="utf-8") as f:
    data = json.load(f)

parsed = AnalyseRequest(**data)
employer_block = parsed.employers[0]
employer = employer_block.employer
existing_findings = employer_block.deterministic_findings or []

context = build_retrieval_context(employer)
retrieved_numbers = [doc.metadata.get("section") for doc in context["deduped_sections"]]

print(f"Calling Gemini with {len(context['deduped_sections'])} retrieved sections...")
raw_response = analyse_with_ai(employer, existing_findings, context["deduped_sections"])

print("\n--- Raw Gemini response ---")
print(raw_response)

print("\n--- Validation ---")
parsed_findings, is_valid, errors = parse_and_validate(raw_response, retrieved_numbers)
print("Valid:", is_valid)
if errors:
    for e in errors:
        print(" -", e)
else:
    print(f"{len(parsed_findings)} findings validated successfully.")
    for f in parsed_findings:
        print(f"  [{f['severity']}] {f['rule_id']} -> {f['section_reference']}")