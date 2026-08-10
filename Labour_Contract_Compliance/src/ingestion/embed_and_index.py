"""
Embeds each Labour Act chunk using a local sentence-transformers model
(via LangChain's HuggingFaceEmbeddings wrapper) and writes it into a
persistent ChromaDB collection (via LangChain's Chroma wrapper).

Run this once (via scripts/build_vector_store.py) to build the
reference vector store. Re-run only if the Labour Act PDF or the
chunking logic changes.
"""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.config import (
    CHROMA_DB_PATH,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
)
from src.ingestion.chunker import FinalChunk


def get_embedding_model():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)


def get_vectorstore(embedding_model=None):
    """Returns the (created-if-missing) Chroma vectorstore, ready to query or add to."""
    if embedding_model is None:
        embedding_model = get_embedding_model()

    return Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=embedding_model,
        persist_directory=CHROMA_DB_PATH,
    )


def _chunk_id(chunk: FinalChunk) -> str:
    """Deterministic ID so re-running indexing on the same chunk overwrites cleanly."""
    return f"section_{chunk.section_number}_part_{chunk.section_part}"


def index_chunks(chunks: list[FinalChunk], vectorstore=None):
    """
    Converts each FinalChunk into a LangChain Document and upserts it
    into the Chroma vectorstore. Uses deterministic IDs so re-running
    this is safe/idempotent (re-indexing overwrites, doesn't duplicate).
    """
    if vectorstore is None:
        vectorstore = get_vectorstore()

    documents = []
    ids = []

    for chunk in chunks:
        documents.append(Document(
            page_content=chunk.text,
            metadata={
                "section": chunk.section_number,
                "chapter": chunk.chapter or "unknown",
                "pages": ",".join(str(p) for p in chunk.pages) if chunk.pages else "unknown",
                "section_part": chunk.section_part,
            },
        ))
        ids.append(_chunk_id(chunk))

    vectorstore.add_documents(documents=documents, ids=ids)
    print(f"Indexed {len(chunks)} chunks into '{CHROMA_COLLECTION_NAME}'.")
    return vectorstore


if __name__ == "__main__":
    from src.ingestion.pdf_loader import load_labour_act
    from src.ingestion.section_splitter import split_into_sections
    from src.ingestion.chunker import chunk_sections

    text, boundaries = load_labour_act()
    sections = split_into_sections(text, boundaries)
    final_chunks = chunk_sections(sections)

    index_chunks(final_chunks)

    # Quick sanity check: run one test query
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search("working hours per day", k=3)
    print("\nTest query: 'working hours per day' — top 3 results:")
    for r in results:
        print(f"  Section {r.metadata['section']} (part {r.metadata['section_part']}): {r.page_content[:100]}...")