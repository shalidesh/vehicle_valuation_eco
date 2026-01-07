# CDB Vehicle Valuation - Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the CDB Vehicle Valuation system on a Linux-based on-premises server using Docker containers.

## Architecture

```
Internet → Nginx (Port 80/443)
            ├── / → Frontend (Next.js)
            ├── /backend/ → Backend API (FastAPI)
            └── /api/ → Valuation Engine (AI Service)
                         ↓
                    PostgreSQL Database
```

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ or CentOS 8+ recommended)
- **CPU**: Minimum 4 cores (8+ recommended for production)
- **RAM**: Minimum 8GB (16GB+ recommended)
- **Disk**: Minimum 50GB free space
- **Network**: Static IP address configured

### Software Requirements
```bash
# Docker
Docker Engine 20.10+
Docker Compose 2.0+

# Optional but recommended
Git (for source control)
UFW or firewalld (for firewall)
```

## Installation Steps

### 1. Install Docker and Docker Compose

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 2. Prepare the Application

```bash
# Create application directory
sudo mkdir -p /opt/cdb-valuation
cd /opt/cdb-valuation

# Copy your application files to this directory
# Or clone from repository:
# git clone <your-repo-url> .

# Set proper permissions
sudo chown -R $USER:$USER /opt/cdb-valuation
```

### 3. Configure Environment Variables

```bash
# Copy environment template
cp .env.prod.example .env.prod

# Edit with secure values
nano .env.prod
```

**Important**: Update these values in `.env.prod`:
- `DB_PASSWORD`: Strong database password
- `BACKEND_SECRET_KEY`: Generate with `openssl rand -hex 32`
- `VALUATION_PASSWORD`: Strong password for valuation engine
- `CORS_ORIGINS`: Your domain(s)
- `NEXT_PUBLIC_API_URL`: Your domain URL

### 4. Configure Nginx

```bash
# Use production nginx configuration
cp nginx.prod.conf nginx.conf

# If you have SSL certificates, update nginx.conf:
# - Uncomment SSL lines (listen 443, ssl_certificate, etc.)
# - Update certificate paths
# - Place certificates in project root or specify custom path
```

### 5. Prepare Data Files

```bash
# Create postgres_data directory if it doesn't exist
mkdir -p postgres_data

# Ensure CSV files are present:
# - postgres_data/master_table_scraped.csv
# - postgres_data/model_mapped.csv
```

### 6. Build and Start Services

```bash
# Build images (first time only)
docker-compose --env-file .env.prod -f docker-compose.prod.yml build

# Start all services
docker-compose --env-file .env.prod -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### 7. Verify Deployment

```bash
# Check all containers are running
docker ps

# Test endpoints
curl http://localhost/health                    # Nginx health
curl http://localhost/backend/health            # Backend health
curl http://localhost/api/health                # Valuation engine health

# Access services:
# - Web Portal: http://your-server-ip
# - Backend API Docs: http://your-server-ip/backend/docs
```

## Firewall Configuration

### Ubuntu (UFW)
```bash
# Enable firewall
sudo ufw enable

# Allow SSH (important!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status verbose
```

### CentOS (firewalld)
```bash
# Enable firewall
sudo systemctl enable --now firewalld

# Allow HTTP and HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https

# Reload firewall
sudo firewall-cmd --reload

# Check status
sudo firewall-cmd --list-all
```

## SSL/TLS Configuration (HTTPS)

### Option 1: Let's Encrypt (Free SSL)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate (with nginx running)
sudo certbot certonly --nginx -d your-domain.com

# Certificates will be in: /etc/letsencrypt/live/your-domain.com/

# Update docker-compose.prod.yml to mount certificates:
# Add to nginx service volumes:
#   - /etc/letsencrypt:/etc/letsencrypt:ro

# Update nginx.conf to use certificates
# Uncomment SSL lines and update paths
```

### Option 2: Corporate Certificates

```bash
# Create certificates directory
mkdir -p ssl_certificates

# Copy your certificates
cp your-cert.crt ssl_certificates/
cp your-cert.key ssl_certificates/
cp ca-bundle.crt ssl_certificates/

# Update docker-compose.prod.yml nginx volumes
# Update nginx.conf SSL paths
```

