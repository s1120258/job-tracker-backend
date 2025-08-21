# EC2 Setup Instructions for ResMatch API Deployment

## AWS Parameter Store Integration

### 1. IAM Role Setup for EC2

Create an IAM role with the following policy for Parameter Store access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": ["arn:aws:ssm:*:*:parameter/resmatch/*"]
    }
  ]
}
```

Attach this role to your EC2 instance.

### 2. Parameter Store Configuration

Ensure the following parameters are set in AWS Systems Manager Parameter Store:

```bash
# Secure parameters (SecureString type)
/resmatch/DB_PASSWORD          # Supabase database password
/resmatch/SECRET_KEY           # JWT secret key
/resmatch/OPENAI_API_KEY       # OpenAI API key
/resmatch/SUPABASE_KEY         # Supabase anon key (if needed)
```

### 3. EC2 Environment Variables

Create `/opt/resmatch/.env` file on EC2:

```bash
# Database connection (Supabase)
DB_HOST=db.your-project.supabase.co
DB_USER=postgres
DB_NAME=postgres
DB_PORT=5432

# AWS region for Parameter Store
AWS_DEFAULT_REGION=us-east-1

# CORS origins (JSON format)
BACKEND_CORS_ORIGINS=["https://res-match-ui.vercel.app","https://resmatch-api.ddns.net","http://localhost:3000"]

# API configuration
API_V1_STR=/api/v1
PROJECT_NAME=ResMatch

# Job scraper settings
JOB_SCRAPER_TIMEOUT=30
JOB_SCRAPER_RETRIES=3
JOB_SCRAPER_DELAY=1.0
JOB_SCRAPER_USER_AGENT=res-match-api/1.0 (https://res-match.com/bot)
JOB_SCRAPER_MAX_RESULTS=100
```

### 4. Docker Compose Production Override

Update `/opt/resmatch/docker-compose.yml`:

```yaml
services:
  api:
    image: ghcr.io/YOUR_GITHUB_USERNAME/res-match-api:latest
    container_name: resmatch-api
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"
    env_file:
      - /opt/resmatch/.env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Deployment Verification

### 1. Test AWS Parameter Store Access

```bash
# SSH to EC2 and test
docker exec resmatch-api python -c "
from app.core.config import settings
print('DB_PASSWORD:', '***' if settings.DB_PASSWORD else 'NOT SET')
print('SECRET_KEY:', '***' if settings.SECRET_KEY else 'NOT SET')
print('OPENAI_API_KEY:', '***' if settings.OPENAI_API_KEY else 'NOT SET')
"
```

### 2. Test Database Connection

```bash
curl https://resmatch-api.ddns.net/ping-db
```

### 3. Test API Health

```bash
curl https://resmatch-api.ddns.net/healthz
```

## Security Notes

1. **IAM Role**: Use IAM roles instead of access keys for better security
2. **Parameter Store**: Use SecureString type for sensitive parameters
3. **Network**: Keep Docker port bound to 127.0.0.1 only
4. **Logging**: Monitor logs for any AWS authentication issues

## Troubleshooting

### AWS Authentication Issues

```bash
# Check IAM role attachment
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Check AWS region
echo $AWS_DEFAULT_REGION

# Test parameter access
aws ssm get-parameter --name "/resmatch/SECRET_KEY" --with-decryption
```

### Database Connection Issues

```bash
# Test Supabase connection
docker exec resmatch-api python -c "
import psycopg2
from app.core.config import settings
try:
    conn = psycopg2.connect(settings.DATABASE_URL)
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print('❌ Database connection failed:', e)
"
```
