# 📂 Job Application Tracker + Resume Matcher

A FastAPI-based backend to help users track job applications, analyze resumes, and receive AI-powered feedback and match scoring against job descriptions.

---

## 🎯 Overview

This project provides an API-first backend system with resume parsing, vector-based matching, and LLM feedback. Ideal for developers building intelligent job tracking platforms.

---

## 🚀 Key Features

### ✅ Job Application Tracking

- Create, update, and manage job applications with status, notes, and manually entered job descriptions.

### 📄 Resume Upload & AI Feedback

- Upload a single resume (PDF/DOCX), automatically extract text, and receive actionable feedback from an LLM.

### 🤖 Resume-to-Job Matching

- Compare resume and job descriptions using vector embeddings (OpenAI/sentence-transformers + pgvector) and score match quality.

### 📊 Analytics-Ready API

- Backend API endpoints to support frontend dashboards — including application status summaries, time trends, and match score statistics.

### 🔐 Authentication & Authorization

- Secure JWT-based user authentication for all protected routes.

### ⚙️ Modular & Configurable

- Environment-based config using Pydantic settings; ready for extension.

### 🧪 Production-Ready Dev Workflow

- Docker Compose setup, full test suite with pytest, formatting with `black`, and CI/CD via GitHub Actions.

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

- 📑 [API Specification](docs/API_SPEC.md)
- 🗂️ [Data Model](docs/DATA_MODEL.md)
- ➕ [Full Setup Guide](docs/SETUP.md)
- ⚙️ [Project Structure](docs/PROJECT_STRUCTURE.md)
- 🧪 [Testing & CI](docs/TESTING.md)

---

For API endpoints, setup instructions, and detailed usage, please refer to the linked documentation above.

---
