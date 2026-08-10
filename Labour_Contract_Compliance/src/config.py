"""
Central configuration for the Labour Act Compliance pipeline.
Every model name, path, and tunable constant lives here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---- API ----
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"

# ---- Paths ----
LABOUR_ACT_PDF_PATH = "data/raw/The-Labour-Act-2017.pdf"
CHROMA_DB_PATH = "data/chroma_db"
CHROMA_COLLECTION_NAME = "nepal_labour_act"

# ---- Embedding ----
EMBEDDING_MODEL_NAME = "BAAI/bge-base-en-v1.5"

# ---- Chunking ----
MAX_SECTION_CHUNK_SIZE = 1500    # characters; sections longer than this get sub-split
CHUNK_OVERLAP = 150

# ---- Retrieval ----
RETRIEVAL_K = 5

# ---- Rate limiting (Gemini free tier safety) ----
SECONDS_BETWEEN_CALLS = 5
MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 10