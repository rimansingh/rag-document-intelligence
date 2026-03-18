import os
import uuid
import logging
import tempfile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    CSVLoader,
    TextLoader,
)
from langchain_core.documents import Document
from app.vectorstore import get_vectorstore, reset_vectorstore
from app.database import save_document_metadata

logger = logging.getLogger(__name__)

# Map file extensions to their LangChain loaders
LOADERS = {
    ".pdf":  PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".csv":  CSVLoader,
    ".txt":  TextLoader,
}

SUPPORTED_TYPES = list(LOADERS.keys())


def load_file(file_bytes: bytes, filename: str) -> list[Document]:
    """
    Writes bytes to a temp file, loads with the appropriate
    LangChain loader, then cleans up the temp file.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext not in LOADERS:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Supported: {', '.join(SUPPORTED_TYPES)}"
        )

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(file_bytes)
        tmp_path = f.name

    try:
        loader = LOADERS[ext](tmp_path)
        docs = loader.load()
        logger.info(f"Loaded {len(docs)} pages/sections from {filename}")
        return docs
    finally:
        os.unlink(tmp_path)


def chunk_documents(
    docs: list[Document],
    filename: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> list[Document]:
    """
    Splits documents into overlapping chunks with source metadata attached.
    Uses recursive splitting so natural boundaries (paragraphs, sentences)
    are preserved over hard character limits.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)

    # Attach consistent source metadata to every chunk
    for i, chunk in enumerate(chunks):
        chunk.metadata["source"] = filename
        chunk.metadata["chunk_id"] = i

    logger.info(f"Split into {len(chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")
    return chunks


def ingest_document(file_bytes: bytes, filename: str) -> dict:
    """
    Full ingestion pipeline:
      1. Load file into LangChain documents
      2. Split into chunks
      3. Embed and store in ChromaDB
      4. Save metadata to Supabase
      5. Reset vectorstore cache so next query picks up new chunks

    Returns a dict with document_id and chunk_count.
    """
    file_size_kb = len(file_bytes) // 1024
    document_id = str(uuid.uuid4())

    logger.info(f"Starting ingestion: {filename} ({file_size_kb}KB)")

    # 1 & 2: Load and chunk
    docs = load_file(file_bytes, filename)
    chunks = chunk_documents(docs, filename)

    if not chunks:
        raise ValueError(f"No content could be extracted from {filename}")

    # 3: Store in ChromaDB
    vectorstore = get_vectorstore()
    vectorstore.add_documents(chunks)
    logger.info(f"Stored {len(chunks)} chunks in ChromaDB")

    # 4: Save metadata to Supabase
    save_document_metadata(
        document_id=document_id,
        filename=filename,
        file_type=os.path.splitext(filename)[1].lower(),
        chunk_count=len(chunks),
        file_size_kb=file_size_kb,
    )

    # 5: Reset cache so retrieval picks up new chunks immediately
    reset_vectorstore()

    logger.info(f"Ingestion complete: {filename} → {len(chunks)} chunks")

    return {
        "document_id": document_id,
        "chunk_count": len(chunks),
    }