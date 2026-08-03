FROM python:3.11-slim AS base

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY mcp-toolkit/pyproject.toml mcp-toolkit/pyproject.toml
COPY mcp-toolkit/src/ mcp-toolkit/src/
RUN pip install --no-cache-dir ./mcp-toolkit

COPY mcp-toolkit/examples/voyageai/pyproject.toml voyageai/pyproject.toml
COPY mcp-toolkit/examples/voyageai/ voyageai/
RUN pip install --no-cache-dir ./voyageai

WORKDIR /app/voyageai

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
