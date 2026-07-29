# Use the official Python 3.11-slim image as the base image.
FROM python:3.11-slim

# Set the working directory inside the container.
WORKDIR /app

# Prevent Python from writing .pyc files and force stdout/stderr to be unbuffered.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Default workspace inside the container (you can override at runtime).
ENV WORKSPACE_DIR=/app/workspace

# Copy only requirements first to leverage Docker layer caching.
COPY requirements.txt /app/requirements.txt

# Install required Python packages from requirements.txt.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files into the container.
COPY . /app

# Ensure workspace directory exists inside container.
RUN mkdir -p /app/workspace

# Expose port 8081 so that the container can accept incoming connections.
EXPOSE 8081

# Define the command to run your SSE server.
CMD ["python", "terminal_server_sse.py"]
