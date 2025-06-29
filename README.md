# 📂 ResMatch API

A FastAPI-based backend to help users track job applications, upload and analyze resumes, and receive AI-powered feedback and matching scores against job descriptions.

---

## 🎯 Overview

This project provides an API-first backend system designed for developers building intelligent job-tracking platforms. It includes resume parsing, vector-based matching, and LLM-generated insights to streamline and enhance job search workflows.

---

## 🚀 Key Features

### ✅ Job Application Tracking

- Create, update, and manage job applications with status fields, notes, and manually entered job descriptions.

### 📄 Resume Upload & AI Feedback

- Upload a resume (PDF/DOCX), auto-extract content, and get AI-powered general or job-specific feedback.

### 🤖 AI Resume-to-Job Matching

- Leverage vector embeddings (OpenAI with pgvector) to compare resumes with job descriptions and score compatibility.

### 📊 Analytics-Ready API

- Built-in backend analytics endpoints to support dashboards — includes application status breakdowns, match score summaries, and trend analysis.

### 🔐 Secure Authentication

- JWT-based user authentication system secures all protected API routes.

### ⚙️ Modular & Configurable

- Environment-driven configuration using Pydantic, with easy customization for different environments.

### 🧪 Developer-First Workflow

- Docker Compose for environment setup, unit and integration tests via `pytest`, code formatting with `black`, and CI/CD powered by GitHub Actions.

---

## 🧰 Tech Stack

- **Backend:** FastAPI (async, API-first)
- **Database:** PostgreSQL with SQLAlchemy & Alembic
- **Configuration:** Pydantic Settings + `.env` support
- **Resume Parsing:** PyPDF2, python-docx
- **LLM & Embeddings:** OpenAI API, pgvector
- **Authentication:** JWT
- **Developer Tools:** Docker Compose, pytest, black, GitHub Actions

---

## 📄 Documentation

- 📑 [API Specification](docs/API_SPEC.md)
- 🗂️ [Data Model](docs/DATA_MODEL.md)
- ➕ [Full Setup Guide](docs/SETUP.md)
- ⚙️ [Project Structure](docs/PROJECT_STRUCTURE.md)
- 🧪 [Testing & CI](docs/TESTING.md)

---

For API usage, environment setup, and contribution guidelines, please refer to the linked documentation above.
