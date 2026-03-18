from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    message: str


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class SourceDocument(BaseModel):
    content: str
    source: str
    page: Optional[int] = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[SourceDocument]
    retrieval_method: str
    response_time_ms: int


class HealthResponse(BaseModel):
    status: str
    environment: str
    chroma_ready: bool


class MetricsResponse(BaseModel):
    total_queries: int
    total_documents: int
    average_response_time_ms: float
    retrieval_methods_used: dict[str, int]