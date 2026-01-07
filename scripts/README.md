# Deployment Scripts
## CDB Vehicle Valuation System

This directory contains automation scripts for deployment, backup, rollback, and monitoring.

---

## Scripts Overview

| Script | Purpose | Usage |
|--------|---------|-------|
| `deploy.sh` | Main deployment script with blue-green deployment | `bash deploy.sh <environment> <image-tag>` |
| `backup.sh` | Create full system backup (DB, volumes, configs) | `bash backup.sh` |
| `rollback.sh` | Rollback to previous deployment | `bash rollback.sh [backup-file]` |
| `health-check.sh` | Comprehensive health monitoring | `bash health-check.sh` |

---

## Script Details

### deploy.sh

**Purpose**: Orchestrates zero-downtime deployment using blue-green strategy

**Usage**:
```bash
bash deploy.sh production latest
bash deploy.sh staging v1.2.3
```

**Features**:
- Creates automatic backup before deployment
- Pulls latest Docker images
- Performs rolling updates with health checks
- Verifies deployment success
- Automatic rollback on failure

**Exit Codes**:
- `0`: Successful deployment
- `1`: Deployment failed

---

### backup.sh

**Purpose**: Creates comprehensive backup of the system

**Usage**:
```bash
bash backup.sh
```

**Backup Includes**:
- PostgreSQL database dump (compressed)
- Docker volumes
- Configuration files (sanitized)
- Deployment metadata
- Git commit information

**Backup Location**: `/opt/cdb/backups/backup_YYYYMMDD_HHMMSS.tar.gz`

**Retention**: Keeps last 10 backups automatically

---

### rollback.sh

**Purpose**: Restore system to a previous state

**Usage**:
```bash
# Rollback to last backup
bash rollback.sh

# Rollback to specific backup
bash rollback.sh /opt/cdb/backups/backup_20240115_120000.tar.gz
```

**Process**:
1. Validates backup file integrity
2. Prompts for confirmation
3. Creates safety backup of current state
4. Stops running services
5. Restores configuration, database, and volumes
6. Restarts services
7. Verifies restoration

**Safety**: Always creates a safety backup before rolling back

---

### health-check.sh

**Purpose**: Monitor system health and detect issues

**Usage**:
```bash
bash health-check.sh
```

**Checks**:
- ✓ Container status and health
- ✓ Database connectivity
- ✓ HTTP endpoint availability
- ✓ Disk space usage
- ✓ Memory and CPU usage
- ✓ Recent application errors
- ✓ Docker volume sizes

**Exit Codes**:
- `0`: System healthy
- `1`: Warnings present (non-critical)
- `2`: Critical issues detected

**Log Location**: `/var/log/cdb-health-check.log`

---

## Making Scripts Executable

After cloning the repository, ensure scripts are executable:

```bash
chmod +x scripts/*.sh
```

Or individually:
```bash
chmod +x scripts/deploy.sh
chmod +x scripts/backup.sh
chmod +x scripts/rollback.sh
chmod +x scripts/health-check.sh
```

---

## Automation

### Recommended Cron Jobs

Add to server crontab (`crontab -e`):

```bash
# Health checks every 5 minutes
*/5 * * * * /opt/cdb/vehicle-valuation/scripts/health-check.sh >> /var/log/cdb-health.log 2>&1

# Daily backups at 2 AM
0 2 * * * /opt/cdb/vehicle-valuation/scripts/backup.sh >> /var/log/cdb-backup.log 2>&1

# Weekly Docker cleanup (Sundays at 3 AM)
0 3 * * 0 docker system prune -af --filter "until=168h" >> /var/log/docker-cleanup.log 2>&1

# Monthly backup verification (1st of month at 4 AM)
0 4 1 * * /opt/cdb/vehicle-valuation/scripts/verify-backups.sh >> /var/log/backup-verify.log 2>&1
```

---

## Environment Variables

Scripts read environment variables from `.env.prod` file in the project root.

Required variables:
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name
- `CI_REGISTRY`: Docker registry URL (optional)
- `CI_REGISTRY_USER`: Registry username (optional)
- `CI_REGISTRY_PASSWORD`: Registry password (optional)

---

## Logging

All scripts support logging to both console and log files.

**Log Files**:
- `/var/log/cdb-health-check.log`: Health check results
- `/var/log/cdb-backup.log`: Backup operations
- `/var/log/cdb-deployment.log`: Deployment logs

**Log Rotation**: Configure logrotate for automatic log management:

```bash
# /etc/logrotate.d/cdb-vehicle-valuation
/var/log/cdb-*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 deploy deploy
}
```

---

## Error Handling

All scripts follow these error handling principles:

- Exit immediately on errors (`set -e`)
- Fail on undefined variables (`set -u`)
- Fail on pipe errors (`set -o pipefail`)
- Colorized output for easy reading
- Detailed error messages with timestamps

---

## Security Considerations

1. **Permissions**: Scripts should be owned by `deploy` user
   ```bash
   chown deploy:deploy scripts/*.sh
   ```

2. **Sensitive Data**: Backup script sanitizes environment files to exclude passwords/secrets

3. **SSH Keys**: Never commit SSH keys or credentials to repository

4. **Backup Encryption**: Consider encrypting backup files for sensitive data
   ```bash
   gpg --symmetric --cipher-algo AES256 backup_file.tar.gz
   ```

---

## Troubleshooting

### Script Permission Denied

```bash
chmod +x scripts/deploy.sh
```

### Docker Command Not Found

```bash
# Ensure user is in docker group
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect
```

### Database Connection Fails

Check `.env.prod` file has correct credentials:
```bash
cat .env.prod | grep DB_
```

### Backup Too Large

Adjust backup retention policy or exclude large log files:
```bash
# Edit backup.sh to exclude logs
--exclude='logs/*' --exclude='*.log'
```

---

## Testing Scripts Locally

Before using in production, test scripts in staging:

```bash
# Test deployment
bash deploy.sh staging test-tag

# Test backup
bash backup.sh

# Test health check
bash health-check.sh
```

---

## Script Maintenance

**Version**: 1.0
**Last Updated**: 2024-01-15
**Maintainer**: DevOps Team

For issues or improvements, create an issue in GitLab.

---

## Additional Resources

- [GitLab CI/CD Setup Guide](../GITLAB_CICD_SETUP.md)
- [Deployment Quick Start](../DEPLOYMENT_QUICKSTART.md)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Backup Best Practices](https://www.postgresql.org/docs/current/backup.html)
