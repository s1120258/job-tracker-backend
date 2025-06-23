# 🧪 Testing & Formatting

## ✅ Local Testing

```bash
pytest            # Run all tests
```

Ensure test coverage for all major modules (API, CRUD, services).

---

## 🎨 Code Formatting

```bash
black .           # Format all code with Black
isort .           # Organize imports
```

### Run formatters inside Docker:

```bash
docker compose run --rm backend black .
docker compose run --rm backend isort .
```

---

## 🧱 Linting (Optional)

Integrate tools like `flake8` or `mypy` for additional linting and type checks:

```bash
pip install flake8 mypy
flake8 .
mypy app/
```

---

## 📦 CI/CD

GitHub Actions are configured under `.github/workflows/`.

Typical CI pipeline includes:

- Install dependencies
- Lint and format check
- Run tests

You can trigger CI runs automatically on pull requests and commits.

---

For API usage and project details, see the [README](../README.md) and other docs in the `docs/` folder.
