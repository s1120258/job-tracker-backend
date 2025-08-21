# GitHub Secrets Setup Guide

## Required Secrets Configuration

Navigate to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**

### SSH Connection Secrets

```
SSH_HOST=resmatch-api.ddns.net
SSH_PORT=22
SSH_USER=ubuntu
SSH_PRIVATE_KEY=<your-private-ssh-key>
```

#### SSH_PRIVATE_KEY Setup

1. **Generate SSH key pair** (if not already done):

   ```bash
   ssh-keygen -t ed25519 -C "github-actions@resmatch-deploy" -f ~/.ssh/resmatch_deploy
   ```

2. **Add public key to EC2**:

   ```bash
   # Copy public key to EC2
   ssh-copy-id -i ~/.ssh/resmatch_deploy.pub ubuntu@resmatch-api.ddns.net

   # Or manually add to ~/.ssh/authorized_keys on EC2
   ```

3. **Add private key to GitHub Secrets**:

   ```bash
   # Copy the ENTIRE private key including headers
   cat ~/.ssh/resmatch_deploy
   ```

   Copy the output (including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`) to the `SSH_PRIVATE_KEY` secret.

### Testing Secrets (for CI/CD pipeline)

```
SECRET_KEY=<test-jwt-secret-for-ci>
ALGORITHM=HS256
```

These are used by the existing test workflow and should be different from production values.

## Repository Settings

### 1. Enable GitHub Container Registry

Ensure your repository has access to GitHub Container Registry:

- Go to **Settings** → **General** → **Permissions**
- Under "Container registry", ensure it's enabled

### 2. Repository Visibility

For private repositories:

- ✅ GHCR images will be private by default
- ✅ Only repository collaborators can pull images

For public repositories:

- ⚠️ GHCR images may be public
- Consider making repository private if needed

## Security Best Practices

### 1. SSH Key Management

```bash
# Use a dedicated key for deployment (not your personal key)
# Restrict key permissions on EC2
chmod 600 ~/.ssh/authorized_keys

# Consider adding key restrictions in authorized_keys
echo 'command="cd /opt/resmatch && docker compose pull && docker compose up -d",restrict ssh-ed25519 AAAAC3... github-actions@resmatch-deploy' >> ~/.ssh/authorized_keys
```

### 2. EC2 Security

```bash
# Ensure proper firewall rules
sudo ufw status

# Expected rules:
# 22/tcp (SSH) - restricted to your IPs
# 80/tcp (HTTP) - redirect to HTTPS
# 443/tcp (HTTPS) - public access
```

### 3. Docker Security

```bash
# Verify image signatures (optional)
docker trust key generate <key-name>
docker trust signer add --key <key-file> <signer-name> <repository>
```

## Verification Commands

### Test SSH Connection from GitHub Actions

Run this locally to simulate GitHub Actions SSH:

```bash
# Test SSH connection
ssh -o StrictHostKeyChecking=no -i ~/.ssh/resmatch_deploy ubuntu@resmatch-api.ddns.net "whoami && pwd"

# Test Docker commands
ssh -i ~/.ssh/resmatch_deploy ubuntu@resmatch-api.ddns.net "docker ps && docker compose --version"
```

### Test Container Registry Access

```bash
# Login to GHCR (replace <username> and <token>)
echo "<github-token>" | docker login ghcr.io -u <username> --password-stdin

# Test push (manual)
docker tag <local-image> ghcr.io/<username>/<repo>:test
docker push ghcr.io/<username>/<repo>:test

# Test pull
docker pull ghcr.io/<username>/<repo>:test
```

## Troubleshooting

### SSH Issues

```bash
# Debug SSH connection
ssh -v -i ~/.ssh/resmatch_deploy ubuntu@resmatch-api.ddns.net

# Check SSH logs on EC2
sudo tail -f /var/log/auth.log
```

### Container Registry Issues

```bash
# Check GHCR permissions
curl -H "Authorization: token <github-token>" https://api.github.com/user/packages

# Verify image existence
docker manifest inspect ghcr.io/<username>/<repo>:latest
```

### GitHub Actions Debug

Enable debug logging in your repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add these secrets:
   ```
   ACTIONS_RUNNER_DEBUG=true
   ACTIONS_STEP_DEBUG=true
   ```

## Environment Variables Reference

### Production Environment (.env on EC2)

```env
# Database (Supabase)
DB_HOST=db.your-project.supabase.co
DB_USER=postgres
DB_NAME=postgres
DB_PORT=5432

# AWS
AWS_DEFAULT_REGION=us-east-1

# CORS
BACKEND_CORS_ORIGINS=["https://res-match-ui.vercel.app","https://resmatch-api.ddns.net"]

# API
API_V1_STR=/api/v1
PROJECT_NAME=ResMatch
```

### Secrets in AWS Parameter Store

```bash
# Verify parameter store access
aws ssm get-parameter --name "/resmatch/SECRET_KEY" --with-decryption --region us-east-1

# Expected parameters:
/resmatch/DB_PASSWORD
/resmatch/SECRET_KEY
/resmatch/OPENAI_API_KEY
/resmatch/SUPABASE_KEY
```

## Monitoring Deployment

### GitHub Actions

Monitor deployments in:

- **Actions** tab in your repository
- Check logs for each step
- Verify successful completion

### EC2 Monitoring

```bash
# Monitor deployment logs
docker logs -f resmatch-api

# Check service health
curl http://localhost:8000/healthz
curl https://resmatch-api.ddns.net/healthz

# Monitor system resources
docker stats
htop
```

## Rollback Procedure

If deployment fails:

```bash
# SSH to EC2
ssh ubuntu@resmatch-api.ddns.net

# Check previous images
docker images | grep resmatch

# Rollback to previous version
docker tag ghcr.io/<username>/<repo>:<previous-sha> ghcr.io/<username>/<repo>:latest
cd /opt/resmatch
docker compose up -d
```
