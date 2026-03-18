import os
import logging
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

logger = logging.getLogger(__name__)

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Cache the embeddings model so it only loads once
_embeddings = None
_vectorstore = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Returns a cached HuggingFace embeddings instance.
    Downloads the model on first call (~80MB), then uses the cache.
    """
    global _embeddings
    if _embeddings is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("Embedding model loaded successfully")
    return _embeddings


def get_vectorstore() -> Chroma:
    """
    Returns a cached ChromaDB instance backed by the persistent directory.
    Creates the directory and collection if they do not exist yet.
    """
    global _vectorstore
    if _vectorstore is None:
        os.makedirs(CHROMA_PATH, exist_ok=True)
        logger.info(f"Initialising ChromaDB at: {CHROMA_PATH}")
        _vectorstore = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=get_embeddings(),
            collection_name="documents",
        )
        count = _vectorstore._collection.count()
        logger.info(f"ChromaDB ready — {count} chunks in store")
    return _vectorstore


def reset_vectorstore() -> None:
    """
    Clears the in-memory cache so the next call to get_vectorstore()
    re-initialises from disk. Used after ingestion to pick up new chunks.
    """
    global _vectorstore
    _vectorstore = None


def is_vectorstore_ready() -> bool:
    """Returns True if ChromaDB is accessible and has at least one document."""
    try:
        vs = get_vectorstore()
        return vs._collection.count() > 0
    except Exception:
        return False