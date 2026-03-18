import pytest
from unittest.mock import patch, MagicMock
from app.ingestion import chunk_documents, load_file, SUPPORTED_TYPES
from langchain_core.documents import Document


class TestSupportedTypes:

    def test_txt_is_supported(self):
        assert ".txt" in SUPPORTED_TYPES

    def test_pdf_is_supported(self):
        assert ".pdf" in SUPPORTED_TYPES

    def test_docx_is_supported(self):
        assert ".docx" in SUPPORTED_TYPES

    def test_csv_is_supported(self):
        assert ".csv" in SUPPORTED_TYPES

    def test_exe_is_not_supported(self):
        assert ".exe" not in SUPPORTED_TYPES


class TestLoadFile:

    def test_rejects_unsupported_extension(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            load_file(b"content", "malware.exe")

    def test_loads_txt_file(self, sample_document_bytes):
        docs = load_file(sample_document_bytes, "test.txt")
        assert len(docs) > 0
        assert hasattr(docs[0], "page_content")
        assert len(docs[0].page_content) > 0

    def test_loaded_docs_have_content(self, sample_document_bytes):
        docs = load_file(sample_document_bytes, "test.txt")
        for doc in docs:
            assert doc.page_content.strip() != ""


class TestChunkDocuments:

    def test_attaches_source_metadata(self, sample_document_bytes):
        docs = load_file(sample_document_bytes, "myfile.txt")
        chunks = chunk_documents(docs, "myfile.txt")

        for chunk in chunks:
            assert chunk.metadata["source"] == "myfile.txt"

    def test_attaches_chunk_id(self, sample_document_bytes):
        docs = load_file(sample_document_bytes, "test.txt")
        chunks = chunk_documents(docs, "test.txt")

        for i, chunk in enumerate(chunks):
            assert "chunk_id" in chunk.metadata

    def test_chunks_are_not_empty(self, sample_document_bytes):
        docs = load_file(sample_document_bytes, "test.txt")
        chunks = chunk_documents(docs, "test.txt")

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.page_content.strip() != ""

    def test_chunk_size_respected(self):
        # Create a long document that must be split
        long_text = "This is a sentence about cloud infrastructure. " * 50
        doc = Document(page_content=long_text, metadata={})
        chunks = chunk_documents([doc], "long.txt", chunk_size=100, chunk_overlap=10)

        # Should produce multiple chunks
        assert len(chunks) > 1
        # Each chunk should be at most chunk_size + some overlap tolerance
        for chunk in chunks:
            assert len(chunk.page_content) <= 200


class TestIngestDocument:

    def test_full_ingestion_pipeline(self, mock_vectorstore, sample_document_bytes):
        with patch("app.ingestion.get_vectorstore", return_value=mock_vectorstore), \
             patch("app.ingestion.save_document_metadata") as mock_save, \
             patch("app.ingestion.reset_vectorstore"):

            from app.ingestion import ingest_document
            result = ingest_document(sample_document_bytes, "test.txt")

        assert "document_id" in result
        assert "chunk_count" in result
        assert result["chunk_count"] > 0
        mock_save.assert_called_once()
        mock_vectorstore.add_documents.assert_called_once()

    def test_returns_document_id(self, mock_vectorstore, sample_document_bytes):
        with patch("app.ingestion.get_vectorstore", return_value=mock_vectorstore), \
             patch("app.ingestion.save_document_metadata"), \
             patch("app.ingestion.reset_vectorstore"):

            from app.ingestion import ingest_document
            result = ingest_document(sample_document_bytes, "test.txt")

        assert isinstance(result["document_id"], str)
        assert len(result["document_id"]) > 0

    def test_rejects_unsupported_file_type(self, mock_vectorstore):
        with pytest.raises(ValueError, match="Unsupported file type"):
            from app.ingestion import ingest_document
            ingest_document(b"content", "virus.exe")