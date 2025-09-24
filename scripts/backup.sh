#!/bin/sh
# PostgreSQL backup script for SICETAC database

# Configuration
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-sicetac_db}"
DB_USER="${DB_USER:-sicetac_user}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Generate backup filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/sicetac_backup_${TIMESTAMP}.sql.gz"

echo "Starting backup at $(date)"
echo "Backing up database ${DB_NAME} to ${BACKUP_FILE}"

# Perform backup using pg_dump and compress with gzip
pg_dump -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --no-password \
        --verbose \
        --format=plain \
        --clean \
        --if-exists \
        --no-owner \
        --no-privileges | gzip > "${BACKUP_FILE}"

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Backup completed successfully at $(date)"

    # Get file size
    FILE_SIZE=$(ls -lh "${BACKUP_FILE}" | awk '{print $5}')
    echo "Backup file size: ${FILE_SIZE}"

    # Remove old backups
    echo "Removing backups older than ${RETENTION_DAYS} days"
    find "${BACKUP_DIR}" -name "sicetac_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete

    # List remaining backups
    echo "Current backups:"
    ls -lh "${BACKUP_DIR}"/sicetac_backup_*.sql.gz 2>/dev/null || echo "No backups found"
else
    echo "Backup failed at $(date)" >&2
    exit 1
fi

echo "Backup process completed at $(date)"