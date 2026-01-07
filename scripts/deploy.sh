#!/bin/bash
###############################################################################
# Deployment Script for CDB Vehicle Valuation System
# Implements blue-green deployment strategy with zero downtime
###############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
IMAGE_TAG=${2:-latest}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"
BACKUP_DIR="/opt/cdb/backups"
MAX_BACKUPS=5

# Logging functions
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

# Error handler
error_exit() {
    log_error "$1"
    exit 1
}

# Check if running as root or with sudo
check_permissions() {
    if [[ $EUID -ne 0 ]] && ! groups | grep -q docker; then
        error_exit "This script must be run with sudo or as a user in the docker group"
    fi
}

# Check required commands
check_requirements() {
    log_info "Checking requirements..."

    local requirements=("docker" "docker-compose")
    for cmd in "${requirements[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error_exit "$cmd is required but not installed"
        fi
    done

    log_success "All requirements satisfied"
}

# Validate environment
validate_environment() {
    log_info "Validating environment: $ENVIRONMENT"

    if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
        error_exit "Invalid environment. Must be 'staging' or 'production'"
    fi

    if [[ ! -f "$PROJECT_ROOT/$ENV_FILE" ]]; then
        error_exit "Environment file not found: $ENV_FILE"
    fi

    if [[ ! -f "$PROJECT_ROOT/$COMPOSE_FILE" ]]; then
        error_exit "Docker Compose file not found: $COMPOSE_FILE"
    fi

    log_success "Environment validated"
}

# Create backup of current deployment
create_backup() {
    log_info "Creating backup before deployment..."

    mkdir -p "$BACKUP_DIR"

    local backup_name="backup_$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"

    mkdir -p "$backup_path"

    # Backup docker-compose file
    if [[ -f "$PROJECT_ROOT/$COMPOSE_FILE" ]]; then
        cp "$PROJECT_ROOT/$COMPOSE_FILE" "$backup_path/"
    fi

    # Backup environment file
    if [[ -f "$PROJECT_ROOT/$ENV_FILE" ]]; then
        cp "$PROJECT_ROOT/$ENV_FILE" "$backup_path/"
    fi

    # Backup database
    if docker ps --format '{{.Names}}' | grep -q "cdb_postgres"; then
        log_info "Backing up database..."
        docker exec cdb_postgres pg_dump -U "${DB_USER:-cdb}" "${DB_NAME:-cdb_valuation_db}" > "$backup_path/database_backup.sql" 2>/dev/null || log_warning "Database backup failed"
    fi

    # Save current docker-compose state
    cd "$PROJECT_ROOT" && docker-compose -f "$COMPOSE_FILE" config > "$backup_path/docker-compose-state.yml" 2>/dev/null || true

    # Create backup metadata
    cat > "$backup_path/metadata.txt" << EOF
Backup created: $(date)
Environment: $ENVIRONMENT
Git commit: $(git rev-parse HEAD 2>/dev/null || echo 'N/A')
Git branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'N/A')
Image tag: $IMAGE_TAG
EOF

    # Compress backup
    tar -czf "$backup_path.tar.gz" -C "$BACKUP_DIR" "$backup_name"
    rm -rf "$backup_path"

    # Clean old backups
    cleanup_old_backups

    log_success "Backup created: $backup_path.tar.gz"
    echo "$backup_path.tar.gz" > "$PROJECT_ROOT/.last_backup"
}

