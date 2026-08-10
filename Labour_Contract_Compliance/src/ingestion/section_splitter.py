"""
Splits the concatenated Labour Act text into per-section chunks, using
the section header pattern as the split point — NOT the PDF page
boundary. This correctly handles a section that spans two pages, since
splitting happens on the merged text, not per-page.

SECTION_HEADER_PATTERN requires a number + period on its own line,
followed by a title that ends in a colon within the next few lines.
The title itself is allowed to wrap across multiple lines and contain
any characters (parentheses, quotes, etc.) — this matters because real
section titles in this PDF sometimes wrap ("...despite change in
\\nownership:") or include parentheses ("...remuneration (grade):").

This is still strict enough to reject false positives like inline
cross-references ("(w) ... pursuant to Section 5") because those don't
have a colon-terminated title within a few lines of a standalone
number+period line.
"""

import re
from dataclasses import dataclass, field
from typing import List

from src.ingestion.pdf_loader import load_labour_act, pages_spanned

# Matches: start of line, 1-3 digit section number, period, newline,
# then up to 3 lines with no colon, then a line containing a colon
# (the colon marks the end of the section title).
SECTION_HEADER_PATTERN = re.compile(
    r'(?=^(\d{1,3})\.\s*\n(?:[^\n:]*\n){0,3}[^\n:]*:)',
    re.MULTILINE
)

# Pulls the number back out of a chunk that starts with "28.\nSome Title:"
SECTION_NUMBER_PATTERN = re.compile(r'^(\d{1,3})\.\s*\n')

# Only matches "Chapter" as a standalone heading line, not a stray
# number appearing elsewhere in body text.
CHAPTER_PATTERN = re.compile(r'^Chapter[\s-]+(\d+)', re.IGNORECASE | re.MULTILINE)


@dataclass
class SectionChunk:
    section_number: str
    chapter: str
    text: str
    pages: List[int] = field(default_factory=list)


def clean_page_artifacts(text: str) -> str:
    """
    Strip common page-break artifacts left behind by PDF text extraction:
    standalone page-number lines, and the repeating lawcommission.gov.np
    footer link seen in this specific PDF.
    """
    text = re.sub(r'\n\s*\d{1,4}\s*\n', '\n', text)
    text = re.sub(
        r'\[?www\.lawcommission\.gov\.np\]?(\(https://www\.lawcommission\.gov\.np\))?',
        '',
        text,
        flags=re.IGNORECASE,
    )
    return text


def split_into_sections(full_text: str, page_boundaries) -> List[SectionChunk]:
    full_text = clean_page_artifacts(full_text)
    raw_sections = SECTION_HEADER_PATTERN.split(full_text)

    sections = []
    cursor = 0
    current_chapter = None

    for raw in raw_sections:
        if not raw.strip():
            continue

        start = full_text.find(raw, cursor)
        if start == -1:
            start = cursor
        end = start + len(raw)
        cursor = end

        chapter_match = CHAPTER_PATTERN.search(raw)
        if chapter_match:
            current_chapter = chapter_match.group(1)

        section_match = SECTION_NUMBER_PATTERN.match(raw.strip() + "\n")
        if not section_match:
            continue  # not a section-starting chunk (e.g. preamble) — skip

        section_number = section_match.group(1)
        pages = pages_spanned(start, end, page_boundaries)

        sections.append(SectionChunk(
            section_number=section_number,
            chapter=current_chapter,
            text=raw.strip(),
            pages=pages,
        ))

    return sections


def run_sanity_checks(sections: List[SectionChunk], full_text: str = None):
    numbers = [int(s.section_number) for s in sections]

    seen = set()
    duplicates = sorted(set(n for n in numbers if n in seen or seen.add(n)))
    print(f"\nDuplicate section numbers found: {duplicates}")

    missing = []
    if numbers:
        expected = set(range(1, max(numbers) + 1))
        missing = sorted(expected - set(numbers))
        print(f"Missing section numbers (gaps): {missing}")

    lengths = [len(s.text) for s in sections]
    if lengths:
        print(f"Min length: {min(lengths)}, Max: {max(lengths)}, Avg: {sum(lengths)//len(lengths)}")

    if missing and full_text is not None:
        for missing_num in missing:
            idx = full_text.find(f"\n{missing_num}.")
            if idx != -1:
                print(f"\n--- Around missing Section {missing_num} ---")
                print(full_text[idx:idx + 200])
            else:
                print(f"\n--- Section {missing_num}: pattern not found at all ---")


if __name__ == "__main__":
    text, boundaries = load_labour_act()
    sections = split_into_sections(text, boundaries)

    print(f"Found {len(sections)} sections.\n")
    for s in sections[:5]:
        print(f"Section {s.section_number} (Chapter {s.chapter}) — pages {s.pages}")
        print(s.text[:150], "...\n")

    run_sanity_checks(sections, full_text=text)