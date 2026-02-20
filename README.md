# CDB Vehicle Valuation System

## CI/CD Pipeline Configuration Guide

This document provides step-by-step instructions to configure GitLab CI/CD for the Vehicle Valuation System. The pipeline is defined in `.gitlab-ci.yml` and covers building, testing, security scanning, deployment, verification, and rollback.

---

## Table of Contents

- [Pipeline Overview](#pipeline-overview)
- [Pipeline Stages](#pipeline-stages)
- [Pipeline Trigger Rules](#pipeline-trigger-rules)
- [Step 1: Register a GitLab Runner](#step-1-register-a-gitlab-runner)
- [Step 2: Enable Container Registry](#step-2-enable-container-registry)
- [Step 3: Configure CI/CD Variables](#step-3-configure-cicd-variables)
- [Step 4: Protect Branches](#step-4-protect-branches)
- [Step 5: Configure Environments](#step-5-configure-environments)
- [Step 6: Validate Pipeline Configuration](#step-6-validate-pipeline-configuration)
- [Step 7: Prepare Deployment Servers](#step-7-prepare-deployment-servers)
- [Step 8: Create Required Deployment Scripts](#step-8-create-required-deployment-scripts)
- [Step 9: Run Your First Pipeline](#step-9-run-your-first-pipeline)
- [Rollback Procedure](#rollback-procedure)
- [Troubleshooting](#troubleshooting)
- [Configuration Checklist](#configuration-checklist)

---

## Pipeline Overview

The CI/CD pipeline automates the full software delivery lifecycle:

```
build --> test --> security --> deploy (manual) --> verify --> rollback (manual)
```

- **Build**: Compiles frontend, installs backend dependencies, and builds Docker images
- **Test**: Runs backend and frontend test suites
- **Security**: Scans Docker images and dependencies for vulnerabilities
- **Deploy**: Deploys to staging or production via SSH (manual trigger)
- **Verify**: Runs health checks against deployed services
- **Rollback**: Reverts production to the previous version (manual trigger)

---

## Pipeline Stages

| Stage | Jobs | Description |
|-------|------|-------------|
| `build` | `build:frontend`, `build:backend`, `build:valuation-engine`, `build:docker-images` | Compile code and build Docker images |
| `test` | `test:backend`, `test:frontend` | Run automated tests |
| `security` | `security:docker-scan`, `security:dependency-scan` | Vulnerability scanning |
| `deploy` | `deploy:staging`, `deploy:production`, `stop:staging`, `stop:production` | Deploy to target environment |
| `verify` | `verify:staging`, `verify:production` | Health check verification |
| `rollback` | `rollback:production` | Revert to previous deployment |

---

## Pipeline Trigger Rules

The pipeline runs different jobs depending on which branch is pushed:

| Branch / Event | Build | Test | Security | Deploy Target | Verify | Rollback |
|----------------|-------|------|----------|---------------|--------|----------|
| `main` | Yes | Yes | Yes | Production (manual) | Yes | Yes (manual) |
| `develop` | Yes | Yes | Yes | Staging (manual) | Yes | No |
| Merge Requests | Yes | Yes | No | No | No | No |

- Deploy and rollback jobs require **manual trigger** (click the play button in the pipeline UI).
- Security scan jobs are set to `allow_failure: true`, so they will not block the pipeline if they fail.

---

## Step 1: Register a GitLab Runner

The pipeline requires a GitLab Runner with the `docker` tag and Docker executor with **privileged mode** enabled (required for Docker-in-Docker builds).

### 1.1 Create the Runner in GitLab UI

1. Navigate to your project in GitLab
2. Go to **Settings > CI/CD**
3. Expand the **Runners** section
4. Click **New project runner**
5. Configure:
   - **Tags**: Enter `docker`
   - **Run untagged jobs**: Check this if you want the runner to also pick up untagged jobs
   - **Platform**: Select **Linux**
6. Click **Create runner**
7. Copy the **registration token** shown on the next page

### 1.2 Install GitLab Runner on Your Server

On the Linux server that will act as the runner:

```bash
# Install GitLab Runner (Debian/Ubuntu)
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash
sudo apt-get install gitlab-runner

# Or for RHEL/CentOS
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.rpm.sh" | sudo bash
sudo yum install gitlab-runner
```

### 1.3 Register the Runner

```bash
sudo gitlab-runner register \
  --url https://your-gitlab-instance.com \
  --token <TOKEN_FROM_STEP_1.1> \
  --executor docker \
  --docker-image alpine:latest \
  --tag-list docker \
  --docker-privileged \
  --docker-volumes "/certs/client"
```

**Flags explained:**

| Flag | Purpose |
|------|---------|
| `--url` | Your GitLab instance URL |
| `--token` | The token from the runner creation step |
| `--executor docker` | Use Docker as the executor |
| `--docker-image alpine:latest` | Default image when jobs don't specify one |
| `--tag-list docker` | Tags that match the `tags: [docker]` in `.gitlab-ci.yml` |
| `--docker-privileged` | **Required** for `docker:24-dind` service (Docker-in-Docker) |
| `--docker-volumes "/certs/client"` | Required for Docker TLS communication |

### 1.4 Verify Runner Status

1. Go back to **Settings > CI/CD > Runners** in GitLab
2. The runner should appear with a **green circle** (online status)
3. Verify the `docker` tag is listed

### 1.5 (Optional) Configure Runner for Concurrent Jobs

Edit the runner configuration file on the server:

```bash
sudo nano /etc/gitlab-runner/config.toml
```

Set the `concurrent` value to allow multiple parallel jobs:

```toml
concurrent = 4
```

---

## Step 2: Enable Container Registry

The pipeline builds and pushes Docker images to GitLab's built-in Container Registry. This must be enabled.

1. Go to **Settings > General**
2. Expand **Visibility, project features, permissions**
3. Toggle **Container Registry** to **ON**
4. Click **Save changes**

Once enabled, the following predefined CI/CD variables become available automatically:

| Variable | Description |
|----------|-------------|
| `$CI_REGISTRY` | The registry URL (e.g., `registry.gitlab.com`) |
| `$CI_REGISTRY_IMAGE` | The registry image path for this project |
| `$CI_REGISTRY_USER` | Username for registry authentication |
| `$CI_REGISTRY_PASSWORD` | Password/token for registry authentication |

These are used in the `build:docker-images` job for `docker login` and `docker push`.

---

## Step 3: Configure CI/CD Variables

The pipeline requires several variables for SSH deployment, server addresses, and environment configuration.

### 3.1 Navigate to Variables Settings

1. Go to **Settings > CI/CD**
2. Expand the **Variables** section
3. Click **Add variable** for each variable listed below

### 3.2 Required Variables

Add each of the following variables:

#### SSH_PRIVATE_KEY

| Field | Value |
|-------|-------|
| **Key** | `SSH_PRIVATE_KEY` |
| **Value** | The full contents of the SSH private key file (including `-----BEGIN ... KEY-----` and `-----END ... KEY-----` lines) |
| **Type** | Variable |
| **Protected** | Yes |
| **Masked** | Yes |
| **Scope** | All environments |

Generate an SSH key pair if you don't have one:

```bash
ssh-keygen -t ed25519 -C "gitlab-ci-deploy" -f gitlab-deploy-key
# Copy the contents of gitlab-deploy-key (private key) into this variable
# Copy gitlab-deploy-key.pub (public key) to the deploy server's authorized_keys
```

#### DEPLOY_USER

| Field | Value |
|-------|-------|
| **Key** | `DEPLOY_USER` |
| **Value** | SSH username on the deployment server (e.g., `deploy`) |
| **Type** | Variable |
| **Protected** | Yes |
| **Masked** | No |
| **Scope** | All environments |

#### DEPLOY_SERVER

| Field | Value |
|-------|-------|
| **Key** | `DEPLOY_SERVER` |
| **Value** | Production server IP address or hostname (e.g., `192.168.1.100`) |
| **Type** | Variable |
| **Protected** | Yes |
| **Masked** | No |
| **Scope** | `main` branch or `production` environment |

#### DEPLOY_SERVER_STAGING

| Field | Value |
|-------|-------|
| **Key** | `DEPLOY_SERVER_STAGING` |
| **Value** | Staging server IP address or hostname |
| **Type** | Variable |
| **Protected** | Yes |
| **Masked** | No |
| **Scope** | `develop` branch or `staging` environment |

#### ENV_PRODUCTION

| Field | Value |
|-------|-------|
| **Key** | `ENV_PRODUCTION` |
| **Value** | Full contents of your production `.env.prod` file (all environment variables for production) |
| **Type** | Variable |
| **Protected** | Yes |
| **Masked** | Yes |
| **Scope** | `main` branch or `production` environment |

Example value (adjust to match your actual `.env.prod`):

```
DATABASE_URL=postgresql://user:password@db:5432/vehicle_valuation
SECRET_KEY=your-secret-key
ENVIRONMENT=production
...
```

#### ENV_STAGING

| Field | Value |
|-------|-------|
| **Key** | `ENV_STAGING` |
| **Value** | Full contents of your staging `.env.prod` file |
| **Type** | Variable |
| **Protected** | Yes |
| **Masked** | Yes |
| **Scope** | `develop` branch or `staging` environment |

### 3.3 How to Add a Variable (Step-by-Step)

1. Click **Add variable**
2. Enter the **Key** (variable name)
3. Paste the **Value**
4. Set **Type** to `Variable`
5. Check **Protect variable** if the variable should only be available on protected branches
6. Check **Mask variable** if the value should be hidden in job logs
7. Set **Environment scope** as needed (`All environments`, or a specific branch/environment)
8. Click **Add variable**

### 3.4 Variables Summary Table

| Variable | Protected | Masked | Scope |
|----------|-----------|--------|-------|
| `SSH_PRIVATE_KEY` | Yes | Yes | All |
| `DEPLOY_USER` | Yes | No | All |
| `DEPLOY_SERVER` | Yes | No | `main` / production |
| `DEPLOY_SERVER_STAGING` | Yes | No | `develop` / staging |
| `ENV_PRODUCTION` | Yes | Yes | `main` / production |
| `ENV_STAGING` | Yes | Yes | `develop` / staging |

---

## Step 4: Protect Branches

Protected branches ensure that only authorized users can push or merge, and that protected CI/CD variables are only exposed on these branches.

### 4.1 Protect the `main` Branch

1. Go to **Settings > Repository**
2. Expand **Protected branches**
3. If `main` is not already listed, select it from the dropdown
4. Configure:
   - **Allowed to merge**: Maintainers (recommended)
   - **Allowed to push and merge**: No one (forces use of merge requests)
   - **Allowed to force push**: No
5. Click **Protect**

### 4.2 Protect the `develop` Branch

1. In the same **Protected branches** section
2. Select `develop` from the dropdown
3. Configure:
   - **Allowed to merge**: Developers + Maintainers
   - **Allowed to push and merge**: Developers + Maintainers (or restrict as needed)
4. Click **Protect**

### 4.3 Why Branch Protection Matters

- **Protected CI/CD variables** (like `ENV_PRODUCTION`, `SSH_PRIVATE_KEY`) are only injected into pipelines running on protected branches
- Prevents accidental or unauthorized deployments from feature branches
- Enforces code review through merge requests before deployment

---

## Step 5: Configure Environments

Environments in GitLab provide deployment tracking, history, and the ability to stop/rollback deployments.

### 5.1 Automatic Creation

Environments are **automatically created** the first time a deploy job runs. The `.gitlab-ci.yml` defines:

- `staging` environment (URL: `https://staging.vehicle-valuation.example.com`)
- `production` environment (URL: `https://vehicle-valuation.example.com`)

### 5.2 Manual Pre-Configuration (Optional)

If you want to set up environments before the first deployment:

1. Go to **Operate > Environments**
2. Click **New environment**
3. Create `staging`:
   - **Name**: `staging`
   - **External URL**: Your staging URL
4. Create `production`:
   - **Name**: `production`
   - **External URL**: Your production URL

### 5.3 Update Environment URLs

Update the URLs in `.gitlab-ci.yml` to match your actual deployment:

```yaml
# In deploy:staging job
environment:
  name: staging
  url: https://your-actual-staging-url.com

# In deploy:production job
environment:
  name: production
  url: https://your-actual-production-url.com
```

Also update the health check URLs in the `verify:staging` and `verify:production` jobs to match.

---

## Step 6: Validate Pipeline Configuration

Before running the pipeline, validate that the `.gitlab-ci.yml` is correct.

### 6.1 Using Pipeline Editor

1. Go to **Build > Pipeline editor**
2. The editor will load your `.gitlab-ci.yml` file
3. Click **Validate** to check for syntax errors
4. Fix any reported issues
5. Click the **Visualize** tab to see a graphical representation of the pipeline flow

### 6.2 Using CI Lint (Alternative)

1. Go to **Build > Pipelines**
2. Click **CI lint** (top right)
3. Paste the contents of your `.gitlab-ci.yml`
4. Click **Validate**

### 6.3 Expected Pipeline Visualization

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ build              test             security         deploy          verify         │
│                                                                                     │
│ build:frontend --> test:frontend                                                    │
│ build:backend  --> test:backend --> security:*  --> deploy:staging --> verify:staging│
│ build:valuation-engine                          --> deploy:production --> verify:prod│
│ build:docker-images                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 7: Prepare Deployment Servers

Both the staging and production servers need to be prepared before the pipeline can deploy.

### 7.1 Install Docker and Docker Compose

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y docker.io docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Verify installation
docker --version
docker compose version
```

### 7.2 Create the Deploy User

```bash
# Create the deploy user
sudo useradd -m -s /bin/bash deploy

# Add deploy user to the docker group (allows running docker without sudo)
sudo usermod -aG docker deploy

# Verify docker access
sudo -u deploy docker ps
```

### 7.3 Set Up SSH Access

```bash
# Create .ssh directory for the deploy user
sudo -u deploy mkdir -p /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh

# Add the public key (corresponding to SSH_PRIVATE_KEY in GitLab variables)
# Paste the contents of your gitlab-deploy-key.pub
sudo -u deploy nano /home/deploy/.ssh/authorized_keys
sudo chmod 600 /home/deploy/.ssh/authorized_keys
```

### 7.4 Create Deployment Directories

```bash
# Create application directory
sudo mkdir -p /opt/cdb/vehicle-valuation
sudo chown -R deploy:deploy /opt/cdb/vehicle-valuation

# Create backup directory
sudo mkdir -p /opt/cdb/backups
sudo chown -R deploy:deploy /opt/cdb/backups

# Create scripts directory
sudo -u deploy mkdir -p /opt/cdb/vehicle-valuation/scripts
```

### 7.5 Configure Firewall (if applicable)

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

### 7.6 Test SSH Connection

From the GitLab Runner server (or any machine with the private key):

```bash
ssh -i gitlab-deploy-key deploy@<SERVER_IP> "echo 'SSH connection successful'"
```

---

## Step 8: Create Required Deployment Scripts

The pipeline references three scripts that must exist in the `scripts/` directory of the repository.

### 8.1 `scripts/deploy.sh`

This script is called by the deploy jobs to start services:

```bash
#!/bin/bash
set -e

ENVIRONMENT=$1
IMAGE_TAG=$2
COMPOSE_FILE="docker-compose.prod.yml"

echo "Deploying $ENVIRONMENT with image tag: $IMAGE_TAG"

# Pull latest images
docker compose -f $COMPOSE_FILE pull

# Stop existing services
docker compose -f $COMPOSE_FILE down

# Start services with new images
IMAGE_TAG=$IMAGE_TAG docker compose -f $COMPOSE_FILE up -d

# Wait for services to be healthy
echo "Waiting for services to start..."
sleep 10

# Show running containers
docker compose -f $COMPOSE_FILE ps

echo "Deployment to $ENVIRONMENT completed."
```

### 8.2 `scripts/backup.sh`

This script creates a backup before production deployment:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/opt/cdb/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Creating backup: $TIMESTAMP"

# Backup database
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U postgres vehicle_valuation > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

# Backup current docker-compose and env files
cp docker-compose.prod.yml "$BACKUP_DIR/docker-compose_$TIMESTAMP.yml"

# Keep only last 5 backups
ls -t "$BACKUP_DIR"/db_backup_*.sql | tail -n +6 | xargs -r rm

echo "Backup completed: $BACKUP_DIR"
```

### 8.3 `scripts/rollback.sh`

This script reverts to the previous deployment:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/opt/cdb/backups"

# Find the latest backup
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/db_backup_*.sql | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "No backup found. Cannot rollback."
    exit 1
fi

echo "Rolling back to: $LATEST_BACKUP"

# Stop current services
docker compose -f docker-compose.prod.yml down

# Restore database
docker compose -f docker-compose.prod.yml up -d db
sleep 5
docker compose -f docker-compose.prod.yml exec -T db psql -U postgres vehicle_valuation < "$LATEST_BACKUP"

# Restart all services with previous images
docker compose -f docker-compose.prod.yml up -d

echo "Rollback completed."
```

Make the scripts executable:

```bash
chmod +x scripts/deploy.sh scripts/backup.sh scripts/rollback.sh
```

---

## Step 9: Run Your First Pipeline

### 9.1 Push Code to GitLab

```bash
git remote add origin https://your-gitlab-instance.com/your-group/vehicle-valuation.git
git push -u origin main
git push -u origin develop
```

### 9.2 Monitor the Pipeline

1. Go to **Build > Pipelines**
2. You should see a new pipeline triggered by your push
3. Click on the pipeline to see the detailed view
4. Click on individual jobs to view their logs

### 9.3 Trigger Manual Deployment

1. Once the build, test, and security stages pass, the deploy stage will show a **play button** icon
2. Click the **play button** on the desired deploy job (`deploy:staging` or `deploy:production`)
3. The deployment will start and you can monitor its progress in the job logs
4. After deployment, the verify stage will run automatically

### 9.4 View Deployment History

1. Go to **Operate > Environments**
2. Click on `staging` or `production`
3. View the deployment history with timestamps and commit references

---

## Rollback Procedure

If a production deployment fails or causes issues:

1. Go to **Build > Pipelines**
2. Find the pipeline for the `main` branch
3. In the **rollback** stage, click the **play button** on `rollback:production`
4. Monitor the job logs to confirm the rollback completes successfully
5. Verify the application is working by checking the health endpoints

---

## Troubleshooting

### Runner Not Picking Up Jobs

- Verify the runner is online: **Settings > CI/CD > Runners**
- Check that the runner has the `docker` tag
- Ensure the runner is assigned to the project (not just the group)
- Check runner logs: `sudo gitlab-runner status` and `sudo journalctl -u gitlab-runner`

### Docker-in-Docker (DinD) Fails

- Ensure the runner is registered with `--docker-privileged`
- Check the `DOCKER_TLS_CERTDIR` variable is set correctly
- Verify Docker service is running: `docker:24-dind`

### SSH Connection Fails During Deploy

- Verify `SSH_PRIVATE_KEY` variable is set correctly (include the full key with headers)
- Ensure the corresponding public key is in the deploy user's `~/.ssh/authorized_keys`
- Test SSH manually from the runner server
- Check that `DEPLOY_SERVER` / `DEPLOY_SERVER_STAGING` variables contain the correct IP/hostname
- Ensure the server's SSH port (22) is open in the firewall

### Protected Variables Not Available

- Ensure the branch is protected: **Settings > Repository > Protected branches**
- Ensure the variable has **Protected** checked
- Ensure the environment scope matches

### Container Registry Push Fails

- Verify Container Registry is enabled: **Settings > General > Visibility**
- Check that `$CI_REGISTRY_USER` and `$CI_REGISTRY_PASSWORD` are available (these are auto-generated)
- Verify the runner can reach the registry URL

### Pipeline Passes But Deployment Fails

- Check that `scripts/deploy.sh` exists and is executable
- Verify the `docker-compose.prod.yml` file is correct
- Check Docker is installed on the deployment server
- Verify the deploy user has docker permissions

---

## Configuration Checklist

Use this checklist to ensure everything is properly configured:

- [ ] **GitLab Runner** registered with `docker` tag and privileged mode enabled
- [ ] **Runner status** shows as online (green dot) in Settings > CI/CD > Runners
- [ ] **Container Registry** enabled in Settings > General
- [ ] **CI/CD Variable**: `SSH_PRIVATE_KEY` configured (Protected, Masked)
- [ ] **CI/CD Variable**: `DEPLOY_USER` configured (Protected)
- [ ] **CI/CD Variable**: `DEPLOY_SERVER` configured (Protected, scoped to main)
- [ ] **CI/CD Variable**: `DEPLOY_SERVER_STAGING` configured (Protected, scoped to develop)
- [ ] **CI/CD Variable**: `ENV_PRODUCTION` configured (Protected, Masked, scoped to main)
- [ ] **CI/CD Variable**: `ENV_STAGING` configured (Protected, Masked, scoped to develop)
- [ ] **Branch `main`** is protected
- [ ] **Branch `develop`** is protected
- [ ] **Staging server** prepared (Docker, deploy user, SSH, directories)
- [ ] **Production server** prepared (Docker, deploy user, SSH, directories)
- [ ] **`scripts/deploy.sh`** exists and is executable
- [ ] **`scripts/backup.sh`** exists and is executable
- [ ] **`scripts/rollback.sh`** exists and is executable
- [ ] **Pipeline validated** in Pipeline Editor (no syntax errors)
- [ ] **Environment URLs** updated in `.gitlab-ci.yml` to match actual deployment URLs
- [ ] **Health check URLs** updated in verify jobs to match actual endpoints
