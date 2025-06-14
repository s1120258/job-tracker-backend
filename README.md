# Job Tracker Backend

A FastAPI backend for managing job applications, storing resumes, and providing AI-powered resume matching and feedback using LLMs.

---

## 🚀 Features

- User authentication with JWT
- Job application management
- Resume storage
- AI-powered resume matching and feedback (LLM integration)
- RESTful API with automatic docs (Swagger UI)

---

## 🛠️ Setup

```sh
python -m venv venv                # Create a virtual environment
source venv/bin/activate           # Activate the virtual environment (Linux/Mac)
pip install "fastapi[all]" uvicorn sqlalchemy psycopg2-binary alembic python-dotenv
pip install openai pytest black isort
pip install 'python-jose[cryptography]' 'passlib[bcrypt]'
```

---

## 🐳 Running with Docker Compose

```sh
docker compose up --build          # Launch Docker containers
docker compose down                # Stop containers
```

- The backend will be available at [http://localhost:8000](http://localhost:8000)
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Testing & Formatting

```sh
pytest                             # Run tests
black app/                         # Format code
isort app/                         # Sort imports
```

---

## 🗄️ Database Migrations

**Initialize Alembic (first time only):**

```sh
alembic init app/db/migrations
```

**Run migrations (inside the backend container):**

```sh
docker compose exec backend bash   # Enter the backend container (while docker-compose is running)
alembic revision --autogenerate -m "create new table"   # Create a new migration
alembic upgrade head               # Apply migrations
```

---

### ⚠️ Important: After `docker compose down -v`

Running `docker compose down -v` deletes your database volume and all data/tables.
**After bringing containers back up, you must re-apply migrations to recreate the tables:**

```sh
docker compose up -d
docker compose exec backend alembic upgrade head
```

---

## 📂 Project Structure

```
app/
  ├── api/           # API route definitions
  ├── core/          # Security, config, and core logic
  ├── crud/          # Database CRUD operations
  ├── db/            # Database setup and migrations
  ├── models/        # SQLAlchemy models
  ├── schemas/       # Pydantic schemas
  └── main.py        # FastAPI entrypoint
```

---

## 📝 Notes

- Make sure your `.env` file is set up with the correct database credentials if needed.
- When running locally (not in Docker), update `alembic.ini` to use `localhost` as the DB host.
- When running in Docker Compose, use `db` as the DB host.

---
