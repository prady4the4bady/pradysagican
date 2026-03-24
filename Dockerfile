FROM python:3.11-slim

LABEL maintainer="Prady <f20240323@dubai.bits-pilani.ac.in>"
LABEL description="PRADYSAGICAN — Super General Intelligence System v6.0"

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[dev]"

# Application code
COPY . .

# Data dirs
RUN mkdir -p data/chromadb data/logs data/memory data/tools data/benchmarks

# Verify
RUN python -m pytest tests/ --tb=no -q || true

EXPOSE 8000

ENTRYPOINT ["pradysagican"]
CMD ["serve", "--port", "8000"]
