# 📂 Job Application Tracker + Resume Matcher

A FastAPI-based backend to help users track job applications, analyze resumes, and receive AI-powered feedback and match scoring against job descriptions.

---

## 🎯 Overview

This project provides an API-first backend system with resume parsing, vector-based matching, and LLM feedback. Ideal for developers building intelligent job tracking platforms.

---

## 🚀 MVP Features

- Track job applications with custom metadata and manual job description input
- Upload resumes (PDF/DOCX), extract text, and get LLM-generated feedback
- Match resumes to job descriptions using vector similarity (OpenAI/pgvector)
- Get actionable LLM reviews
- Dashboard-ready backend analytics (API only)
- Centralized configuration management
- API versioning support

---

## 🧰 Tech Stack

- **Backend:** FastAPI (async, API-first)
- **Database:** PostgreSQL, SQLAlchemy + Alembic
- **Configuration:** Pydantic Settings with environment variable support
- **Resume Parsing:** PyPDF2, python-docx
- **LLM & Embeddings:** OpenAI API, sentence-transformers, pgvector
- **Authentication:** JWT
- **Dev Tools:** Docker Compose, pytest, black, CI/CD (GitHub Actions)

---

## 📄 Documentation

- ➕ [Full Setup Guide](docs/SETUP.md)
- ⚙️ [Project Structure](docs/PROJECT_STRUCTURE.md)
- 🧪 [Testing & CI](docs/TESTING.md)
- 🤝 [Contributing](docs/CONTRIBUTING.md)
- 📑 [API Specification](docs/API_SPEC.md)
- 🗂️ [Data Model & ERD](docs/DATA_MODEL.md)

---

For API endpoints, setup instructions, and detailed usage, please refer to the linked documentation above.

---
