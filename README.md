# RAG Document Intelligence 📄

> Upload any document, ask questions in plain English, get cited answers — powered by a LangGraph agent with Hybrid Search + HyDE retrieval.

[![CI/CD](https://img.shields.io/github/actions/workflow/status/rimansingh/rag-document-intelligence/backend-deploy.yml?label=CI%2FCD&style=flat-square)](https://github.com/rimansingh/rag-document-intelligence/actions)
[![Tests](https://img.shields.io/badge/Tests-37%20passing-brightgreen?style=flat-square)](#testing)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)](https://python.org)

**🚀 [Live Demo → rimandeep-rag-frontend.hf.space](https://rimandeep-rag-frontend.hf.space)**

---

## What it does

Upload a PDF, Word document, CSV, or text file. Ask questions about it. Get accurate, cited answers that reference exactly which part of your document the answer came from.

The system uses three retrieval strategies working together to find the most relevant content before generating an answer:

| Strategy | How it works |
|---|---|
| **Semantic** | Embeds your question and finds similar chunks directly |
| **HyDE** | Generates a hypothetical answer first, then finds chunks similar to that — improving recall for complex questions |
| **Hybrid** | Fuses semantic + HyDE results and deduplicates — default strategy |

---

## Architecture

```
GitHub (rimansingh/rag-document-intelligence)
    │
    push to main
    ├── backend/**  → backend-deploy.yml → pytest → Trivy → HF Docker Space
    └── frontend/** → frontend-deploy.yml → sync → HF Streamlit Space

┌──────────────────────────────────────────────────────────────────┐
│                      HuggingFace Spaces                          │
│                                                                  │
│         POST /upload  ┐                                          │
│  User → Streamlit  ───┤ POST /chat       ──► Docker Space        │
│         Space      ───┘ DELETE /clear   ◄──  (FastAPI +          │
│                         JSON + sources       LangGraph)          │
└──────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼─────────────────┬────────────────┐
          ▼                   ▼                 ▼                ▼
      ChromaDB            Supabase          Groq API        LangChain
    (vector store)     (query history)   (LLaMA 3.3 70B)  (agent+retrieval)

Local (Terraform manages):
  rag-backend ◄── Prometheus scrapes /metrics ──► Grafana dashboards
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| LLM | LLaMA 3.3 70B via Groq | Free tier, ~300 tok/s, strong on reasoning |
| Agent framework | LangGraph | State-machine agent — explicit node control |
| Embeddings | HuggingFace sentence-transformers | Free, runs locally, no API cost |
| Vector store | ChromaDB | Persistent, no external service needed |
| Backend | FastAPI + Uvicorn | Async, auto-docs, Pydantic validation |
| Frontend | Streamlit | Rapid UI, free HuggingFace hosting |
| Database | Supabase | Managed Postgres, free tier |
| Containers | Docker (multi-stage build) | Reproducible, non-root, small image |
| IaC | Terraform (docker provider) | Infrastructure as code, full lifecycle |
| CI/CD | GitHub Actions | Automated test → scan → deploy |
| Monitoring | Prometheus + Grafana | Metrics, SLO alerting, dashboards |
| Keep-alive | Async self-ping + st_autorefresh | Prevents HF Space sleep on free tier |

---

## Project Structure

```
rag-document-intelligence/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI — routes, logging, Prometheus metrics, keep-alive
│   │   ├── agent.py         # LangGraph state machine (retrieve→context→generate)
│   │   ├── retrieval.py     # Semantic, HyDE, Hybrid retrieval strategies
│   │   ├── ingestion.py     # Multi-format loader + recursive chunking
│   │   ├── vectorstore.py   # ChromaDB + HuggingFace embeddings (cached)
│   │   ├── database.py      # Supabase client — save queries, fetch metrics
│   │   └── models.py        # Pydantic request/response models
│   ├── tests/
│   │   ├── conftest.py      # Shared fixtures (TestClient, mocks)
│   │   ├── test_api.py      # 13 endpoint tests
│   │   ├── test_retrieval.py # 12 retrieval strategy tests
│   │   └── test_ingestion.py # 12 ingestion pipeline tests
│   ├── Dockerfile           # Multi-stage build, non-root user
│   └── requirements.txt
├── frontend/
│   ├── app.py               # Streamlit UI — upload, chat, source citations
│   └── requirements.txt
├── terraform/
│   ├── main.tf              # Docker provider — 3 containers + network
│   ├── variables.tf         # Typed variables with sensitive marking
│   └── outputs.tf           # Service URLs as named outputs
├── monitoring/
│   ├── prometheus.yml       # Scrape config
│   ├── alerts.yml           # 3 SLO-based alert rules
│   └── grafana/
│       └── dashboard.json   # 8-panel pre-built dashboard
├── .github/
│   └── workflows/
│       ├── backend-deploy.yml   # test → Trivy scan → deploy
│       └── frontend-deploy.yml  # sync to HF Space
├── docker-compose.yml       # Full local stack (app + prometheus + grafana)
└── .env.example
```

---

## LangGraph Agent Pipeline

Every question runs through a three-node state machine:

```
User question
      │
      ▼
┌─────────────┐
│   retrieve  │  Hybrid Search (semantic + HyDE fusion + dedup)
└──────┬──────┘
       │  documents[]
       ▼
┌─────────────────┐
│  build_context  │  Format chunks with source citations
└──────┬──────────┘
       │  context string + sources[]
       ▼
┌──────────────┐
│   generate   │  LLaMA 3.3 answers from context only
└──────┬───────┘
       │
       ▼
   Answer + cited sources
```

If the context does not contain enough information, the agent returns: *"The uploaded documents do not contain enough information to answer this question."* — it never hallucinates from outside the document.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check — status, environment, chroma_ready |
| `GET` | `/metrics` | Usage stats from Supabase |
| `GET` | `/metrics/prometheus` | Prometheus scrape endpoint |
| `POST` | `/upload` | Ingest a document (PDF/DOCX/TXT/CSV) |
| `POST` | `/chat` | Ask a question, get a cited answer |
| `DELETE` | `/documents/clear` | Clear the vector store |

**`POST /chat` example:**
```json
// Request
{ "question": "What are the key findings?", "session_id": "optional-uuid" }

// Response
{
  "answer": "The key findings include...",
  "session_id": "abc-123",
  "sources": [
    { "content": "...", "source": "report.pdf", "page": 4 }
  ],
  "retrieval_method": "hybrid",
  "response_time_ms": 2840
}
```

---

## Local Development

**Prerequisites:** Python 3.11, Docker Desktop, Git

```bash
# 1. Clone
git clone https://github.com/rimansingh/rag-document-intelligence.git
cd rag-document-intelligence

# 2. Environment variables
cp .env.example .env
# Fill in: GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY

# 3. Start full stack with Docker Compose
docker compose up --build
# Backend:    http://localhost:8000
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000 (admin/admin)

# OR start with Terraform (manages lifecycle as IaC)
cd terraform
terraform init
terraform apply
```

**Backend only (for development):**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

---

## Testing

37 tests across three modules — all mocked, no real API calls:

```bash
cd backend
pytest tests/ -v
```

```
tests/test_api.py         13 tests  — health, metrics, upload, chat
tests/test_retrieval.py   12 tests  — semantic, HyDE, hybrid, dispatcher
tests/test_ingestion.py   12 tests  — file loading, chunking, pipeline

37 passed in ~4s
```

Tests run automatically on every push via GitHub Actions before any deployment occurs.

---

## CI/CD Pipeline

```
push to main (backend/** changed)
  ├── Job 1: pytest (37 tests) ──────────── must pass
  ├── Job 2: Trivy security scan ─────────── must pass (blocks on CRITICAL)
  └── Job 3: deploy to HF Docker Space ──── runs only if jobs 1+2 pass
        └── curl /health to verify deployment
```

No code reaches production without passing tests and a security scan first.

---

## Infrastructure as Code (Terraform)

The local development stack is fully managed by Terraform using the Docker provider:

```bash
cd terraform

terraform init      # download docker provider plugin
terraform plan      # see what will be created (7 resources)
terraform apply     # create network + 3 containers
terraform destroy   # tear everything down cleanly
```

Resources managed:
- `docker_network.rag_network` — shared container network
- `docker_image.backend` — built from local Dockerfile
- `docker_image.prometheus` — pulled from Docker Hub
- `docker_image.grafana` — pulled from Docker Hub
- `docker_container.backend` — FastAPI app with health check
- `docker_container.prometheus` — metrics scraping
- `docker_container.grafana` — dashboards

---

## Monitoring & Observability

**Prometheus metrics** instrumented on every request:

| Metric | Type | Description |
|---|---|---|
| `rag_requests_total` | Counter | Requests by endpoint and status |
| `rag_request_duration_seconds` | Histogram | Latency — p50/p95/p99 |
| `rag_retrieval_method_total` | Counter | Hybrid vs semantic vs HyDE usage |
| `rag_documents_ingested_total` | Counter | Total documents ingested |

**Grafana dashboard** — 8 panels at `http://localhost:3000`:
- Total requests, p95 latency, docs ingested, error rate (stat panels)
- Request rate over time, latency percentiles (time series)
- Retrieval method distribution (pie chart)
- Success vs error rate (time series)

**SLO-based alert rules** in `monitoring/alerts.yml`:
- `RAGBackendDown` — fires if backend unreachable for 1 min (critical)
- `HighLatency` — fires if p95 > 10s for 2 min (warning)
- `HighErrorRate` — fires if error rate > 10% for 2 min (warning)

---

## Environment Variables

| Variable | Description | Where to get it |
|---|---|---|
| `GROQ_API_KEY` | LLM API key | [console.groq.com](https://console.groq.com) |
| `SUPABASE_URL` | Supabase project URL | Supabase dashboard |
| `SUPABASE_KEY` | Supabase anon key | Supabase dashboard |
| `BACKEND_URL` | URL the frontend calls | Your HF Docker Space URL |
| `HF_SPACE_URL` | Backend Space URL for keep-alive self-ping | `https://rimandeep-rag-backend.hf.space` |
| `KEEP_ALIVE_INTERVAL` | Ping interval in seconds | Default: `600` (10 min) |
| `ENVIRONMENT` | `development` or `production` | Set manually |
| `CHROMA_PATH` | ChromaDB persistence directory | Default: `./chroma_db` |

Never commit `.env` — use GitHub Actions secrets for CI/CD and HuggingFace Space secrets for production.

---

## Roadmap

- [ ] Multi-document support with per-document filtering
- [ ] Conversation memory across sessions
- [ ] Support for web URL ingestion
- [ ] Kubernetes deployment with Helm chart

---

## Author

**Rimandeep Singh** — DevOps / Cloud / AI Engineer
[LinkedIn](https://linkedin.com/in/rimandeepsingh) · [GitHub](https://github.com/rimansingh) · [Portfolio](https://portfolio-website-3qw.pages.dev/) · [AI DevOps Assistant](https://rimandeep-ai-devops-frontend.hf.space/)