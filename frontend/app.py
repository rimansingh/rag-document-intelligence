import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="RAG Document Intelligence",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  /* ── Hide Streamlit chrome ── */
  div[data-testid="stToolbar"],
  div[data-testid="stDecoration"],
  div[data-testid="stStatusWidget"],
  #MainMenu, footer { display: none !important; }

  /* ── Collapse the header bar height so it doesn't push content down ── */
  header[data-testid="stHeader"] {
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
  }

  /* ── Global background ── */
  .stApp {
    background-color: #f8f9fb;
  }

  /* ── Layout ── */
  div[data-testid="stAppViewContainer"] > section.main > div.block-container {
    padding-top: 0.75rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 100% !important;
  }

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
  }
  section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #4f46e5;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
  }
  section[data-testid="stSidebar"] hr {
    border-color: #f0f0f5;
    margin: 0.75rem 0;
  }

  /* ── Sidebar buttons ── */
  section[data-testid="stSidebar"] .stButton > button {
    background-color: #4f46e5;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    transition: background 0.2s;
  }
  section[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #4338ca;
  }

  /* ── Hero banner ── */
  .hero {
    background: #ffffff;
    border: 1px solid #e0e7ff;
    border-left: 4px solid #4f46e5;
    border-radius: 10px;
    padding: 1rem 1.5rem;
    margin-top: 0 !important;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  .hero-title {
    font-size: 1.35rem;
    font-weight: 800;
    color: #1e1b4b;
    margin: 0;
    line-height: 1.2;
  }
  .hero-sub {
    font-size: 0.75rem;
    color: #6b7280;
    margin-top: 3px;
  }
  .hero-badge {
    margin-left: auto;
    background: #eef2ff;
    border: 1px solid #c7d2fe;
    color: #4f46e5;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    white-space: nowrap;
  }

  /* ── Source card ── */
  .source-box {
    background: #f9fafb;
    border-left: 3px solid #6366f1;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 12.5px;
    margin: 6px 0;
    color: #374151;
    line-height: 1.6;
  }
  .source-meta {
    color: #6366f1;
    font-size: 11.5px;
    font-weight: 600;
    margin-bottom: 4px;
  }

  /* ── Metric cards ── */
  div[data-testid="metric-container"] {
    background: #f5f3ff;
    border: 1px solid #e0e7ff;
    border-radius: 8px;
    padding: 8px;
  }
  div[data-testid="metric-container"] label {
    color: #6366f1 !important;
    font-size: 11px !important;
  }
  div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #1e1b4b !important;
    font-size: 1.3rem !important;
  }

  /* ── Expander ── */
  details summary {
    font-size: 12.5px;
    color: #6366f1;
  }

  /* ── Chat messages ── */
  div[data-testid="stChatMessage"] {
    background: #ffffff;
    border: 1px solid #f0f0f5;
    border-radius: 10px;
    padding: 0.3rem 0.5rem;
    margin-bottom: 0.4rem;
  }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────
if "messages"     not in st.session_state:
    st.session_state.messages     = []
if "session_id"   not in st.session_state:
    st.session_state.session_id   = None
