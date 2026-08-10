"""Access to the persistent Chroma vectorstore of The Labour Act, 2017.

Only the *loading* side of the reference pipeline's embed_and_index.py is
needed here — the store is pre-built (see apps/api/data/chroma_db) and shipped
with the app. The embedding model is loaded lazily on first use and cached,
because pulling the ~130 MB model (and any Chroma start-up cost) on every
request would be wasteful.
"""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from .config import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME

_vectorstore = None


def get_embedding_model():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)


def get_vectorstore():
    """Returns the (cached) Chroma vectorstore, creating it on first use."""
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name=CHROMA_COLLECTION_NAME,
            embedding_function=get_embedding_model(),
            persist_directory=CHROMA_DB_PATH,
        )
    return _vectorstore
