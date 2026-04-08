#!/bin/bash
# -----------------------------------------
# FastAPI + Docker volume backup script
# Backs up:
#   - demo_app_db volume (SQLite DB)
#   - backend/data folder
# -----------------------------------------

set -e

### CONFIG ###
VOLUME_NAME="demo_app_db"        # ✅ YOUR REAL DB VOLUME
BACKEND_DATA_DIR="./backend/data"
BACKUP_DIR="./backup"
MAX_BACKUPS=7
DATE=$(date +%F_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup-${DATE}.tar.gz"
OLDER_DIR="${BACKUP_DIR}/older"
################

echo "Using volume: $VOLUME_NAME"

mkdir -p "$BACKUP_DIR"
mkdir -p "$OLDER_DIR"

TMP_DIR=$(mktemp -d)

echo "Temporary dir: $TMP_DIR"

# -----------------------------
# Copy backend data
# -----------------------------
if [ -d "$BACKEND_DATA_DIR" ]; then
  echo "Backing up backend data..."
  cp -r "$BACKEND_DATA_DIR" "$TMP_DIR/backend_data"
fi

# -----------------------------
# Copy Docker volume safely
# -----------------------------
echo "Backing up docker volume..."
docker run --rm \
  -v ${VOLUME_NAME}:/data:ro \
  -v ${TMP_DIR}:/backup_tmp \
  alpine \
  sh -c "cp -a /data /backup_tmp/app_db"

# -----------------------------
# Create tar.gz
# -----------------------------
echo "Creating archive..."
tar czf "$BACKUP_FILE" -C "$TMP_DIR" .

rm -rf "$TMP_DIR"

echo "✅ Backup created:"
echo "$BACKUP_FILE"

# -----------------------------
# Rotate old backups
# -----------------------------
BACKUPS=($(ls -1t ${BACKUP_DIR}/backup-*.tar.gz 2>/dev/null || true))
NUM=${#BACKUPS[@]}

if [ $NUM -gt $MAX_BACKUPS ]; then
  for ((i=MAX_BACKUPS; i<NUM; i++)); do
    mv "${BACKUPS[$i]}" "$OLDER_DIR/"
    echo "Moved old backup: ${BACKUPS[$i]}"
  done
fi

echo "Done."