if "doc_uploaded" not in st.session_state:
    st.session_state.doc_uploaded = False

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='text-align:center; padding:0.6rem 0 0.4rem;'>"
        "<span style='font-size:1.8rem;'>📄</span>"
        "<p style='color:#1e1b4b; font-weight:800; font-size:0.95rem; margin:4px 0 2px;'>"
        "RAG Document Intelligence</p>"
        "<p style='color:#9ca3af; font-size:0.7rem; margin:0;'>Upload · Ask · Cite</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ── Upload ──
    st.markdown("### 📂 Upload Document")
    uploaded_file = st.file_uploader(
        "PDF, DOCX, TXT, CSV",
        type=["pdf", "docx", "txt", "csv"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.markdown(
            f"<div style='font-size:12px; color:#6b7280; margin-bottom:6px;'>"
            f"📎 {uploaded_file.name}</div>",
            unsafe_allow_html=True,
        )
        if st.button("Ingest Document", use_container_width=True):
            with st.spinner("Ingesting..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/upload",
                        files={"file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type,
                        )},
                        timeout=120,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.success(
                            f"✅ {data['chunk_count']} chunks from **{data['filename']}**"
                        )
                        st.session_state.doc_uploaded = True
                    else:
                        st.error(f"Upload failed: {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.button("🗑️ Clear all documents", use_container_width=True):
        try:
            r = requests.delete(f"{BACKEND_URL}/documents/clear", timeout=10)
            if r.status_code == 200:
                st.success("Vector store cleared")
                st.session_state.doc_uploaded = False
            else:
                st.error("Failed to clear")
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")

    # ── How it works ──
    st.markdown("### 💡 How it works")
    st.markdown(
        "<div style='color:#6b7280; font-size:12.5px; line-height:1.9;'>"
        "① Upload a document<br>"
        "② Ask questions in chat<br>"
        "③ Get answers with citations"
        "</div>"
        "<div style='margin-top:10px; background:#f5f3ff; border:1px solid #e0e7ff;"
        "border-radius:8px; padding:8px 12px; font-size:12px; color:#4f46e5;'>"
        "🔍 <strong>Hybrid Search + HyDE</strong><br>"
        "<span style='color:#9ca3af;'>Semantic similarity &amp; hypothetical document embeddings</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Live metrics ──
    st.markdown("### 📊 Live Metrics")
    try:
        r = requests.get(f"{BACKEND_URL}/metrics", timeout=3)
        if r.status_code == 200:
            m = r.json()
            col1, col2 = st.columns(2)
            col1.metric("Queries", m["total_queries"])
            col2.metric("Docs", m["total_documents"])
            st.caption(f"⏱ Avg: {m['average_response_time_ms']}ms")
    except Exception:
        st.caption("Metrics unavailable")

    st.markdown("---")

    # ── Backend status ──
    st.markdown("### 🔌 Backend Status")
    try:
        h = requests.get(f"{BACKEND_URL}/health", timeout=3)
        if h.status_code == 200:
            data = h.json()
            st.markdown(
                "<div style='background:#f0fdf4; border:1px solid #bbf7d0; border-radius:6px;"
                "padding:6px 10px; font-size:12.5px; color:#166534;'>🟢 Backend healthy</div>",
                unsafe_allow_html=True,
            )
            if data.get("chroma_ready", False):
                st.markdown(
                    "<div style='margin-top:6px; font-size:12px; color:#2563eb;'>"
                    "📚 Documents ready for querying</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div style='margin-top:6px; font-size:12px; color:#d97706;'>"
                    "⚠️ No documents uploaded yet</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.error("Backend error")
    except Exception:
        st.markdown(
            "<div style='background:#fef2f2; border:1px solid #fecaca; border-radius:6px;"
            "padding:6px 10px; font-size:12.5px; color:#991b1b;'>🔴 Cannot reach backend</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    if st.button("🗑 Clear conversation", use_container_width=True):
        st.session_state.messages   = []
        st.session_state.session_id = None
        st.rerun()

# ── Hero header ───────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <span style="font-size:1.8rem;">📄</span>
  <div>
    <div class="hero-title">RAG Document Intelligence</div>
    <div class="hero-sub">LLaMA 3.3 · Groq · LangGraph · ChromaDB · Hybrid Search + HyDE</div>
  </div>
  <div class="hero-badge">⚡ Powered by Groq</div>
</div>
""", unsafe_allow_html=True)

# ── Conversation history ──────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg.get("sources"):
            with st.expander(
                f"📎 {len(msg['sources'])} sources · "
                f"{msg.get('retrieval_method', 'hybrid')} · "
                f"{msg.get('response_time_ms', 0)}ms"
            ):
                for src in msg["sources"]:
                    page_info = f" · page {src['page']}" if src.get("page") else ""
                    st.markdown(
                        f'<div class="source-box">'
                        f'<div class="source-meta">{src["source"]}{page_info}</div>'
                        f'{src["content"][:300]}...'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

# ── Chat input ────────────────────────────────────────────────────────────
question = st.chat_input("Ask a question about your document...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/chat",
                    json={
                        "question":   question,
                        "session_id": st.session_state.session_id,
                    },
                    timeout=120,
                )

                if response.status_code == 200:
                    data = response.json()
                    st.session_state.session_id = data["session_id"]
                    st.markdown(data["answer"])

                    if data.get("sources"):
                        with st.expander(
                            f"📎 {len(data['sources'])} sources · "
                            f"{data['retrieval_method']} · "
                            f"{data['response_time_ms']}ms"
                        ):
                            for src in data["sources"]:
                                page_info = f" · page {src['page']}" if src.get("page") else ""
                                st.markdown(
                                    f'<div class="source-box">'
                                    f'<div class="source-meta">{src["source"]}{page_info}</div>'
                                    f'{src["content"][:300]}...'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )

                    st.session_state.messages.append({
                        "role":             "assistant",
                        "content":          data["answer"],
                        "sources":          data.get("sources", []),
                        "retrieval_method": data.get("retrieval_method"),
                        "response_time_ms": data.get("response_time_ms"),
                    })

                elif response.status_code == 400:
                    st.warning(response.json().get("detail"))
                else:
                    st.error(f"Error {response.status_code}")

            except requests.exceptions.Timeout:
                st.error("Request timed out — the model may be busy, try again.")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
