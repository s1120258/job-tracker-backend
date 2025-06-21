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

---

## 🧰 Tech Stack

- **Backend:** FastAPI (async, API-first)
- **Database:** PostgreSQL, SQLAlchemy + Alembic
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
