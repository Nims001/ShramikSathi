"""
Secondary splitting pass — applied only to sections longer than
MAX_SECTION_CHUNK_SIZE (src/config.py). Most Labour Act sections are
short enough to stay as a single chunk (confirmed by the length stats
printed in section_splitter.py); this is a safety net for the few
that aren't (e.g. Section 2's Definitions, which is very long).

Every sub-chunk keeps its parent section's number/chapter/pages in its
metadata, so citations still resolve to the correct section even if
that section got split into multiple pieces.
"""

from dataclasses import dataclass
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import MAX_SECTION_CHUNK_SIZE, CHUNK_OVERLAP
from src.ingestion.section_splitter import SectionChunk


@dataclass
class FinalChunk:
    section_number: str
    chapter: str
    text: str
    pages: List[int]
    section_part: int = 1  # 1 if the section wasn't sub-split


def chunk_sections(sections: List[SectionChunk]) -> List[FinalChunk]:
    """
    Applies RecursiveCharacterTextSplitter only to sections longer than
    MAX_SECTION_CHUNK_SIZE. Short sections pass through unchanged.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=MAX_SECTION_CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    final_chunks: List[FinalChunk] = []

    for section in sections:
        if len(section.text) <= MAX_SECTION_CHUNK_SIZE:
            final_chunks.append(FinalChunk(
                section_number=section.section_number,
                chapter=section.chapter,
                text=section.text,
                pages=section.pages,
                section_part=1,
            ))
            continue

        sub_texts = splitter.split_text(section.text)
        for i, sub_text in enumerate(sub_texts, start=1):
            final_chunks.append(FinalChunk(
                section_number=section.section_number,
                chapter=section.chapter,
                text=sub_text,
                pages=section.pages,
                section_part=i,
            ))

    return final_chunks


if __name__ == "__main__":
    from src.ingestion.pdf_loader import load_labour_act
    from src.ingestion.section_splitter import split_into_sections

    text, boundaries = load_labour_act()
    sections = split_into_sections(text, boundaries)
    final_chunks = chunk_sections(sections)

    print(f"{len(sections)} sections -> {len(final_chunks)} final chunks")

    multi_part = [c for c in final_chunks if c.section_part > 1]
    print(f"{len(multi_part)} sub-chunks came from sections that got split.")

    if multi_part:
        example_section = multi_part[0].section_number
        parts = [c for c in final_chunks if c.section_number == example_section]
        print(f"\nExample — Section {example_section} was split into {len(parts)} parts:")
        for p in parts:
            print(f"  Part {p.section_part}: {len(p.text)} chars")