## Maintenance Commands

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f valuation_engine
```

### Restart Services
```bash
# Restart all
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend
```

### Update Application
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose --env-file .env.prod -f docker-compose.prod.yml up -d --build

# Or rebuild specific service
docker-compose --env-file .env.prod -f docker-compose.prod.yml up -d --build backend
```

### Database Backup
```bash
# Create backup
docker exec cdb_postgres pg_dump -U airflow airflow > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker exec -i cdb_postgres psql -U airflow airflow < backup_20241217_120000.sql
```

### Stop Services
```bash
# Stop all services
docker-compose -f docker-compose.prod.yml stop

# Stop and remove containers (data persists)
docker-compose -f docker-compose.prod.yml down

# Stop and remove everything including volumes (DANGEROUS!)
docker-compose -f docker-compose.prod.yml down -v
```

## Scaling Services

### Scale Valuation Engine
```bash
# Edit docker-compose.prod.yml, uncomment under valuation_engine:
# deploy:
#   replicas: 2

# Restart
docker-compose --env-file .env.prod -f docker-compose.prod.yml up -d --scale valuation_engine=2
```

### Scale Backend
```bash
# Similar approach for backend service
docker-compose --env-file .env.prod -f docker-compose.prod.yml up -d --scale backend=2
```

## Monitoring

### Resource Usage
```bash
# Real-time monitoring
docker stats

# Disk usage
docker system df
docker volume ls
```

### Health Checks
```bash
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# Inspect specific container
docker inspect cdb_backend | grep -A 10 Health
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs service_name

# Check container status
docker ps -a

# Inspect container
docker inspect container_name

# Restart specific service
docker-compose -f docker-compose.prod.yml restart service_name
```

### Database Connection Issues
```bash
# Check postgres is running
docker ps | grep postgres

# Test database connection
docker exec cdb_postgres psql -U airflow -d airflow -c "SELECT 1;"

# Check database logs
docker logs cdb_postgres
```

### Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER /opt/cdb-valuation

# Fix log directories
docker exec cdb_backend chown -R appuser:appuser /app/logs
```

### Clear and Rebuild
```bash
# Stop and remove everything
docker-compose -f docker-compose.prod.yml down

# Remove dangling images
docker image prune -a

# Rebuild from scratch
docker-compose --env-file .env.prod -f docker-compose.prod.yml build --no-cache
docker-compose --env-file .env.prod -f docker-compose.prod.yml up -d
```

## API Endpoints

After deployment, the following endpoints will be available:

### Frontend
- **Web Portal**: `http://your-server/`

### Backend API (FastAPI)
- **API Root**: `http://your-server/backend/`
- **API Docs**: `http://your-server/backend/docs`
- **Health Check**: `http://your-server/backend/health`
- **Authentication**: `http://your-server/backend/auth/`
- **Vehicles**: `http://your-server/backend/vehicles/`
- **Analytics**: `http://your-server/backend/analytics/`
- **Mapping**: `http://your-server/backend/mapping/`

### Valuation Engine (AI Service)
- **API Root**: `http://your-server/api/`
- **Predict Endpoint**: `http://localhost:8443/api/predict` (via Nginx proxy)
- **Health Check**: `http://your-server/api/health`

## Production Best Practices

1. **Security**
   - Change all default passwords
   - Use strong SECRET_KEY values
   - Enable HTTPS with valid certificates
   - Regular security updates
   - Secure database access with strong credentials

2. **Backups**
   - Schedule daily database backups
   - Store backups off-server
   - Test restore procedures regularly

3. **Monitoring**
   - Set up log aggregation
   - Monitor disk space
   - Track container resource usage
   - Configure alerts for service failures

4. **Updates**
   - Test updates in staging environment first
   - Maintain rollback procedures
   - Document all changes

5. **Performance**
   - Scale services based on load
   - Monitor response times
   - Optimize database queries
   - Use CDN for static assets

6. **Database Management**
   - Use direct PostgreSQL client tools for database management
   - Consider installing pgAdmin locally if GUI access needed
   - Use SSH tunnel for secure remote database access

## Support

For issues or questions:
1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Review this guide
3. Contact system administrator
4. Check application documentation

## Quick Reference Card

```bash
# Start services
docker-compose --env-file .env.prod -f docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker-compose.prod.yml stop

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart service
docker-compose -f docker-compose.prod.yml restart backend

# Check status
docker ps

# Backup database
docker exec cdb_postgres pg_dump -U airflow airflow > backup.sql

# Update application
git pull && docker-compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```
