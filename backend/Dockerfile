# ── Stage 1: Builder ──────────────────────────────────────────────────────
# Install dependencies in a separate stage to keep final image clean
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────
FROM python:3.11-slim

# Never run as root in production
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY app/ ./app/

# Create chroma_db directory with correct permissions
RUN mkdir -p /app/chroma_db && chown -R appuser:appuser /app

USER appuser

# Add local packages to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8000

# Health check using Python stdlib — no curl needed
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]