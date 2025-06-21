# 📂 Job Application Tracker + Resume Matcher

A FastAPI-based backend to help users track job applications, analyze resumes, and receive AI-powered feedback and match scoring against job descriptions.

---

## 🎯 Overview

This project provides an API-first backend system with resume parsing, vector-based matching, and LLM feedback. Ideal for developers building intelligent job tracking platforms.

---

## 🚀 Key Features

- Track job applications with custom metadata
- Upload resumes and get LLM-generated improvement feedback
- Match resumes to job descriptions using vector similarity
- Get actionable LLM reviews
- Dashboard-ready backend
- Centralized configuration management
- API versioning support

---

## 🧰 Tech Stack

- **Backend:** FastAPI (async, API-first)
- **Database:** PostgreSQL, SQLAlchemy + Alembic
- **Configuration:** Pydantic Settings with environment variable support
- **Resume Parsing:** PyPDF2, python-docx, optional spaCy
- **LLM & Embeddings:** OpenAI API or local (LangChain), sentence-transformers
- **Vector DB:** ChromaDB / pgvector / FAISS
- **Authentication:** JWT or OAuth2
- **Dev Tools:** Docker Compose, pytest, black, CI/CD (GitHub Actions)

---

## 📄 Documentation

- ➕ [Full Setup Guide](docs/SETUP.md)
- ⚙️ [Project Structure](docs/PROJECT_STRUCTURE.md)
- 🧪 [Testing & CI](docs/TESTING.md)
- 🤝 [Contributing](docs/CONTRIBUTING.md)

---

## 🔗 API Endpoints

- **Base URL:** `http://localhost:8000/api/v1`
- **Authentication:** `/api/v1/auth/register`, `/api/v1/auth/token`, `/api/v1/auth/me`
- **API Documentation:** `http://localhost:8000/docs`
- **OpenAPI Schema:** `http://localhost:8000/api/v1/openapi.json`
