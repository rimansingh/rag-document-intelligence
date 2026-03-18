import os
import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from app.vectorstore import get_vectorstore

logger = logging.getLogger(__name__)

# ── LLM (shared across retrieval strategies) ──────────────────────────────
def get_llm():
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.3-70b-versatile",
        temperature=0,
        max_tokens=1024,
    )


# ── Strategy 1: Semantic retrieval ────────────────────────────────────────
def semantic_retrieve(question: str, k: int = 4) -> list[Document]:
    """
    Direct similarity search — embeds the question and finds
    the k most similar chunks in ChromaDB.
    Fast and works well for straightforward questions.
    """
    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(question, k=k)
    logger.info(f"Semantic retrieval: {len(docs)} docs for '{question[:60]}'")
    return docs


# ── Strategy 2: HyDE retrieval ────────────────────────────────────────────
HYDE_PROMPT = ChatPromptTemplate.from_template(
    """Write a short factual paragraph (3-5 sentences) that would 
    directly answer this question. Be specific and detailed.
    
    Question: {question}
    
    Hypothetical answer:"""
)

def hyde_retrieve(question: str, k: int = 4) -> list[Document]:
    """
    Hypothetical Document Embeddings — asks the LLM to write a
    hypothetical answer, then finds chunks similar to THAT answer
    rather than the question. Improves recall for complex questions
    where the question wording differs from how the answer is phrased.
    """
    llm = get_llm()
    chain = HYDE_PROMPT | llm
    hypothetical_answer = chain.invoke({"question": question}).content
    logger.info(f"HyDE generated hypothetical answer ({len(hypothetical_answer)} chars)")

    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(hypothetical_answer, k=k)
    logger.info(f"HyDE retrieval: {len(docs)} docs")
    return docs


# ── Strategy 3: Hybrid (semantic + HyDE fused) ────────────────────────────
def hybrid_retrieve(question: str, k: int = 6) -> list[Document]:
    """
    Combines semantic and HyDE retrieval then deduplicates.
    Semantic retrieval catches exact matches.
    HyDE catches conceptually related content.
    Together they improve both precision and recall.
    """
    half_k = max(2, k // 2)

    semantic_docs = semantic_retrieve(question, k=half_k)
    hyde_docs     = hyde_retrieve(question, k=half_k)

    # Deduplicate by page content — keep first occurrence
    seen: set[str] = set()
    combined: list[Document] = []

    for doc in semantic_docs + hyde_docs:
        content_key = doc.page_content.strip()[:200]
        if content_key not in seen:
            seen.add(content_key)
            combined.append(doc)

    result = combined[:k]
    logger.info(
        f"Hybrid retrieval: {len(semantic_docs)} semantic + "
        f"{len(hyde_docs)} HyDE → {len(result)} after dedup"
    )
    return result


# ── Dispatcher ────────────────────────────────────────────────────────────
RETRIEVAL_STRATEGIES = {
    "semantic": semantic_retrieve,
    "hyde":     hyde_retrieve,
    "hybrid":   hybrid_retrieve,
}

def retrieve(
    question: str,
    method: str = "hybrid",
    k: int = 6,
) -> tuple[list[Document], str]:
    """
    Main retrieval entry point. Returns (documents, method_used).
    Falls back to hybrid if an unknown method is requested.
    """
    if method not in RETRIEVAL_STRATEGIES:
        logger.warning(f"Unknown method '{method}', falling back to hybrid")
        method = "hybrid"

    docs = RETRIEVAL_STRATEGIES[method](question, k=k)
    return docs, method