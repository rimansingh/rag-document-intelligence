import streamlit as st
import requests
import os
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="RAG Document Intelligence",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Keep the HF Space awake: refresh every 10 minutes ────────────────────
st_autorefresh(interval=10 * 60 * 1000, key="keep_alive_refresh")

st.markdown("""
<style>
  /* ── Google Fonts ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

  /* ── Hide Streamlit chrome ── */
  div[data-testid="stToolbar"],
  div[data-testid="stDecoration"],
  div[data-testid="stStatusWidget"],
  #MainMenu, footer { display: none !important; }

  header[data-testid="stHeader"] {
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
  }

  /* ── Global Styles (Modern Soft UI) ── */
  .stApp {
    background: #f8fafc; /* Soft Slate */
    font-family: 'Inter', sans-serif;
    color: #1e293b;
  }

  [data-testid="stAppViewContainer"] > section.main > div.block-container {
    padding-top: 0 !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 100% !important;
    margin: 0 !important;
    background: #ffffff; /* Floating Content Card */
    border-radius: 0 0 24px 24px;
    margin-top: 0 !important;
    margin-bottom: 2rem;
    box-shadow: 
      0 10px 15px -3px rgba(0, 0, 0, 0.04),
      0 4px 6px -4px rgba(0, 0, 0, 0.02),
      0 20px 25px -5px rgba(0, 0, 0, 0.03); /* Multi-layered soft shadow */
    border: 1px solid rgba(226, 232, 240, 0.8);
  }

  /* ── Sidebar (Glassmorphism Lite) ── */
  section[data-testid="stSidebar"] {
    background-color: #f0f4ff !important; /* Soft Indigo */
    border-right: 1px solid #e2e8f0;
  }
  
  section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    padding-top: 0 !important;
  }
  
  section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #4338ca;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
    margin-top: 1.5rem;
    opacity: 0.8;
  }

  section[data-testid="stSidebar"] hr {
    border-color: #e2e8f0;
    margin: 1.5rem 0;
  }

  /* ── Sidebar Buttons (Premium Branded) ── */
  section[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: #ffffff;
    border: none;
    border-radius: 14px;
    font-weight: 600;
    font-size: 14px;
    padding: 0.6rem 1rem;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
    width: 100%;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  section[data-testid="stSidebar"] .stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3);
    filter: brightness(1.05);
  }

  /* ── Hero section (Modern Display) ── */
  .hero {
    padding-bottom: 2rem;
    margin-bottom: 2.5rem;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .hero-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    color: #0f172a;
    margin: 0;
    letter-spacing: -0.04em;
    line-height: 1.1;
  }

  .hero-sub {
    font-size: 1rem;
    color: #64748b;
    margin-top: 0.5rem;
    font-weight: 500;
    max-width: 600px;
  }

  .hero-badge {
    background: linear-gradient(135deg, #e0e7ff 0%, #f1f5f9 100%);
    border: 1px solid #c7d2fe;
    color: #4338ca;
    padding: 6px 14px;
    border-radius: 100px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 1rem;
  }

  /* ── Chat Messages (Soft UI Bubbles) ── */
  div[data-testid="stChatMessage"] {
    background: #ffffff !important;
    border: 1px solid #f1f5f9 !important;
    border-radius: 20px !important;
    padding: 1.25rem 1.5rem !important;
    margin-bottom: 1.25rem !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
  }
  
  div[data-testid="stChatMessage"] .stMarkdown p {
    color: #334155 !important;
    font-size: 15px !important;
    line-height: 1.7 !important;
  }

  /* User Message Distinction (Soft Brand Tint) */
  div[data-testid="stChatMessage"][data-testid="user"] {
    background: #f8faff !important;
    border-color: #e0e7ff !important;
  }

  /* ── Metrics (Modern Stat Minimal) ── */
  div[data-testid="metric-container"] {
    background: #fbfcfe !important;
    border: 1px solid #f1f5f9 !important;
    border-radius: 16px !important;
    padding: 1.25rem !important;
    text-align: center !important;
    transition: all 0.3s ease;
  }
  
  div[data-testid="metric-container"]:hover {
    transform: translateY(-3px);
    border-color: #c7d2fe;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.03);
  }

  div[data-testid="metric-container"] label {
    color: #94a3b8 !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
  }

  div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #0f172a !important;
    font-size: 1.75rem !important;
    font-weight: 800 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    margin-top: 0.25rem !important;
  }

  /* ── Source Cards (Floating Glass) ── */
  .source-box {
    background: #ffffff;
    border: 1px solid #f1f5f9;
    border-left: 6px solid #6366f1;
    border-radius: 16px;
    padding: 1.5rem;
    font-size: 14px;
    margin: 1rem 0;
    color: #475569;
    line-height: 1.8;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
  }

  .source-meta {
    color: #6366f1;
    font-size: 12px;
    font-weight: 800;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  /* ── Custom File Uploader ── */
  div[data-testid="stFileUploadDropzone"] {
    background: #fbfcfe !important;
    border: 2px dashed #e2e8f0 !important;
    border-radius: 20px !important;
    padding: 3rem !important;
    transition: all 0.3s ease;
  }
  
  div[data-testid="stFileUploadDropzone"]:hover {
    border-color: #6366f1 !important;
    background: #ffffff !important;
  }
  
  /* ── Chat Input ── */
  div[data-testid="stChatInput"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 20px !important;
    padding: 8px 12px !important;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.03) !important;
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
        "<div style='text-align:left; padding:0.25rem 0.5rem;'>"
        "<p style='color:#4338ca; font-family:\"Plus Jakarta Sans\", sans-serif; font-weight:800; font-size:1.4rem; margin:0; letter-spacing:-0.03em;'>"
        "RAG IQ</p>"
        "<p style='color:#64748b; font-size:0.85rem; font-weight:500; margin:4px 0 0;'>Intelligence Augmented</p>"
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
        "<div style='color:#475569; font-size:13px; font-weight:500; line-height:2.0; padding:0 0.5rem;'>"
        "<span style='color:#6366f1; margin-right:8px;'>01</span> Upload documentation<br>"
        "<span style='color:#6366f1; margin-right:8px;'>02</span> Query in natural language<br>"
        "<span style='color:#6366f1; margin-right:8px;'>03</span> Receive a cited, AI-generated answer"
        "</div>"
        "<div style='margin-top:1.5rem; background:#ffffff; border:1px solid #eef2ff;"
        "border-radius:14px; padding:12px 16px; font-size:12px; color:#1e293b; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);'>"
        "<strong style='color:#4338ca; font-family:\"Plus Jakarta Sans\", sans-serif;'>RAG ENGINE v1.0</strong><br>"
        "<span style='color:#64748b; font-weight:500;'>Hybrid Search + HyDE Fusion</span>"
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
                "<div style='background:#ffffff; border:1px solid #dcfce7; border-radius:10px;"
                "padding:8px 12px; font-size:12px; font-weight:600; color:#166534; box-shadow: 0 2px 4px rgba(0,0,0,0.02);'>"
                "<span style='color:#22c55e; margin-right:6px;'>●</span> System Operational</div>",
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
            "<div style='background:#ffffff; border:1px solid #fee2e2; border-radius:10px;"
            "padding:8px 12px; font-size:12px; font-weight:600; color:#991b1b; box-shadow: 0 2px 4px rgba(0,0,0,0.02);'>"
            "<span style='color:#ef4444; margin-right:6px;'>●</span> System Offline</div>",
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
  <div class="hero-badge">Deep Retrieval Agent</div>
  <div class="hero-title">RAG Document Intelligence</div>
  <div class="hero-sub">Upload any documentation and query it with human-like reasoning. Powered by LLaMA 3.3 and Hybrid Search + HyDE.</div>
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
                elif response.status_code == 429:
                    st.warning("Rate limit reached on the LLM API. Please wait 10-15 seconds and try again.")
                else:
                    st.error(f"Error {response.status_code}")

            except requests.exceptions.Timeout:
                st.error("Request timed out — the model may be busy, try again.")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")