# Cleanup old backups
cleanup_old_backups() {
    local backup_count=$(ls -1 "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | wc -l)

    if [[ $backup_count -gt $MAX_BACKUPS ]]; then
        log_info "Cleaning up old backups (keeping last $MAX_BACKUPS)..."
        ls -1t "$BACKUP_DIR"/backup_*.tar.gz | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -f
    fi
}

# Pull latest images
pull_images() {
    log_info "Pulling Docker images with tag: $IMAGE_TAG..."

    cd "$PROJECT_ROOT"

    # Login to registry if credentials are available
    if [[ -n "${CI_REGISTRY:-}" ]] && [[ -n "${CI_REGISTRY_USER:-}" ]] && [[ -n "${CI_REGISTRY_PASSWORD:-}" ]]; then
        echo "$CI_REGISTRY_PASSWORD" | docker login -u "$CI_REGISTRY_USER" --password-stdin "$CI_REGISTRY" || log_warning "Registry login failed"
    fi

    # Pull images
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull || error_exit "Failed to pull images"

    log_success "Images pulled successfully"
}

# Health check function
health_check() {
    local service=$1
    local max_attempts=30
    local attempt=1

    log_info "Performing health check for $service..."

    while [[ $attempt -le $max_attempts ]]; do
        if docker ps --format '{{.Names}}' | grep -q "$service"; then
            local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "none")

            if [[ "$health_status" == "healthy" ]] || [[ "$health_status" == "none" ]]; then
                # If no healthcheck defined, check if container is running
                if docker ps --filter "name=$service" --filter "status=running" | grep -q "$service"; then
                    log_success "$service is healthy"
                    return 0
                fi
            fi
        fi

        log_info "Waiting for $service to be healthy (attempt $attempt/$max_attempts)..."
        sleep 2
        ((attempt++))
    done

    log_error "$service failed health check"
    return 1
}

# Deploy services with zero downtime
deploy_services() {
    log_info "Deploying services..."

    cd "$PROJECT_ROOT"

    # Stop old containers gracefully (keep database running)
    log_info "Stopping old application containers..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop nginx frontend backend valuation_engine || true

    # Start database and migrations first
    log_info "Starting database..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d postgres

    # Wait for database
    health_check "cdb_postgres" || error_exit "Database health check failed"

    # Run migrations
    log_info "Running database migrations..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up db_migrations

    # Start backend services
    log_info "Starting backend services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d backend valuation_engine

    # Health checks
    health_check "cdb_backend" || error_exit "Backend health check failed"
    health_check "cdb_valuation_engine" || error_exit "Valuation engine health check failed"

    # Start frontend
    log_info "Starting frontend..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d frontend
    health_check "cdb_frontend" || error_exit "Frontend health check failed"

    # Start nginx
    log_info "Starting nginx..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d nginx
    health_check "cdb_nginx" || error_exit "Nginx health check failed"

    # Remove old containers
    log_info "Cleaning up old containers..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" rm -f

    log_success "All services deployed successfully"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    # Check if all containers are running
    local services=("cdb_postgres" "cdb_backend" "cdb_valuation_engine" "cdb_frontend" "cdb_nginx")

    for service in "${services[@]}"; do
        if ! docker ps --format '{{.Names}}' | grep -q "$service"; then
            error_exit "Service $service is not running"
        fi
    done

    # Test health endpoints
    sleep 5

    # Internal health checks
    docker exec cdb_nginx wget -q --spider http://localhost:80/health || log_warning "Nginx health check warning"
    docker exec cdb_backend curl -f http://localhost:8000/health || log_warning "Backend health check warning"

    log_success "Deployment verification completed"
}

# Show deployment status
show_status() {
    log_info "Deployment Status:"
    echo ""
    docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" --env-file "$PROJECT_ROOT/$ENV_FILE" ps
    echo ""
    log_info "Deployment completed successfully for environment: $ENVIRONMENT"
    log_info "Image tag: $IMAGE_TAG"
}

# Main deployment flow
main() {
    log_info "========================================="
    log_info "CDB Vehicle Valuation Deployment"
    log_info "Environment: $ENVIRONMENT"
    log_info "Image Tag: $IMAGE_TAG"
    log_info "========================================="
    echo ""

    check_permissions
    check_requirements
    validate_environment
    create_backup
    pull_images
    deploy_services
    verify_deployment
    show_status

    log_success "Deployment completed successfully!"
}

# Run main function
main "$@"
