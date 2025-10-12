# Nomad Backend - Multi-stage Dockerfile
# Optimized for production deployment with FastAPI

# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies to /install
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

# Labels
LABEL maintainer="Sophia/Nomad Team"
LABEL description="Nomad AI Agent Orchestrator - Backend API"
LABEL version="0.9.0"

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash nomad

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=nomad:nomad backend/ ./backend/
COPY --chown=nomad:nomad core/ ./core/
COPY --chown=nomad:nomad tools/ ./tools/
COPY --chown=nomad:nomad mcp_servers/ ./mcp_servers/
COPY --chown=nomad:nomad prompts/ ./prompts/
COPY --chown=nomad:nomad config/ ./config/

# Create directories
RUN mkdir -p logs memory sandbox && chown -R nomad:nomad logs memory sandbox

# Switch to non-root user
USER nomad

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/nomad/.local/bin:$PATH" \
    NOMAD_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/health/ping || exit 1

# Expose port
EXPOSE 8080

# Start command
CMD ["python", "-m", "uvicorn", "backend.server:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--log-level", "info"]
