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
Docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)
API docs available at: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 🗄️ Database Migrations

```bash
docker compose exec backend alembic revision --autogenerate -m "Add feature"
docker compose exec backend alembic upgrade head
```

### ⚠️ Note on `docker compose down -v`

This deletes the DB volume. Re-apply migrations afterward:

```bash
docker compose up -d
docker compose exec backend alembic upgrade head
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

For API usage and project details, see the [README](../README.md) and other docs in the `docs/` folder.
