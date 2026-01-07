#!/bin/bash
###############################################################################
# Rollback Script for CDB Vehicle Valuation System
# Restores system to previous working state using backups
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
BACKUP_FILE="${1:-}"

# Logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

error_exit() {
    log_error "$1"
    exit 1
}

# Find latest backup if not specified
find_latest_backup() {
    if [[ -z "$BACKUP_FILE" ]]; then
        # Check for .last_backup file
        if [[ -f "$PROJECT_ROOT/.last_backup" ]]; then
            BACKUP_FILE=$(cat "$PROJECT_ROOT/.last_backup")
            log_info "Using backup from .last_backup: $BACKUP_FILE"
        else
            # Find the most recent backup
            BACKUP_FILE=$(ls -t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | head -1)
            if [[ -z "$BACKUP_FILE" ]]; then
                error_exit "No backup files found in $BACKUP_DIR"
            fi
            log_info "Using latest backup: $BACKUP_FILE"
        fi
    fi
}

# Validate backup file
validate_backup() {
    log_info "Validating backup file..."

    if [[ ! -f "$BACKUP_FILE" ]]; then
        error_exit "Backup file not found: $BACKUP_FILE"
    fi

    if ! tar -tzf "$BACKUP_FILE" > /dev/null 2>&1; then
        error_exit "Backup file is corrupted or invalid"
    fi

    log_success "Backup file validated"
}

# Confirm rollback
confirm_rollback() {
    echo ""
    log_warning "You are about to rollback the system to a previous state"
    log_info "Backup file: $BACKUP_FILE"
    echo ""

    # Extract and show backup metadata
    local temp_dir=$(mktemp -d)
    tar -xzf "$BACKUP_FILE" -C "$temp_dir"
    local backup_name=$(basename "$BACKUP_FILE" .tar.gz)

    if [[ -f "$temp_dir/$backup_name/metadata.txt" ]]; then
        cat "$temp_dir/$backup_name/metadata.txt"
    fi

    rm -rf "$temp_dir"
    echo ""

    read -p "Do you want to proceed with the rollback? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Rollback cancelled by user"
        exit 0
    fi
}

# Create safety backup before rollback
create_safety_backup() {
    log_info "Creating safety backup before rollback..."
    bash "$SCRIPT_DIR/backup.sh" || log_warning "Safety backup failed"
}

# Stop current services
stop_services() {
    log_info "Stopping current services..."

    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.prod.yml --env-file .env.prod down || log_warning "Some services failed to stop gracefully"

    log_success "Services stopped"
}

# Extract backup
extract_backup() {
    log_info "Extracting backup..."

    local temp_dir=$(mktemp -d)
    tar -xzf "$BACKUP_FILE" -C "$temp_dir"
    local backup_name=$(basename "$BACKUP_FILE" .tar.gz)

    # Restore configuration files
    if [[ -f "$temp_dir/$backup_name/docker-compose.prod.yml" ]]; then
        cp "$temp_dir/$backup_name/docker-compose.prod.yml" "$PROJECT_ROOT/"
        log_success "Docker compose file restored"
    fi

    # Restore nginx config
    if [[ -f "$temp_dir/$backup_name/nginx.conf" ]]; then
        cp "$temp_dir/$backup_name/nginx.conf" "$PROJECT_ROOT/"
        log_success "Nginx configuration restored"
    fi

    echo "$temp_dir/$backup_name" > /tmp/rollback_temp_dir
    log_success "Backup extracted"
}

# Restore database
restore_database() {
    log_info "Restoring database..."

    local temp_dir=$(cat /tmp/rollback_temp_dir)

    # Start database container
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d postgres

    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 10

    # Restore database from SQL dump
    if [[ -f "$temp_dir/database_backup.sql.gz" ]]; then
        gunzip -c "$temp_dir/database_backup.sql.gz" | docker exec -i cdb_postgres psql -U "${DB_USER:-cdb}" -d "${DB_NAME:-cdb_valuation_db}"
        log_success "Database restored from backup"
    elif [[ -f "$temp_dir/database_backup.sql" ]]; then
        cat "$temp_dir/database_backup.sql" | docker exec -i cdb_postgres psql -U "${DB_USER:-cdb}" -d "${DB_NAME:-cdb_valuation_db}"
        log_success "Database restored from backup"
    else
        log_warning "No database backup found in backup file"
    fi
}

# Restore docker volumes
restore_volumes() {
    log_info "Restoring Docker volumes..."

    local temp_dir=$(cat /tmp/rollback_temp_dir)
    local volumes=("postgres_data" "backend_logs" "valuation_logs")

    for volume in "${volumes[@]}"; do
        if [[ -f "$temp_dir/${volume}_backup.tar.gz" ]]; then
            local full_volume_name="vehicle_valuation_version_02_$volume"

            log_info "Restoring volume: $full_volume_name"

            # Remove existing volume
            docker volume rm "$full_volume_name" 2>/dev/null || true

            # Create new volume
            docker volume create "$full_volume_name"

            # Restore data
            docker run --rm \
                -v "$full_volume_name:/data" \
                -v "$temp_dir:/backup:ro" \
                alpine sh -c "cd /data && tar xzf /backup/${volume}_backup.tar.gz"

            log_success "Volume $full_volume_name restored"
        fi
    done
}

# Start services
start_services() {
    log_info "Starting services..."

    cd "$PROJECT_ROOT"

    # Start all services
    docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 20

    # Check service status
    docker-compose -f docker-compose.prod.yml --env-file .env.prod ps

    log_success "Services started"
}

# Verify rollback
verify_rollback() {
    log_info "Verifying rollback..."

    # Check if containers are running
    local services=("cdb_postgres" "cdb_backend" "cdb_frontend" "cdb_nginx")
    local all_running=true

    for service in "${services[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "$service"; then
            log_success "$service is running"
        else
            log_error "$service is not running"
            all_running=false
        fi
    done

    if $all_running; then
        log_success "Rollback verification completed"
    else
        log_error "Rollback verification failed - some services are not running"
        return 1
    fi
}

# Cleanup temporary files
cleanup() {
    if [[ -f /tmp/rollback_temp_dir ]]; then
        local temp_dir=$(cat /tmp/rollback_temp_dir)
        rm -rf "$temp_dir"
        rm /tmp/rollback_temp_dir
    fi
}

# Main execution
main() {
    log_info "========================================="
    log_info "CDB Vehicle Valuation Rollback"
    log_info "========================================="
    echo ""

    find_latest_backup
    validate_backup
    confirm_rollback
    create_safety_backup
    stop_services
    extract_backup
    restore_database
    restore_volumes
    start_services
    verify_rollback
    cleanup

    echo ""
    log_success "Rollback completed successfully!"
    log_info "System has been restored to: $BACKUP_FILE"
}

# Run main
trap cleanup EXIT
main "$@"
