import os
import uuid
import time
import logging
import json
import asyncio
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import PlainTextResponse
from app.vectorstore import is_vectorstore_ready

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

from app.models import (
    ChatRequest, ChatResponse, SourceDocument,
    DocumentUploadResponse, HealthResponse, MetricsResponse,
)
from app.agent import run_rag
from app.ingestion import ingest_document, SUPPORTED_TYPES
from app.vectorstore import is_vectorstore_ready
from app.database import save_query, get_metrics

# ── Structured JSON logging ───────────────────────────────────────────────
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "level":   record.levelname,
            "message": record.getMessage(),
            "logger":  record.name,
        }
        return json.dumps(log)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

# ── Prometheus metrics ────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "rag_requests_total",
    "Total requests by endpoint",
    ["endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "rag_request_duration_seconds",
    "Request latency in seconds",
    ["endpoint"],
)
RETRIEVAL_METHOD_COUNT = Counter(
    "rag_retrieval_method_total",
    "Retrieval method used",
    ["method"],
)
DOCS_INGESTED = Counter(
    "rag_documents_ingested_total",
    "Total documents ingested",
)


# ── Keep-alive background task ────────────────────────────────────────────
async def keep_alive():
    """
    Pings /health every 10 minutes to prevent Hugging Face Space from sleeping.
    The Space URL is read from HF_SPACE_URL env var; falls back to localhost.
    """
    url = os.getenv("HF_SPACE_URL", "http://localhost:7860")
    ping_url = f"{url.rstrip('/')}/health"
    interval = int(os.getenv("KEEP_ALIVE_INTERVAL", 600))  # seconds, default 10 min

    await asyncio.sleep(30)  # wait for app to fully start
    while True:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(ping_url)
            logger.info(f"Keep-alive ping → {ping_url} [{r.status_code}]")
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")
        await asyncio.sleep(interval)


# ── App lifecycle ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("RAG Document Intelligence starting up")
    task = asyncio.create_task(keep_alive())
    yield
    task.cancel()
    logger.info("RAG Document Intelligence shutting down")


app = FastAPI(
    title="RAG Document Intelligence",
    description="Upload documents, ask questions, get cited answers",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        environment=os.getenv("ENVIRONMENT", "development"),
        chroma_ready=is_vectorstore_ready(),
    )


@app.get("/metrics/prometheus", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus scrape endpoint."""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/metrics", response_model=MetricsResponse)
async def metrics():
    """Human-readable usage metrics from Supabase."""
    data = get_metrics()
    return MetricsResponse(**data)


@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts a document upload, ingests it into ChromaDB,
    and saves metadata to Supabase.
    """
    start = time.time()

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED_TYPES)}"
        )

    try:
        file_bytes = await file.read()
        result = ingest_document(file_bytes, file.filename)

        DOCS_INGESTED.inc()
        REQUEST_COUNT.labels(endpoint="upload", status="success").inc()
        REQUEST_LATENCY.labels(endpoint="upload").observe(time.time() - start)

        return DocumentUploadResponse(
            document_id=result["document_id"],
            filename=file.filename,
            chunk_count=result["chunk_count"],
            message=f"Successfully ingested {result['chunk_count']} chunks",
        )

    except Exception as e:
        REQUEST_COUNT.labels(endpoint="upload", status="error").inc()
        logger.error(f"Upload failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Accepts a question, runs the RAG pipeline,
    and returns an answer with cited sources.
    """
    start = time.time()
    session_id = request.session_id or str(uuid.uuid4())

    if not is_vectorstore_ready():
        raise HTTPException(
            status_code=400,
            detail="No documents uploaded yet. Please upload a document first."
        )

    try:
        result = run_rag(
            question=request.question,
            retrieval_method="hybrid",
        )

        elapsed_ms = round((time.time() - start) * 1000)

        save_query(
            session_id=session_id,
            question=request.question,
            answer=result["answer"],
            sources_used=len(result["sources"]),
            retrieval_method=result["retrieval_method"],
            response_time_ms=elapsed_ms,
        )

        RETRIEVAL_METHOD_COUNT.labels(method=result["retrieval_method"]).inc()
        REQUEST_COUNT.labels(endpoint="chat", status="success").inc()
        REQUEST_LATENCY.labels(endpoint="chat").observe(time.time() - start)

        return ChatResponse(
            answer=result["answer"],
            session_id=session_id,
            sources=[SourceDocument(**s) for s in result["sources"]],
            retrieval_method=result["retrieval_method"],
            response_time_ms=elapsed_ms,
        )

    except HTTPException:
        raise
    except Exception as e:
        REQUEST_COUNT.labels(endpoint="chat", status="error").inc()
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/clear")
async def clear_documents():
    """Clears all documents from the vector store."""
    import shutil
    chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
    try:
        if os.path.exists(chroma_path):
            shutil.rmtree(chroma_path)
        reset_vectorstore()
        return {"message": "Vector store cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))