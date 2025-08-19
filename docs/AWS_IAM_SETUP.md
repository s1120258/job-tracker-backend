# AWS IAM Setup Guide

## Creating EC2 IAM Role (Recommended for Production)

### 1. Create IAM Role

1. AWS Console → IAM → Roles → Create role
2. Trusted entity type: AWS service
3. Service: EC2
4. Role name: `resmatch-ec2-role`

### 2. Create Parameter Store Policy

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
      "Resource": ["arn:aws:ssm:us-east-1:*:parameter/resmatch/*"]
    }
  ]
}
```

Policy name: `resmatch-parameter-store-access`

### 3. Attach Policy to Role

1. Select the created role `resmatch-ec2-role`
2. Permissions → Attach policies
3. Select and attach `resmatch-parameter-store-access`

### 4. Assign Role to EC2 Instance

#### For new instance creation:

- Launch instance → IAM instance profile → `resmatch-ec2-role`

#### For existing instance:

1. EC2 Console → Instances → Select instance
2. Actions → Security → Modify IAM role
3. Select `resmatch-ec2-role`

## Development Environment Setup (Local Development)

### Method 1: AWS CLI Configuration

```bash
aws configure
# AWS Access Key ID: your_access_key
# AWS Secret Access Key: your_secret_key
# Default region name: us-east-1
# Default output format: json
```

### Method 2: Environment Variables (.env file)

```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
```

### Developer IAM User Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ssm:GetParameter", "ssm:PutParameter", "ssm:DeleteParameter"],
      "Resource": ["arn:aws:ssm:us-east-1:*:parameter/resmatch/*"]
    }
  ]
}
```

## Environment-Specific Authentication Methods

| Environment             | Recommended Method | Reason                           |
| ----------------------- | ------------------ | -------------------------------- |
| **Production (EC2)**    | IAM Role           | Highest security, auto-managed   |
| **Staging (EC2)**       | IAM Role           | Same configuration as production |
| **Development (Local)** | AWS CLI Setup      | Developer convenience            |
| **CI/CD**               | IAM Role or OIDC   | Pipeline-specific permissions    |

## Security Best Practices

1. **Principle of Least Privilege**: Grant only minimum required permissions
2. **Resource Restriction**: Limit Parameter Store access to `/resmatch/*` path only
3. **Regular Auditing**: Monitor access logs with CloudTrail
4. **Credential Rotation**: Regularly rotate development credentials

## Verification

### Verification on EC2 Instance:

```bash
# Check if IAM role is correctly configured
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Test Parameter Store access
aws ssm get-parameter --name "/resmatch/DB_PASSWORD" --with-decryption --region us-east-1
```

## Parameter Store Configuration

### Required Parameters

Create the following parameters in AWS Systems Manager Parameter Store:

1. **`/resmatch/DB_PASSWORD`** (SecureString)

   - Your Supabase database password
   - Example: `5enDH2-mSGaEAUL`

2. **`/resmatch/SECRET_KEY`** (SecureString)

   - JWT secret key for application security
   - Generate: `openssl rand -hex 32`

3. **`/resmatch/OPENAI_API_KEY`** (SecureString)

   - OpenAI API key for LLM features
   - Format: `sk-...`

4. **`/resmatch/SUPABASE_KEY`** (SecureString)
   - Supabase anonymous key
   - Get from Supabase dashboard

### Creating Parameters via AWS CLI

```bash
# Create database password
aws ssm put-parameter \
    --name "/resmatch/DB_PASSWORD" \
    --value "your_db_password" \
    --type "SecureString" \
    --region us-east-1

# Create secret key
aws ssm put-parameter \
    --name "/resmatch/SECRET_KEY" \
    --value "$(openssl rand -hex 32)" \
    --type "SecureString" \
    --region us-east-1

# Create OpenAI API key
aws ssm put-parameter \
    --name "/resmatch/OPENAI_API_KEY" \
    --value "your_openai_api_key" \
    --type "SecureString" \
    --region us-east-1

# Create Supabase key
aws ssm put-parameter \
    --name "/resmatch/SUPABASE_KEY" \
    --value "your_supabase_anon_key" \
    --type "SecureString" \
    --region us-east-1
```

## Deployment Architecture

### Production Setup

```
┌─────────────────────────────────────┐
│            AWS EC2 Instance         │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐    │
│  │      ResMatch API App       │    │
│  │  ┌─────────────────────┐    │    │
│  │  │  IAM Role Auto-Auth │    │    │
│  │  └─────────────────────┘    │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│     AWS Systems Manager             │
│     Parameter Store                 │
├─────────────────────────────────────┤
│  /resmatch/DB_PASSWORD             │
│  /resmatch/SECRET_KEY              │
│  /resmatch/OPENAI_API_KEY          │
│  /resmatch/SUPABASE_KEY            │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│         Supabase Database           │
│     (PostgreSQL + pgvector)         │
└─────────────────────────────────────┘
```

## Troubleshooting

### Common Issues

1. **"No credentials found"**

   - Check IAM role assignment to EC2 instance
   - Verify AWS CLI configuration for local development

2. **"Parameter not found"**

   - Verify parameter exists in correct region (us-east-1)
   - Check parameter name spelling and path

3. **"Access denied"**

   - Verify IAM policy permissions
   - Check resource ARN in policy matches parameter path

4. **"Invalid region"**
   - Ensure region is set correctly (us-east-1)
   - Check EC2 metadata service accessibility

### Debug Commands

```bash
# Check current AWS identity
aws sts get-caller-identity

# List available parameters
aws ssm describe-parameters --region us-east-1

# Test parameter access
aws ssm get-parameter --name "/resmatch/DB_PASSWORD" --region us-east-1

# Check EC2 metadata (if on EC2)
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

## Cost Optimization

- **Parameter Store**: First 10,000 requests per month are free
- **CloudTrail**: Basic logging is free (first copy of management events)
- **IAM**: No charges for IAM users, groups, roles, or policies

## Migration from Environment Variables

If migrating from `.env` file configuration:

1. Create parameters in Parameter Store with existing values
2. Deploy code with Parameter Store integration
3. Verify application loads secrets from Parameter Store
4. Remove sensitive values from `.env` file (keep non-sensitive config)
5. Update deployment scripts to exclude `.env` from production

This ensures zero-downtime migration and maintains fallback capability during transition.
