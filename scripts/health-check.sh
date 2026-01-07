#!/bin/bash
###############################################################################
# Health Check Script for CDB Vehicle Valuation System
# Monitors service health and alerts on issues
###############################################################################

set -e
set -u

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HEALTH_LOG="/var/log/cdb-health-check.log"

# Exit codes
EXIT_SUCCESS=0
EXIT_WARNING=1
EXIT_ERROR=2

# Logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$HEALTH_LOG"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$HEALTH_LOG"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1" | tee -a "$HEALTH_LOG"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" | tee -a "$HEALTH_LOG"
}

# Initialize counters
total_checks=0
passed_checks=0
failed_checks=0
warning_checks=0

# Check if container is running
check_container() {
    local container_name=$1
    local service_name=$2

    ((total_checks++))

    if docker ps --format '{{.Names}}' | grep -q "$container_name"; then
        # Check health status
        local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "none")

        if [[ "$health_status" == "healthy" ]] || [[ "$health_status" == "none" ]]; then
            log_success "$service_name is running and healthy"
            ((passed_checks++))
            return 0
        elif [[ "$health_status" == "starting" ]]; then
            log_warning "$service_name is starting..."
            ((warning_checks++))
            return 1
        else
            log_error "$service_name is unhealthy (status: $health_status)"
            ((failed_checks++))
            return 2
        fi
    else
        log_error "$service_name is not running"
        ((failed_checks++))
        return 2
    fi
}

# Check HTTP endpoint
check_http_endpoint() {
    local endpoint=$1
    local service_name=$2

    ((total_checks++))

    if curl -f -s -o /dev/null -w "%{http_code}" "$endpoint" | grep -q "200"; then
        log_success "$service_name HTTP endpoint is responding ($endpoint)"
        ((passed_checks++))
        return 0
    else
        log_error "$service_name HTTP endpoint is not responding ($endpoint)"
        ((failed_checks++))
        return 2
    fi
}

# Check database connection
check_database() {
    ((total_checks++))

    if docker exec cdb_postgres pg_isready -U "${DB_USER:-cdb}" > /dev/null 2>&1; then
        # Check database size
        local db_size=$(docker exec cdb_postgres psql -U "${DB_USER:-cdb}" -d "${DB_NAME:-cdb_valuation_db}" -t -c "SELECT pg_size_pretty(pg_database_size('${DB_NAME:-cdb_valuation_db}'));" 2>/dev/null | xargs)

        log_success "Database is accepting connections (size: $db_size)"
        ((passed_checks++))
        return 0
    else
        log_error "Database is not accepting connections"
        ((failed_checks++))
        return 2
    fi
}

# Check disk space
check_disk_space() {
    ((total_checks++))

    local usage=$(df -h "$PROJECT_ROOT" | awk 'NR==2 {print $5}' | sed 's/%//')

    if [[ $usage -lt 80 ]]; then
        log_success "Disk space is adequate ($usage% used)"
        ((passed_checks++))
        return 0
    elif [[ $usage -lt 90 ]]; then
        log_warning "Disk space is getting low ($usage% used)"
        ((warning_checks++))
        return 1
    else
        log_error "Disk space is critically low ($usage% used)"
        ((failed_checks++))
        return 2
    fi
}

# Check Docker volume sizes
check_volume_sizes() {
    ((total_checks++))

    local volumes=("vehicle_valuation_version_02_postgres_data" "vehicle_valuation_version_02_backend_logs")

    for volume in "${volumes[@]}"; do
        if docker volume ls --format '{{.Name}}' | grep -q "$volume"; then
            local size=$(docker run --rm -v "$volume:/data:ro" alpine du -sh /data 2>/dev/null | awk '{print $1}')
            log_success "Volume $volume size: $size"
        fi
    done

    ((passed_checks++))
    return 0
}

# Check system resources
check_system_resources() {
    ((total_checks++))

    # Check memory
    local mem_usage=$(free | grep Mem | awk '{print int($3/$2 * 100)}')

    if [[ $mem_usage -lt 90 ]]; then
        log_success "Memory usage is normal ($mem_usage%)"
    else
        log_warning "Memory usage is high ($mem_usage%)"
        ((warning_checks++))
    fi

    # Check CPU (last 1 minute average)
    local cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    log_info "System load average (1 min): $cpu_load"

    ((passed_checks++))
    return 0
}

# Check logs for errors
check_logs_for_errors() {
    ((total_checks++))

    local containers=("cdb_backend" "cdb_frontend" "cdb_valuation_engine")
    local error_count=0

    for container in "${containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "$container"; then
            local errors=$(docker logs --since=5m "$container" 2>&1 | grep -i "error\|exception\|fatal" | wc -l)

            if [[ $errors -gt 0 ]]; then
                log_warning "$container has $errors error(s) in the last 5 minutes"
                ((error_count++))
            fi
        fi
    done

    if [[ $error_count -eq 0 ]]; then
        log_success "No recent errors in application logs"
        ((passed_checks++))
        return 0
    else
        log_warning "Found errors in application logs"
        ((warning_checks++))
        return 1
    fi
}

# Generate health report
generate_report() {
    echo ""
    echo "========================================="
    echo "Health Check Summary"
    echo "========================================="
    echo "Total Checks: $total_checks"
    echo -e "${GREEN}Passed: $passed_checks${NC}"
    echo -e "${YELLOW}Warnings: $warning_checks${NC}"
    echo -e "${RED}Failed: $failed_checks${NC}"
    echo "========================================="
    echo ""

    # Determine overall status
    if [[ $failed_checks -eq 0 ]] && [[ $warning_checks -eq 0 ]]; then
        log_success "System is healthy"
        return $EXIT_SUCCESS
    elif [[ $failed_checks -eq 0 ]]; then
        log_warning "System has warnings but is operational"
        return $EXIT_WARNING
    else
        log_error "System has critical issues"
        return $EXIT_ERROR
    fi
}

# Main execution
main() {
    log_info "========================================="
    log_info "CDB Vehicle Valuation Health Check"
    log_info "========================================="
    echo ""

    # Container checks
    echo "Checking Containers..."
    check_container "cdb_postgres" "PostgreSQL Database"
    check_container "cdb_backend" "Backend API"
    check_container "cdb_valuation_engine" "Valuation Engine"
    check_container "cdb_frontend" "Frontend Application"
    check_container "cdb_nginx" "Nginx Reverse Proxy"
    echo ""

    # Database checks
    echo "Checking Database..."
    check_database
    echo ""

    # HTTP endpoint checks
    echo "Checking HTTP Endpoints..."
    check_http_endpoint "http://localhost:80/health" "Nginx"
    check_http_endpoint "http://localhost:8000/health" "Backend"
    check_http_endpoint "http://localhost:3000" "Frontend"
    echo ""

    # System resource checks
    echo "Checking System Resources..."
    check_disk_space
    check_volume_sizes
    check_system_resources
    echo ""

    # Log checks
    echo "Checking Application Logs..."
    check_logs_for_errors
    echo ""

    # Generate and return report
    generate_report
    return $?
}

# Run main
main "$@"
exit_code=$?
exit $exit_code
