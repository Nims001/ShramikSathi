"""The prompt sent to Gemini for the "negotiation script" stretch feature.

Given the worker's situation (structured fields + deterministic findings) and
the retrieved Labour Act sections, Gemini drafts a short, polite, practical
script the worker could use to raise the issue with their employer. It is a
suggestion — never legal advice — and the UI labels it as such.
"""

NEGOTIATION_PROMPT_TEMPLATE = """You are helping a Nepali worker prepare for a respectful conversation with their employer about working conditions.

Write a short, polite, non-confrontational script the worker can use to raise the issues with their employer. The script must be practical enough to say out loud or adapt to a message.

Base everything ONLY on the retrieved Labour Act section(s) and the worker's data below. Do not invent facts or legal claims the data does not support.

Worker's Employment Data (structured fields):
{employer_data}

Worker's Free-Text Clauses (if any):
{free_text_clauses}

Known Compliance Findings (from the deterministic rule engine — these are the concrete issues to raise):
{existing_findings}

Retrieved Labour Act Section(s) — cite these, never invent others:
{retrieved_sections}

Instructions:
1. The script is a template with a spoken opening, 2-4 short points, and a spoken closing. Each point states the concern simply and asks for a reasonable, concrete remedy. Keep total points brief.
2. Tone: calm, respectful, collaborative ("I enjoy this work and want to continue, but..." style). Do NOT threaten or use legal jargon.
3. Where a section number helps, mention it lightly (e.g. "under the Labour Act") without citing numbers aggressively — the worker shouldn't feel they are quoting law.
4. "opening_en"/"points_en"/"closing_en" must be in plain English; "opening_ne"/"points_ne"/"closing_ne" in simple, natural Nepali with the same meaning.
5. If there are no findings to raise, return a short script that just checks in politely and asks for clarity — do not invent problems.

Return ONLY valid JSON in this exact format (no markdown, no extra text):
{{
  "opening_en": "",
  "opening_ne": "",
  "points_en": ["", ""],
  "points_ne": ["", ""],
  "closing_en": "",
  "closing_ne": ""
}}
"""
