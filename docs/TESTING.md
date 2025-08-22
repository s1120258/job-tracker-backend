# 🧪 Testing & Formatting

## ✅ Local Testing

### Basic Testing

```bash
pytest                    # Run all tests
pytest -v                 # Run with verbose output
pytest -x                 # Stop on first failure
pytest --tb=short         # Short traceback format
```

### Test Coverage

```bash
pytest --cov=app                           # Basic coverage
pytest --cov=app --cov-report=html         # HTML coverage report
pytest --cov=app --cov-report=term-missing # Show missing lines
```

### Specific Test Categories

```bash
pytest tests/test_user.py                      # User authentication tests
pytest tests/test_google_auth.py               # Google OAuth tests
pytest tests/test_job.py                       # Job management tests
pytest tests/test_analytics.py                 # Analytics tests
pytest tests/ -k "google"                      # Run only Google-related tests
```

### Test Environment Configuration

Tests use environment variables configured in `pytest.ini`:

```ini
[pytest]
pythonpath = .
env =
    TESTING=true
    GOOGLE_CLIENT_ID=test_client_id
```

**Requirements File:**

- `requirements.txt` - Single file containing all dependencies (production, testing, development tools)

**Installation:**

```bash
# Install all dependencies
pip install -r requirements.txt

# Or with timeout and retries for CI environments
pip install --timeout=1000 --retries=3 -r requirements.txt
```

**Key Testing Dependencies:**

- `pytest-env==1.1.3` - Environment variable management
- `pytest-cov==5.0.0` - Coverage reporting
- `httpx==0.27.0` - Async HTTP client for API testing

**Development Tools (included):**

- `mypy==1.13.0` - Type checking
- `flake8==7.1.1` - Additional linting
- `pre-commit==4.0.1` - Git hooks for code quality
- `memory-profiler==0.61.0` - Performance profiling

---

## 🔐 Google OAuth Testing

### Test Environment Setup

Google OAuth authentication is configured for test environments:

- **Test Mode**: Automatically detected via `TESTING=true` environment variable
- **Mock Authentication**: Uses test credentials instead of real Google services
- **ID Token Verification**: Mocked for testing purposes

### Testing Google Auth Endpoints

```bash
# Test Google authentication endpoints
pytest tests/test_google_auth.py::TestGoogleAuthEndpoints -v

# Test Google OAuth service functions
pytest tests/test_google_auth.py::TestGoogleOAuth2Service -v

# Test user CRUD with Google OAuth
pytest tests/test_google_auth.py::TestUserCRUD -v
```

---

## 🎨 Code Formatting

### Local Formatting

```bash
black .           # Format all code with Black
black --check .   # Check formatting without applying changes
isort .           # Organize imports
isort --check .   # Check import organization
```

### Docker-based Formatting

```bash
docker compose run --rm backend black .
docker compose run --rm backend black --check .
docker compose run --rm backend isort .
```

---

## 🧱 Linting & Type Checking (Optional)

Integrate additional code quality tools:

```bash
pip install flake8 mypy
flake8 .          # Code linting
mypy app/         # Type checking
```

---

## 📦 CI/CD Workflows

### GitHub Actions Configuration

Three workflows are configured under `.github/workflows/`:

#### **1. checks.yml** - Basic Quality Checks

- **Trigger**: Every push to any branch
- **Environment**: Docker Compose
- **Features**:
  - ✅ Run pytest with Google OAuth support
  - ✅ Black formatting verification
  - ✅ Fast feedback for development

```yaml
# Example workflow execution
env:
  SECRET_KEY: ${{ secrets.SECRET_KEY }}
  ALGORITHM: ${{ secrets.ALGORITHM }}
  GOOGLE_CLIENT_ID: ${{ secrets.GOOGLE_CLIENT_ID }}
  GOOGLE_CLIENT_SECRET: ${{ secrets.GOOGLE_CLIENT_SECRET }}
  TESTING: true
```

#### **2. test.yml** - Comprehensive Testing

- **Trigger**: Push/PR to `main` or `dev` branches
- **Environment**: Python 3.11 + PostgreSQL + pgVector
- **Features**:
  - ✅ Database migrations with Alembic
  - ✅ Full test suite with coverage reporting
  - ✅ Codecov integration
  - ✅ PostgreSQL with pgVector extension
  - ✅ Timeout and retry settings for reliable builds
  - ✅ Modern Python version for better dependency compatibility

#### **3. deploy.yml** - Production Deployment

- **Trigger**: Push to `main` branch
- **Features**:
  - ✅ EC2 deployment with SSH
  - ✅ Docker container updates
  - ✅ Environment variable management

### Required GitHub Secrets

```bash
# Authentication & Security
SECRET_KEY              # JWT signing key
ALGORITHM              # JWT algorithm
GOOGLE_CLIENT_ID       # Google OAuth client ID
GOOGLE_CLIENT_SECRET   # Google OAuth client secret

# Deployment (deploy.yml only)
SSH_HOST              # EC2 instance host
SSH_PORT              # SSH port
SSH_USER              # SSH username
SSH_PRIVATE_KEY       # SSH private key
```

---

## 🐳 Docker Testing

### Run Tests in Docker Environment

```bash
# Basic test execution
docker compose run --rm backend pytest

# With coverage reporting
docker compose run --rm backend pytest --cov=app --cov-report=term-missing

# Specific test files
docker compose run --rm backend pytest tests/test_google_auth.py -v

# Run with environment variables
docker compose run --rm -e TESTING=true backend pytest
```

### Database Testing with Docker

```bash
# Start services for testing
docker compose up -d db

# Run migrations
docker compose exec backend alembic upgrade head

# Run database-dependent tests
docker compose run --rm backend pytest tests/test_user.py
```

---

## 🔍 Test Structure

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_analytics.py        # Analytics endpoints testing
├── test_google_auth.py       # Google OAuth authentication
├── test_job.py              # Job management functionality
├── test_main.py             # Main application endpoints
├── test_resume.py           # Resume processing & feedback
├── test_skill_endpoints.py  # Skill analysis & extraction
└── test_user.py             # User authentication & management
```

### Key Testing Patterns

- **Mocking External Services**: Database sessions, embedding services, similarity services
- **Authentication Testing**: JWT tokens, Google OAuth flows, user sessions
- **API Endpoint Testing**: FastAPI TestClient with comprehensive request/response validation
- **Error Handling**: Validation errors, authentication failures, service unavailability

---

## 📊 Coverage Goals

Aim for comprehensive test coverage across:

- **API Routes**: All endpoints with success/failure cases
- **Authentication**: Traditional email/password and Google OAuth
- **Business Logic**: Job matching, skill analysis, resume processing
- **Database Operations**: CRUD operations with proper error handling
- **External Integrations**: Google OAuth, OpenAI LLM services

### Generate Coverage Reports

```bash
# Terminal coverage report
pytest --cov=app --cov-report=term-missing

# HTML coverage report (opens in browser)
pytest --cov=app --cov-report=html
open htmlcov/index.html

# XML coverage for CI/CD
pytest --cov=app --cov-report=xml
```

---

## 🚀 Quick Testing Commands

```bash
# Fast development testing
pytest -x --tb=short         # Stop on first failure, short output

# Full CI-like testing
pytest --cov=app --cov-report=xml --cov-report=term-missing

# Google OAuth specific testing
pytest tests/test_google_auth.py -v

# Format check before commit
black --check . && isort --check .

# Docker-based full pipeline
docker compose run --rm backend sh -c "black --check . && pytest --cov=app"
```

---

For project setup and configuration details, see [SETUP.md](./SETUP.md) and [README](../README.md).
