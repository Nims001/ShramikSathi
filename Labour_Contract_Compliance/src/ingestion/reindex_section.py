"""
Utility for fixing a single bad chunk in the Chroma vectorstore —
e.g. if you later find a section that was malformed by a chunking bug,
or the source PDF text needs a manual correction — WITHOUT re-embedding
and rebuilding the entire Labour Act collection.

Typical use: you spot-check sections after indexing, find one is
broken, fix the extraction/splitting logic (or the text itself), then
use this to patch just that one section.
"""

from langchain_core.documents import Document

from src.ingestion.embed_and_index import get_vectorstore, _chunk_id
from src.ingestion.chunker import FinalChunk


def reindex_section(section_number: str, corrected_text: str, chapter: str,
                     pages: list, section_part: int = 1, vectorstore=None):
    """
    Replace one section's chunk(s) in the Chroma vectorstore with a
    corrected version. Deletes any existing chunk(s) for that section
    first (in case a bug previously split it into multiple bad parts),
    then adds the corrected chunk(s).
    """
    if vectorstore is None:
        vectorstore = get_vectorstore()

    # Find and delete any existing chunks for this section, regardless
    # of how many parts it was previously split into.
    existing = vectorstore.get(where={"section": section_number})
    if existing["ids"]:
        vectorstore.delete(ids=existing["ids"])
        print(f"Deleted {len(existing['ids'])} old chunk(s) for section {section_number}.")

    corrected_chunk = FinalChunk(
        section_number=section_number,
        chapter=chapter,
        text=corrected_text,
        pages=pages,
        section_part=section_part,
    )

    document = Document(
        page_content=corrected_chunk.text,
        metadata={
            "section": corrected_chunk.section_number,
            "chapter": corrected_chunk.chapter or "unknown",
            "pages": ",".join(str(p) for p in corrected_chunk.pages) if corrected_chunk.pages else "unknown",
            "section_part": corrected_chunk.section_part,
        },
    )

    chunk_id = _chunk_id(corrected_chunk)
    vectorstore.add_documents(documents=[document], ids=[chunk_id])
    print(f"Re-indexed section {section_number} as '{chunk_id}'.")
    return vectorstore


if __name__ == "__main__":
    # Example manual fix — replace with a real correction if/when you
    # actually find a bad section during testing.
    reindex_section(
        section_number="28",
        corrected_text="28. \nWorking hours: (1) No employer shall employ labours to work more than eight hours a day and forty-eight hours a week... [corrected text]",
        chapter="5",
        pages=[14],
        section_part=1,
    )