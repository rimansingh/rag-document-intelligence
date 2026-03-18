import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document


def make_doc(content: str, source: str = "test.txt") -> Document:
    """Helper to create a test Document."""
    return Document(
        page_content=content,
        metadata={"source": source, "chunk_id": 0}
    )


class TestSemanticRetrieve:

    def test_returns_documents(self, mock_vectorstore):
        with patch("app.retrieval.get_vectorstore", return_value=mock_vectorstore):
            from app.retrieval import semantic_retrieve
            results = semantic_retrieve("What is Terraform?", k=2)

        assert len(results) > 0
        assert hasattr(results[0], "page_content")

    def test_calls_similarity_search(self, mock_vectorstore):
        with patch("app.retrieval.get_vectorstore", return_value=mock_vectorstore):
            from app.retrieval import semantic_retrieve
            semantic_retrieve("test question", k=3)

        mock_vectorstore.similarity_search.assert_called_once_with(
            "test question", k=3
        )

    def test_respects_k_parameter(self, mock_vectorstore):
        docs = [make_doc(f"doc {i}") for i in range(5)]
        mock_vectorstore.similarity_search.return_value = docs[:2]

        with patch("app.retrieval.get_vectorstore", return_value=mock_vectorstore):
            from app.retrieval import semantic_retrieve
            results = semantic_retrieve("question", k=2)

        assert len(results) == 2


class TestHybridRetrieve:

    def test_deduplicates_identical_content(self, mock_vectorstore):
        # Both semantic and HyDE return the same document
        duplicate_doc = make_doc("Same content about Terraform")
        mock_vectorstore.similarity_search.return_value = [duplicate_doc]

        with patch("app.retrieval.get_vectorstore", return_value=mock_vectorstore), \
             patch("app.retrieval.hyde_retrieve", return_value=[duplicate_doc]):
            from app.retrieval import hybrid_retrieve
            results = hybrid_retrieve("What is Terraform?", k=4)

        # Should deduplicate — only one unique document
        contents = [r.page_content for r in results]
        assert len(contents) == len(set(contents))

    def test_combines_semantic_and_hyde(self, mock_vectorstore):
        semantic_doc = make_doc("Semantic result about Terraform")
        hyde_doc     = make_doc("HyDE result about IaC")

        mock_vectorstore.similarity_search.return_value = [semantic_doc]

        with patch("app.retrieval.get_vectorstore", return_value=mock_vectorstore), \
             patch("app.retrieval.hyde_retrieve", return_value=[hyde_doc]):
            from app.retrieval import hybrid_retrieve
            results = hybrid_retrieve("Terraform", k=4)

        contents = [r.page_content for r in results]
        assert "Semantic result about Terraform" in contents
        assert "HyDE result about IaC"           in contents

    def test_returns_at_most_k_documents(self, mock_vectorstore):
        docs = [make_doc(f"unique doc {i}") for i in range(10)]
        mock_vectorstore.similarity_search.return_value = docs[:5]

        with patch("app.retrieval.get_vectorstore", return_value=mock_vectorstore), \
             patch("app.retrieval.hyde_retrieve", return_value=docs[5:]):
            from app.retrieval import hybrid_retrieve
            results = hybrid_retrieve("question", k=4)

        assert len(results) <= 4


class TestRetrieveDispatcher:

    def test_unknown_method_falls_back_to_hybrid(self, mock_vectorstore):
        mock_llm_response = MagicMock()
        mock_llm_response.content = "Hypothetical answer about infrastructure"

        with patch("app.retrieval.get_vectorstore", return_value=mock_vectorstore), \
            patch("app.retrieval.get_llm") as mock_get_llm:

            mock_chain = MagicMock()
            mock_chain.invoke.return_value = mock_llm_response
            mock_get_llm.return_value = mock_chain

            from app.retrieval import retrieve
            docs, method = retrieve("question", method="unknown_method")

        assert method == "hybrid"

    def test_semantic_method_dispatches_correctly(self, mock_vectorstore):
        with patch("app.retrieval.get_vectorstore", return_value=mock_vectorstore):
            from app.retrieval import retrieve
            docs, method = retrieve("question", method="semantic")

        assert method == "semantic"
        mock_vectorstore.similarity_search.assert_called_once()

    def test_returns_method_used(self, mock_vectorstore):
        with patch("app.retrieval.get_vectorstore", return_value=mock_vectorstore), \
             patch("app.retrieval.semantic_retrieve", return_value=[]):
            from app.retrieval import retrieve
            _, method = retrieve("question", method="semantic")

        assert method == "semantic"