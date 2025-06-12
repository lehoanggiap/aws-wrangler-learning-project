# Use Python 3.11 with slim variant (smaller size, fewer packages)
# Provides foundation with Python runtime and basic tools
FROM python:3.11-slim

# Build arguments for image metadata and tagging
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Add metadata labels to the image for better tracking and identification
LABEL maintainer="Yaki Project Team" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="yaki-fastapi" \
      org.label-schema.description="FastAPI application for Yaki project with AWS Wrangler" \
      org.label-schema.url="https://github.com/your-username/yaki-project" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/your-username/yaki-project" \
      org.label-schema.vendor="Yaki Project" \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0"

# Set /app as the working directory inside the container
# All subsequent commands will run from this directory
WORKDIR /app

# Install system dependencies required for the application
# gcc & g++: C/C++ compilers needed for Python packages with native extensions
# curl: Used for health checks and HTTP requests
# Clean up package cache to reduce final image size
# RUN apt-get update && apt-get install -y \
#     gcc \
#     g++ \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first (before application code) for better Docker layer caching
# If requirements don't change, this layer can be reused on subsequent builds
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir: Prevents pip from storing cache, reducing image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and configuration
# api/: FastAPI application source code
# config.yaml: Application configuration file
COPY api/ ./api/
COPY config.yaml .

# Create non-root user for security (prevents privilege escalation attacks)
# useradd: Creates new user 'app' with home directory and bash shell
# chown: Changes ownership of /app directory to the 'app' user
# USER: Switch to run subsequent commands as 'app' user (not root)
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Document that the container listens on port 8000
# Note: This doesn't actually publish the port (done with docker run -p)
EXPOSE 8000

# Configure health check for container orchestration platforms
# --interval=30s: Check every 30 seconds
# --timeout=30s: Wait up to 30 seconds for response
# --start-period=5s: Wait 5 seconds before first check (app startup time)
# --retries=3: Mark unhealthy after 3 consecutive failures
# curl -f: Fails on HTTP error codes (4xx, 5xx), assumes /health endpoint exists
# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:8000/health || exit 1

# Start the FastAPI application using uvicorn ASGI server
# uvicorn: Production-ready ASGI server for FastAPI
# api.app:app: Points to the 'app' object in api/app.py
# --host 0.0.0.0: Bind to all network interfaces (allows external connections)
# --port 8000: Run on port 8000
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"] 