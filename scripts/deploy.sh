#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# JyotishAI - Production Deployment Script
# ---------------------------------------------------------------------------

set -euo pipefail

echo "========================================="
echo "Starting JyotishAI Production Deployment"
echo "========================================="

# 1. Load environment variables
if [ -f .env ]; then
    echo "[1/5] Loading environment variables from .env"
    export $(grep -v '^#' .env | xargs)
else
    echo "[ERROR] .env file not found! Copy .env.production.example to .env and configure keys."
    exit 1
fi

# 2. Rebuild and pull containers
echo "[2/5] Pulling and rebuilding containers..."
docker compose build --pull

# 3. Run database migrations in background/temporary container
echo "[3/5] Executing database migrations via Alembic..."
docker compose run --rm backend alembic upgrade head

# 4. Boot application stack with graceful timeout
echo "[4/5] Starting application services..."
docker compose up -d --remove-orphans

# 5. Verify container health status
echo "[5/5] Checking service health endpoints..."
sleep 5

max_attempts=12
attempt=1
health_status="unhealthy"

while [ $attempt -le $max_attempts ]; do
    echo "Checking API health (attempt $attempt/$max_attempts)..."
    # Call internal health check through host mapped Nginx port 80
    if curl -s -f http://localhost/health > /dev/null; then
        health_status="healthy"
        break
    fi
    sleep 5
    attempt=$((attempt+1))
done

if [ "$health_status" = "healthy" ]; then
    echo "========================================="
    echo "SUCCESS: JyotishAI deployed successfully!"
    echo "========================================="
else
    echo "========================================="
    echo "WARNING: Health checks timed out! Check service logs."
    echo "docker compose logs"
    echo "========================================="
    exit 1
fi
