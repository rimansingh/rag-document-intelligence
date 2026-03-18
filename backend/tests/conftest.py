import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Set dummy env vars before importing the app
# This prevents real API calls during tests
os.environ.setdefault("GROQ_API_KEY",  "test-key")
os.environ.setdefault("SUPABASE_URL",  "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY",  "test-supabase-key")
os.environ.setdefault("ENVIRONMENT",   "test")
os.environ.setdefault("CHROMA_PATH",   "./test_chroma_db")

from app.main import app


@pytest.fixture(scope="session")
def client():
    """FastAPI test client — reused across all tests in the session."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_vectorstore():
    """A mock ChromaDB vectorstore that returns one fake document."""
    from langchain_core.documents import Document

    mock = MagicMock()
    mock._collection.count.return_value = 1
    mock.similarity_search.return_value = [
        Document(
            page_content="Terraform is an IaC tool by HashiCorp.",
            metadata={"source": "test.txt", "chunk_id": 0}
        )
    ]
    mock.add_documents.return_value = None
    return mock


@pytest.fixture
def sample_document_bytes():
    """Simple plain text document as bytes for ingestion tests."""
    content = (
        "Terraform is an Infrastructure as Code tool by HashiCorp. "
        "It uses HCL to define cloud resources. "
        "Terraform plan shows changes. Terraform apply makes them."
    )
    return content.encode("utf-8")