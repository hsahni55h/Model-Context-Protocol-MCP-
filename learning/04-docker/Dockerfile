# Use the official Python 3.11-slim image as the base image.
FROM python:3.11-slim

# Set the working directory inside the container to /app.
WORKDIR /app

# Install MCP SDK (the only dependency needed for the terminal server).
RUN pip install --no-cache-dir "mcp[cli]>=1.25.0,<2.0.0"

# Copy only the terminal server script into the container.
COPY terminal_server.py /app/terminal_server.py

# Create the workspace directory inside the container.
RUN mkdir -p /workspace

# Set environment variable so the server knows it's running in Docker.
ENV DOCKER_CONTAINER=true

# The server communicates via STDIO, so no port is exposed.
# Run the terminal server when the container starts.
CMD ["python", "terminal_server.py"]
