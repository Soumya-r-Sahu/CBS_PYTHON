# Account Service Dockerfile
# Multi-stage build for production deployment

# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r cbs && useradd -r -g cbs cbs

# Copy virtual environment from builder stage
COPY --from=builder /venv /venv

# Set working directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY alembic.ini ./
COPY migrations/ ./migrations/

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R cbs:cbs /app

# Switch to non-root user
USER cbs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Default command
CMD ["python", "-m", "uvicorn", "src.account_service.interfaces.api:app", "--host", "0.0.0.0", "--port", "8001"]
