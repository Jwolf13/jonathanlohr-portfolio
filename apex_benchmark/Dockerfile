# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Pull the pre-built venv from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:main", "--host", "0.0.0.0", "--port", "8000"]
