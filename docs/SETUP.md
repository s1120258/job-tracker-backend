# 📦 Setup Guide

## ✅ Local Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt   # Assumes requirements.txt is present
```

Create a `.env` file with necessary configuration variables (see `env.example` for reference).

---

## 🐳 Docker Setup

Make sure you have Docker and Docker Compose installed.

```bash
docker compose up --build         # Start backend and database
docker compose down               # Stop all containers
```

App available at: [http://localhost:8000](http://localhost:8000)
Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
OpenAPI schema: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 🗄️ Database Migrations

### Create & Apply Migrations

```bash
docker compose exec backend alembic revision --autogenerate -m "Add feature"
docker compose exec backend alembic upgrade head
```

### 🧹 Optional: Reset the Database

If you've made significant changes to your data models or want to start from a clean state, you can recreate the database by removing the volume:

```bash
docker compose down -v
docker compose up -d

# Re-enable pgvector extension after reset
docker compose exec db psql -U postgres -d res_match
CREATE EXTENSION IF NOT EXISTS vector;
\q

docker compose exec backend alembic upgrade head
```

### 🧪 Verify Tables

```bash
docker compose exec db psql -U postgres -d res_match -c '\dt'
docker compose exec db psql -U postgres -d res_match -c '\d tablename'
```

---

## 🔐 Environment Configuration

The application uses a centralized configuration system via `app/core/config.py` with **automatic priority handling**.

### 🔄 Configuration Priority (Highest to Lowest)

1. **Environment Variables** (highest priority)

   ```bash
   export DB_USER=production_user
   export SECRET_KEY=super-secret-production-key
   ```

2. **`.env` file** (medium priority)

   ```bash
   # .env file
   DB_USER=dotenv_user
   SECRET_KEY=dotenv-secret-key
   ```

3. **Default values in `config.py`** (lowest priority)
   ```python
   class Settings(BaseSettings):
       DB_USER: str = "postgres"  # Default fallback
       SECRET_KEY: str = "dev-secret-key"  # Default fallback
   ```

### 📋 Required Environment Variables

- **Database**: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`
- **Security**: `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- **API**: `API_V1_STR`, `PROJECT_NAME`
- **CORS**: `BACKEND_CORS_ORIGINS`
- **Optional**: `OPENAI_API_KEY`

### 🧪 Testing Configuration Priority

Run the test script to see your current configuration:

```bash
python test_config_priority.py
```

### 📝 Configuration Examples

#### Development Setup

```bash
# .env file
DB_USER=dev_user
DB_PASSWORD=dev_password
DB_HOST=localhost
SECRET_KEY=dev-secret-key
```

#### Production Setup

```bash
# Environment variables (override .env)
export DB_USER=prod_user
export DB_PASSWORD=prod_password
export DB_HOST=production-db.com
export SECRET_KEY=super-secret-production-key
```

#### Docker Setup

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - DB_HOST=db
      - DB_USER=postgres
      - SECRET_KEY=docker-secret-key
```

### Configuration Notes

- When running locally, set DB host to `localhost`
- When inside Docker, use `db` as the DB host
- LLM keys and config should be stored in `.env`
- Copy `env.example` to `.env` and customize as needed
- Environment variables always override `.env` file values
- Missing values fall back to defaults in `config.py`

---

## 📚 Additional Setup Guides

For specialized deployment scenarios and advanced configurations, refer to these detailed guides:

### 🌐 Production Deployment

- **[🚀 EC2 Setup](EC2_SETUP.md)** - Complete EC2 deployment instructions with AWS Parameter Store integration
- **[🔐 AWS IAM Setup](AWS_IAM_SETUP.md)** - IAM roles, policies, and Parameter Store configuration
- **[🌐 Nginx Integration](NGINX_INTEGRATION.md)** - Nginx reverse proxy configuration with SSL/TLS

### 🔧 CI/CD & Automation

- **[🔑 GitHub Secrets Setup](GITHUB_SECRETS_SETUP.md)** - GitHub Actions deployment configuration and secrets management

### 📖 Additional Documentation

- **[📋 API Specification](API_SPEC.md)** - Complete API endpoint documentation
- **[🏗️ Technical Architecture](TECHNICAL_ARCHITECTURE.md)** - System architecture and design decisions
- **[🧪 Testing Guide](TESTING.md)** - Comprehensive testing strategies and implementation
- **[📊 Data Model](DATA_MODEL.md)** - Database schema and relationships

---

🔗 **Live interactive API docs**: visit [`/docs`](http://localhost:8000/docs) (Swagger UI)

For project details, see the [README](../README.md) and other docs in the `docs/` folder.
