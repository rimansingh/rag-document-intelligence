import os
import logging
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from app.retrieval import retrieve

logger = logging.getLogger(__name__)

ANSWER_PROMPT = ChatPromptTemplate.from_template("""
You are a helpful assistant that answers questions based on provided documents.

INSTRUCTIONS:
- Answer ONLY from the context provided below
- If the context does not contain enough information, say clearly:
  "The uploaded documents do not contain enough information to answer this question."
- Cite the source document name when referencing specific information
- Be concise and direct — do not pad your answer
- Use markdown formatting for clarity (bullet points, bold, etc.)

CONTEXT FROM DOCUMENTS:
{context}

QUESTION:
{question}

ANSWER:
""")


# ── Agent state ───────────────────────────────────────────────────────────
class RAGState(TypedDict):
    question:         str
    retrieval_method: str
    documents:        list[Document]
    context:          str
    answer:           str
    sources:          list[dict]


# ── Graph nodes ───────────────────────────────────────────────────────────
def retrieve_node(state: RAGState) -> RAGState:
    """Retrieves relevant document chunks using the chosen strategy."""
    docs, method_used = retrieve(
        question=state["question"],
        method=state["retrieval_method"],
    )
    return {**state, "documents": docs, "retrieval_method": method_used}


def build_context_node(state: RAGState) -> RAGState:
    """
    Formats retrieved documents into a single context string
    and builds the sources list for citation.
    """
    docs = state["documents"]

    if not docs:
        return {
            **state,
            "context": "No relevant documents found.",
            "sources": [],
        }

    context_parts = []
    sources = []

    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        page   = doc.metadata.get("page", "")
        page_str = f" (page {page})" if page != "" else ""

        context_parts.append(
            f"[Source {i}: {source}{page_str}]\n{doc.page_content}"
        )
        sources.append({
            "content": doc.page_content[:300],
            "source":  source,
            "page":    page if page != "" else None,
        })

    return {
        **state,
        "context": "\n\n---\n\n".join(context_parts),
        "sources": sources,
    }


def generate_node(state: RAGState) -> RAGState:
    """Generates the final answer using the LLM and retrieved context."""
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        max_tokens=2048,
    )
    chain = ANSWER_PROMPT | llm
    answer = chain.invoke({
        "context":  state["context"],
        "question": state["question"],
    }).content

    logger.info(f"Generated answer ({len(answer)} chars)")
    return {**state, "answer": answer}


# ── Build graph ───────────────────────────────────────────────────────────
def build_rag_graph():
    """
    Compiles the LangGraph state machine:
      retrieve → build_context → generate → END
    """
    graph = StateGraph(RAGState)

    graph.add_node("retrieve",      retrieve_node)
    graph.add_node("build_context", build_context_node)
    graph.add_node("generate",      generate_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve",      "build_context")
    graph.add_edge("build_context", "generate")
    graph.add_edge("generate",      END)

    return graph.compile()


# Cache the compiled graph
_graph = None

def run_rag(question: str, retrieval_method: str = "hybrid") -> dict:
    """
    Main entry point. Runs the full RAG pipeline and returns
    answer, sources, and method used.
    """
    global _graph
    if _graph is None:
        _graph = build_rag_graph()

    initial_state: RAGState = {
        "question":         question,
        "retrieval_method": retrieval_method,
        "documents":        [],
        "context":          "",
        "answer":           "",
        "sources":          [],
    }

    result = _graph.invoke(initial_state)

    return {
        "answer":           result["answer"],
        "sources":          result["sources"],
        "retrieval_method": result["retrieval_method"],
    }