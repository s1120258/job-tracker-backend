# ⚙️ Project Structure

```
app/
├── api/         # API route definitions
├── core/        # App configuration, auth setup, and utility logic
├── crud/        # Reusable DB access patterns using SQLAlchemy
├── db/          # DB initialization, Alembic config
├── models/      # SQLAlchemy ORM models
├── schemas/     # Pydantic request/response schemas
└── main.py      # FastAPI app entrypoint

tests/           # Unit and integration tests
.github/workflows/ # CI pipelines (e.g., GitHub Actions)
docker-compose.yml # Docker orchestration
```

---

For API endpoints, setup instructions, and feature details, see the [README](../README.md) and other docs in the `docs/` folder.
