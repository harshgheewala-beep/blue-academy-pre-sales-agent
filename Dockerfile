# --- Stage 1: Build stage ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml .
# README is often required by pyproject metadata
COPY README.md .

# Install dependencies into a specific prefix
RUN pip install --upgrade pip && \
    pip install --prefix=/install .

# --- Stage 2: Final runtime stage ---
FROM python:3.11-slim

WORKDIR /app

# Copy the installed library files from the FIRST stage
COPY --from=builder /install /usr/local

# Copy your actual source code
COPY . .

# Security: Run as non-root user
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--port", "8000", "--reload"]
