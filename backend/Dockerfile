# Stage 1: Build stage
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ requirements/

# Install production dependencies only
RUN pip install --no-cache-dir -r requirements/production.txt

# Stage 2: Runtime stage
FROM python:3.12-slim AS runner

WORKDIR /app

# Install curl for healthcheck, libpq for PostgreSQL connections, and required ML C++ libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    libstdc++6 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies
COPY --from=builder /usr/local /usr/local

# Create non-root group and user
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

# Set up data storage directories with correct ownership
RUN mkdir -p /app/chroma_db /app/avatars && chown -R appuser:appuser /app

COPY --chown=appuser:appuser . .

USER appuser

# Port and environment configurations
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run DB migrations then start the production server
CMD ["sh", "-c", "python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
