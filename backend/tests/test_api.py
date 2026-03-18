import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document


# ── /health ──────────────────────────────────────────────────────────────
class TestHealth:

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_has_required_fields(self, client):
        data = response = client.get("/health").json()
        assert "status"       in data
        assert "environment"  in data
        assert "chroma_ready" in data

    def test_health_status_is_healthy(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"

    def test_health_environment_is_test(self, client):
        data = client.get("/health").json()
        assert data["environment"] == "test"


# ── /metrics ─────────────────────────────────────────────────────────────
class TestMetrics:

    def test_metrics_returns_200(self, client):
        with patch("app.main.get_metrics") as mock:
            mock.return_value = {
                "total_queries":            5,
                "total_documents":          2,
                "average_response_time_ms": 1200.0,
                "retrieval_methods_used":   {"hybrid": 5},
            }
            response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_has_required_fields(self, client):
        with patch("app.main.get_metrics") as mock:
            mock.return_value = {
                "total_queries":            0,
                "total_documents":          0,
                "average_response_time_ms": 0.0,
                "retrieval_methods_used":   {},
            }
            data = client.get("/metrics").json()

        assert "total_queries"            in data
        assert "total_documents"          in data
        assert "average_response_time_ms" in data
        assert "retrieval_methods_used"   in data


# ── /upload ───────────────────────────────────────────────────────────────
class TestUpload:

    def test_upload_txt_succeeds(self, client, mock_vectorstore, sample_document_bytes):
        with patch("app.main.ingest_document") as mock_ingest:
            mock_ingest.return_value = {
                "document_id": "test-uuid-123",
                "chunk_count": 3,
            }
            response = client.post(
                "/upload",
                files={"file": ("test.txt", sample_document_bytes, "text/plain")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"]    == "test.txt"
        assert data["chunk_count"] == 3
        assert "document_id"       in data
        assert "message"           in data

    def test_upload_rejects_unsupported_type(self, client):
        response = client.post(
            "/upload",
            files={"file": ("test.exe", b"binary content", "application/octet-stream")},
        )
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_upload_requires_file(self, client):
        response = client.post("/upload")
        assert response.status_code == 422


# ── /chat ─────────────────────────────────────────────────────────────────
class TestChat:

    def test_chat_returns_answer(self, client):
        with patch("app.main.is_vectorstore_ready", return_value=True), \
             patch("app.main.run_rag") as mock_rag, \
             patch("app.main.save_query"):

            mock_rag.return_value = {
                "answer":           "Terraform is an IaC tool.",
                "sources":          [{"content": "Terraform...", "source": "test.txt", "page": None}],
                "retrieval_method": "hybrid",
            }

            response = client.post(
                "/chat",
                json={"question": "What is Terraform?"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["answer"]           == "Terraform is an IaC tool."
        assert data["retrieval_method"] == "hybrid"
        assert "session_id"             in data
        assert "response_time_ms"       in data
        assert len(data["sources"])     == 1

    def test_chat_rejects_empty_question(self, client):
        response = client.post("/chat", json={})
        assert response.status_code == 422

    def test_chat_returns_400_when_no_documents(self, client):
        with patch("app.main.is_vectorstore_ready", return_value=False):
            response = client.post(
                "/chat",
                json={"question": "What is Terraform?"},
            )
        assert response.status_code == 400
        assert "No documents" in response.json()["detail"]

    def test_chat_accepts_session_id(self, client):
        with patch("app.main.is_vectorstore_ready", return_value=True), \
             patch("app.main.run_rag") as mock_rag, \
             patch("app.main.save_query"):

            mock_rag.return_value = {
                "answer":           "Test answer",
                "sources":          [],
                "retrieval_method": "hybrid",
            }

            response = client.post(
                "/chat",
                json={
                    "question":   "Test?",
                    "session_id": "my-custom-session",
                },
            )

        assert response.status_code == 200
        assert response.json()["session_id"] == "my-custom-session"