# ── Stage 1: Builder ─────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────────────────
FROM python:3.11-slim

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# ← ADD THIS: upgrade system setuptools/wheel in runtime stage too
# This patches CVE-2026-23949 (jaraco.context) and CVE-2026-24049 (wheel)
RUN pip install --no-cache-dir --upgrade setuptools wheel

COPY --from=builder /root/.local /home/appuser/.local

COPY app/ ./app/

RUN mkdir -p /app/chroma_db && chown -R appuser:appuser /app

USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]