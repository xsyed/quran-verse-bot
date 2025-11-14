#!/bin/bash

###############################################################################
# Quran Bot Database Backup Script
# Description: Backs up quran.db from Docker volume to external backup folder
# Usage: ./backup_db.sh
###############################################################################

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
DB_SOURCE="$PROJECT_DIR/data/quran.db"
BACKUP_DIR="$(dirname "$PROJECT_DIR")/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILENAME="quran_backup_${TIMESTAMP}.db"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILENAME"

# Maximum number of backups to keep (optional, set to 0 to disable)
MAX_BACKUPS=30

###############################################################################
# Functions
###############################################################################

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory if it doesn't exist
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log_info "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
        if [ $? -ne 0 ]; then
            log_error "Failed to create backup directory"
            exit 1
        fi
    fi
}

# Check if source database exists
check_source_db() {
    if [ ! -f "$DB_SOURCE" ]; then
        log_error "Source database not found: $DB_SOURCE"
        log_error "Make sure your bot has created the database file"
        exit 1
    fi
}

# Perform the backup
perform_backup() {
    log_info "Starting backup process..."
    log_info "Source: $DB_SOURCE"
    log_info "Destination: $BACKUP_PATH"

    # Copy the database file
    cp "$DB_SOURCE" "$BACKUP_PATH"

    if [ $? -eq 0 ]; then
        # Get file size
        FILE_SIZE=$(ls -lh "$BACKUP_PATH" | awk '{print $5}')
        log_info "Backup completed successfully!"
        log_info "Backup file: $BACKUP_FILENAME"
        log_info "Size: $FILE_SIZE"

        # Create a symlink to latest backup
        ln -sf "$BACKUP_FILENAME" "$BACKUP_DIR/latest.db"

        return 0
    else
        log_error "Backup failed!"
        return 1
    fi
}

# Clean up old backups (keep only MAX_BACKUPS most recent)
cleanup_old_backups() {
    if [ $MAX_BACKUPS -gt 0 ]; then
        BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/quran_backup_*.db 2>/dev/null | wc -l)

        if [ $BACKUP_COUNT -gt $MAX_BACKUPS ]; then
            log_warn "Found $BACKUP_COUNT backups, keeping only $MAX_BACKUPS most recent"

            # Delete old backups
            ls -1t "$BACKUP_DIR"/quran_backup_*.db | tail -n +$((MAX_BACKUPS + 1)) | while read file; do
                log_info "Removing old backup: $(basename "$file")"
                rm "$file"
            done
        fi
    fi
}

# Display backup summary
show_summary() {
    log_info "=== Backup Summary ==="
    log_info "Total backups in directory: $(ls -1 "$BACKUP_DIR"/quran_backup_*.db 2>/dev/null | wc -l)"
    log_info "Latest backup: $BACKUP_FILENAME"

    # Show disk usage
    TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | awk '{print $1}')
    log_info "Total backup size: $TOTAL_SIZE"
}

###############################################################################
# Main Script
###############################################################################

log_info "=== Quran Bot Database Backup ==="
log_info "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"

# Run backup steps
create_backup_dir
check_source_db
perform_backup

if [ $? -eq 0 ]; then
    cleanup_old_backups
    show_summary
    log_info "Backup process completed successfully!"
    exit 0
else
    log_error "Backup process failed!"
    exit 1
fi
