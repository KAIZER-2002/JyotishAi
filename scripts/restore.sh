#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# JyotishAI - Production System Restoration Script
# ---------------------------------------------------------------------------

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 /path/to/backup_YYYYMMDD_HHMMSS.tar.gz"
    exit 1
fi

BACKUP_ARCHIVE="$1"

if [ ! -f "$BACKUP_ARCHIVE" ]; then
    echo "[ERROR] Backup archive file not found: $BACKUP_ARCHIVE"
    exit 1
fi

echo "========================================="
echo "Starting JyotishAI System Restore"
echo "========================================="

TEMP_DIR=$(mktemp -d)
echo "Extracting archive to temporary workspace: $TEMP_DIR"
tar -xzf "$BACKUP_ARCHIVE" -C "$TEMP_DIR"

# Identify extracted directory name (timestamp)
EXTRACTED_SUBDIR=$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)

if [ -z "$EXTRACTED_SUBDIR" ]; then
    echo "[ERROR] Extracted backup directory structure is invalid."
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "Restoring database snapshot..."
if docker compose ps | grep -q "jyotishai-postgres"; then
    POSTGRES_USER=$(docker compose exec -t postgres printenv POSTGRES_USER | tr -d '\r')
    POSTGRES_DB=$(docker compose exec -t postgres printenv POSTGRES_DB | tr -d '\r')

    # Drop and recreate database to ensure clean load
    echo "Cleaning existing database tables..."
    docker compose exec -t postgres dropdb -U "$POSTGRES_USER" --if-exists "$POSTGRES_DB"
    docker compose exec -t postgres createdb -U "$POSTGRES_USER" "$POSTGRES_DB"

    # Restore from dump
    docker compose exec -i postgres pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v < "$EXTRACTED_SUBDIR/database.dump"
    echo "Database restored successfully."
else
    echo "[ERROR] PostgreSQL container is not running! Start postgres before restoring."
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "Restoring Chroma DB indexes..."
if docker compose ps | grep -q "jyotishai-chroma"; then
    # Clear active chroma volume index files
    docker compose exec -t chroma rm -rf /index_data/* || true
    # Re-inject indexes
    docker compose cp "$EXTRACTED_SUBDIR/chroma/." chroma:/index_data/
    echo "Chroma DB indexes restored successfully."
else
    echo "[ERROR] Chroma container is not running! Start chroma before restoring."
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Clean up
rm -rf "$TEMP_DIR"

echo "========================================="
echo "SUCCESS: System restore completed successfully."
echo "Please restart application containers:"
echo "docker compose restart backend frontend nginx"
echo "========================================="
