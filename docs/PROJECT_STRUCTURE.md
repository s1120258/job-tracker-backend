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

## Notes

- The architecture separates concerns cleanly for scalability and maintainability.
- Use `app/services/` for any custom logic that doesn't fit into CRUD directly.
- `main.py` initializes the app with routers, middleware, and dependencies.
- Tests follow a TDD-ready layout with fixtures and coverage in mind.
- Environment-specific settings can be configured in `.env` and read through `app/core/config.py`.
