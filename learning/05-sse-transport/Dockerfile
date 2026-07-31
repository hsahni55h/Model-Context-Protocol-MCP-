FROM python:3.11-slim

WORKDIR /app

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Copy dependency file first (layer caching)
COPY pyproject.toml /app/

# Install dependencies
RUN uv pip install --system "mcp[cli]>=1.25.0,<2.0.0" uvicorn starlette

# Copy server code
COPY server.py /app/

# SSE server listens on port 8000
EXPOSE 8000

# Run the SSE server
CMD ["python", "server.py"]
