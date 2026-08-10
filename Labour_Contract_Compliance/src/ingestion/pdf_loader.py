"""
Loads the Nepal Labour Act PDF using LangChain's PyMuPDFLoader.
The PDF is native digital text (not scanned), so no OCR is needed.

LangChain's PyMuPDFLoader returns one Document object per page. We
concatenate all pages into a single continuous text string here, while
tracking which character range came from which page — this matters
because legal sections can span a page break (e.g. Section 52 spans
pages 19-20), and we don't want to split a section in half just because
it crosses a PDF page boundary.
"""

from langchain_community.document_loaders import PyMuPDFLoader
from src.config import LABOUR_ACT_PDF_PATH


def load_labour_act(pdf_path: str = LABOUR_ACT_PDF_PATH):
    """
    Loads and concatenates all pages of the Labour Act PDF.

    Returns:
        full_text: str — the entire document as one continuous string
        page_boundaries: list[tuple[int, int]] — (start_char_index, page_number)
            for each page, in order. Used later to figure out which
            page(s) a given section came from.
    """
    loader = PyMuPDFLoader(pdf_path)
    pages = loader.load()  # returns a list of Document objects, one per page

    full_text = ""
    page_boundaries = []

    for page in pages:
        # LangChain's PyMuPDFLoader stores the page number in metadata,
        # 0-indexed — we convert to 1-indexed for human-readable output.
        page_number = page.metadata.get("page", 0) + 1

        page_boundaries.append((len(full_text), page_number))
        full_text += page.page_content + "\n"

    return full_text, page_boundaries


def pages_spanned(start_char: int, end_char: int, page_boundaries):
    """
    Given a character range [start_char, end_char) in the concatenated
    full_text, return the list of page numbers that range overlaps.
    """
    spanned = []
    for i, (boundary_start, page_number) in enumerate(page_boundaries):
        boundary_end = (
            page_boundaries[i + 1][0]
            if i + 1 < len(page_boundaries)
            else float("inf")
        )
        if start_char < boundary_end and end_char > boundary_start:
            spanned.append(page_number)

    return spanned


if __name__ == "__main__":
    text, boundaries = load_labour_act()
    print(f"Loaded {len(text)} characters across {len(boundaries)} pages.")
    print("\nFirst 300 characters:\n", text[:300])