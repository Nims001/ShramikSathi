"""Configuration for the "Analyse with AI" RAG pipeline.

Paths default to `apps/api/data/` (the vectorstore + the Labour Act PDF that
were copied from the reference pipeline). Everything can be overridden through
environment variables so Docker / local dev can point elsewhere.
"""

import os
from pathlib import Path

from ..config import settings

# apps/api/data  (parents[0]=ai, parents[1]=app, parents[2]=apps/api)
DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# ---- API ----
GEMINI_API_KEY = settings.gemini_api_key or os.getenv("GEMINI_API_KEY") or ""
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ---- Paths ----
LABOUR_ACT_PDF_PATH = os.getenv(
    "LABOUR_ACT_PDF_PATH", str(DATA_DIR / "raw" / "The-Labour-Act-2017.pdf")
)
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", str(DATA_DIR / "chroma_db"))
CHROMA_COLLECTION_NAME = "nepal_labour_act"

# ---- Embedding ----
# The stored vectors were produced with this model — do not change it or
# retrieval will stop matching.
EMBEDDING_MODEL_NAME = "BAAI/bge-base-en-v1.5"

# ---- Chunking (kept for reference; used if the store is ever re-built) ----
MAX_SECTION_CHUNK_SIZE = 1500
CHUNK_OVERLAP = 150

# ---- Retrieval ----
RETRIEVAL_K = 5

# ---- Rate limiting (Gemini free tier safety) ----
SECONDS_BETWEEN_CALLS = 5
MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 10
