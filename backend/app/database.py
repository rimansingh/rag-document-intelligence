import os
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

_client = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        _client = create_client(url, key)
    return _client


def save_document_metadata(
    document_id: str,
    filename: str,
    file_type: str,
    chunk_count: int,
    file_size_kb: int,
) -> None:
    try:
        get_client().table("documents").insert({
            "id":           document_id,
            "filename":     filename,
            "file_type":    file_type,
            "chunk_count":  chunk_count,
            "file_size_kb": file_size_kb,
        }).execute()
    except Exception as e:
        # Log but do not crash — DB failure should not break ingestion
        logger.warning(f"Failed to save document metadata: {e}")


def save_query(
    session_id: str,
    question: str,
    answer: str,
    sources_used: int,
    retrieval_method: str,
    response_time_ms: int,
) -> None:
    try:
        get_client().table("queries").insert({
            "session_id":       session_id,
            "question":         question,
            "answer":           answer,
            "sources_used":     sources_used,
            "retrieval_method": retrieval_method,
            "response_time_ms": response_time_ms,
        }).execute()
    except Exception as e:
        logger.warning(f"Failed to save query: {e}")


def get_metrics() -> dict:
    try:
        client = get_client()
        queries   = client.table("queries").select("*").execute().data
        documents = client.table("documents").select("*").execute().data

        total_q = len(queries)
        times   = [q["response_time_ms"] for q in queries if q.get("response_time_ms")]
        avg_time = round(sum(times) / len(times), 1) if times else 0.0

        methods: dict[str, int] = {}
        for q in queries:
            m = q.get("retrieval_method", "unknown")
            methods[m] = methods.get(m, 0) + 1

        return {
            "total_queries":             total_q,
            "total_documents":           len(documents),
            "average_response_time_ms":  avg_time,
            "retrieval_methods_used":    methods,
        }

    except Exception as e:
        logger.error(f"Failed to fetch metrics: {e}")
        return {
            "total_queries":            0,
            "total_documents":          0,
            "average_response_time_ms": 0.0,
            "retrieval_methods_used":   {},
        }