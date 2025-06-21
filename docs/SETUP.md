# 📦 Setup Guide

## ✅ Local Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt   # Assumes requirements.txt is present
```

Create a `.env` file with necessary DB credentials and API keys.

---

## 🐳 Docker Setup

Make sure you have Docker and Docker Compose installed.

```bash
docker compose up --build         # Start backend and database
docker compose down               # Stop all containers
```

App available at: [http://localhost:8000](http://localhost:8000)
Docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

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

- When running locally, set DB host to `localhost`
- When inside Docker, use `db` as the DB host
- LLM keys and config should be stored in `.env`
