#!/bin/bash
###############################################################################
# Backup Script for CDB Vehicle Valuation System
# Creates backups of database, configurations, and docker volumes
###############################################################################

set -e
set -u
set -o pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="/opt/cdb/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
MAX_BACKUPS=10

# Logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Create backup directory
create_backup_directory() {
    log_info "Creating backup directory: $BACKUP_PATH"
    mkdir -p "$BACKUP_PATH"
}

# Backup database
backup_database() {
    log_info "Backing up PostgreSQL database..."

    if docker ps --format '{{.Names}}' | grep -q "cdb_postgres"; then
        # Get database credentials from env file or use defaults
        local db_user="${DB_USER:-cdb}"
        local db_name="${DB_NAME:-cdb_valuation_db}"

        # Create SQL dump
        docker exec cdb_postgres pg_dump -U "$db_user" "$db_name" > "$BACKUP_PATH/database_backup.sql"

        # Create compressed backup
        gzip "$BACKUP_PATH/database_backup.sql"

        # Export database schema
        docker exec cdb_postgres pg_dump -U "$db_user" --schema-only "$db_name" > "$BACKUP_PATH/schema_backup.sql"

        log_success "Database backup completed"
    else
        log_error "PostgreSQL container not running"
        return 1
    fi
}

# Backup docker volumes
backup_volumes() {
    log_info "Backing up Docker volumes..."

    local volumes=("postgres_data" "backend_logs" "valuation_logs")

    for volume in "${volumes[@]}"; do
        local full_volume_name="vehicle_valuation_version_02_$volume"

        if docker volume ls --format '{{.Name}}' | grep -q "$full_volume_name"; then
            log_info "Backing up volume: $full_volume_name"

            # Create volume backup using temporary container
            docker run --rm \
                -v "$full_volume_name:/data:ro" \
                -v "$BACKUP_PATH:/backup" \
                alpine tar czf "/backup/${volume}_backup.tar.gz" -C /data .

            log_success "Volume $full_volume_name backed up"
        else
            log_info "Volume $full_volume_name not found, skipping"
        fi
    done
}

# Backup configuration files
backup_configurations() {
    log_info "Backing up configuration files..."

    # Backup docker-compose file
    if [[ -f "$PROJECT_ROOT/docker-compose.prod.yml" ]]; then
        cp "$PROJECT_ROOT/docker-compose.prod.yml" "$BACKUP_PATH/"
    fi

    # Backup environment file (without sensitive data)
    if [[ -f "$PROJECT_ROOT/.env.prod" ]]; then
        # Create sanitized version for security
        grep -v "PASSWORD\|SECRET\|TOKEN" "$PROJECT_ROOT/.env.prod" > "$BACKUP_PATH/env.example" || true
    fi

    # Backup nginx configuration
    if [[ -f "$PROJECT_ROOT/nginx.conf" ]]; then
        cp "$PROJECT_ROOT/nginx.conf" "$BACKUP_PATH/"
    fi

    log_success "Configuration files backed up"
}

# Create backup metadata
create_metadata() {
    log_info "Creating backup metadata..."

    cat > "$BACKUP_PATH/metadata.txt" << EOF
===========================================
CDB Vehicle Valuation System - Backup Info
===========================================

Backup Created: $(date)
Backup Name: $BACKUP_NAME
Hostname: $(hostname)
User: $(whoami)

Git Information:
  Commit: $(git -C "$PROJECT_ROOT" rev-parse HEAD 2>/dev/null || echo 'N/A')
  Branch: $(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'N/A')
  Status: $(git -C "$PROJECT_ROOT" status --short 2>/dev/null || echo 'N/A')

Docker Information:
  Compose Version: $(docker-compose --version)
  Docker Version: $(docker --version)

Running Containers:
$(docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' | grep cdb_ || echo 'None')

Database Size: $(docker exec cdb_postgres psql -U ${DB_USER:-cdb} -d ${DB_NAME:-cdb_valuation_db} -c "SELECT pg_size_pretty(pg_database_size('${DB_NAME:-cdb_valuation_db}'));" -t 2>/dev/null || echo 'N/A')

Backup Contents:
$(ls -lh "$BACKUP_PATH")

===========================================
EOF

    log_success "Metadata created"
}

# Compress backup
compress_backup() {
    log_info "Compressing backup..."

    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"

    # Remove uncompressed directory
    rm -rf "$BACKUP_PATH"

    local backup_size=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
    log_success "Backup compressed: ${BACKUP_NAME}.tar.gz ($backup_size)"
}

# Cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups (keeping last $MAX_BACKUPS)..."

    cd "$BACKUP_DIR"
    local backup_count=$(ls -1 backup_*.tar.gz 2>/dev/null | wc -l)

    if [[ $backup_count -gt $MAX_BACKUPS ]]; then
        ls -1t backup_*.tar.gz | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -f
        log_success "Old backups cleaned up"
    else
        log_info "No old backups to clean up"
    fi
}

# Verify backup
verify_backup() {
    log_info "Verifying backup integrity..."

    if tar -tzf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" > /dev/null 2>&1; then
        log_success "Backup integrity verified"
    else
        log_error "Backup integrity check failed"
        return 1
    fi
}

# Main execution
main() {
    log_info "========================================="
    log_info "CDB Vehicle Valuation Backup"
    log_info "========================================="
    echo ""

    create_backup_directory
    backup_database
    backup_volumes
    backup_configurations
    create_metadata
    compress_backup
    verify_backup
    cleanup_old_backups

    echo ""
    log_success "Backup completed successfully!"
    log_info "Backup location: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    log_info "To restore, use: ./scripts/restore.sh $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
}

# Run main
main "$@"
