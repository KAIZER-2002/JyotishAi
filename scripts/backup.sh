#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# JyotishAI - Production Database and Vector Index Backup Script
# ---------------------------------------------------------------------------

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RUNNING_DIR="$BACKUP_DIR/$TIMESTAMP"

echo "========================================="
echo "Starting JyotishAI System Backup"
echo "========================================="

# 1. Create backups directory structure
mkdir -p "$RUNNING_DIR"

# 2. Database backup (pg_dump within postgres container)
echo "Backing up PostgreSQL database..."
if docker compose ps | grep -q "jyotishai-postgres"; then
    # Load environment variables
    POSTGRES_USER=$(docker compose exec -t postgres printenv POSTGRES_USER | tr -d '\r')
    POSTGRES_DB=$(docker compose exec -t postgres printenv POSTGRES_DB | tr -d '\r')
    
    docker compose exec -t postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -F c -b -v > "$RUNNING_DIR/database.dump"
    echo "Database backup saved to $RUNNING_DIR/database.dump"
else
    echo "[ERROR] PostgreSQL container is not running! Cannot perform database backup."
    exit 1
fi

# 3. Chroma DB Vector Index backup
echo "Backing up Chroma DB indexes..."
# Standard compose volumes path or local directories copy
# Copy chroma volume mapping contents safely
if docker compose ps | grep -q "jyotishai-chroma"; then
    # Create target vector directory
    mkdir -p "$RUNNING_DIR/chroma"
    # Copy indices from the volume
    docker compose cp chroma:/index_data/. "$RUNNING_DIR/chroma/"
    echo "Chroma index backup saved to $RUNNING_DIR/chroma/"
else
    echo "[ERROR] Chroma container is not running! Cannot backup vector database."
    exit 1
fi

# 4. Create single archive
echo "Packaging backup assets..."
tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" -C "$BACKUP_DIR" "$TIMESTAMP"
rm -rf "$RUNNING_DIR"

# 5. Retain only last 30 days of archives
echo "Cleaning up backups older than 30 days..."
find "$BACKUP_DIR" -name "backup_*.tar.gz" -type f -mtime +30 -delete

echo "========================================="
echo "SUCCESS: Backup completed: $BACKUP_DIR/backup_$TIMESTAMP.tar.gz"
echo "========================================="
