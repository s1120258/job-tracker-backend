# 📂 ResMatch

**ResMatch** is an intelligent, AI-driven backend service for managing job applications, analyzing resumes, and maximizing job-fit insights — built with FastAPI, PostgreSQL, and OpenAI.

---

## 🎯 Project Overview

ResMatch offers an API-first backend tailored for developers building smarter job search and resume matching platforms. It integrates:

- External job board scraping
- Resume parsing and skill extraction
- AI-powered job-resume compatibility scoring
- Skill gap analysis with personalized learning recommendations

Whether you’re building a job tracking dashboard, career advisor, or candidate profiling tool, ResMatch provides the intelligence layer.

---

## 🚀 Key Features

### ✅ Job Search & Tracking

- Search remote jobs from boards like RemoteOK (more integrations coming).
- Save, apply, and update application status with notes.
- Sort results by AI-calculated match score or posting date.

### 📄 Resume Management & Feedback

- Upload resumes (PDF/DOCX) and auto-extract content.
- Receive general and job-specific LLM feedback.

### 🤖 AI Matching & Gap Analysis

- Use vector embeddings (OpenAI + pgvector) to compare resumes to jobs.
- Analyze experience and education gaps.
- Identify missing skills with actionable learning plans.

### 📊 Job Application Analytics

- Visualize stats: applications by status, match scores, and historical trends.

### 🔐 User Authentication

- JWT-secured endpoints for resume, job, and profile operations.

### 🧪 Dev & CI Tools

- Dockerized setup, `pytest` testing, `black` formatting, GitHub Actions CI/CD.

---

## 🧰 Tech Stack

| Layer            | Tools                                     |
| ---------------- | ----------------------------------------- |
| **Backend**      | FastAPI (async, API-first)                |
| **Database**     | PostgreSQL, SQLAlchemy, Alembic, pgvector |
| **AI/Embedding** | OpenAI API, vector search                 |
| **Parsing**      | PyPDF2, python-docx, BeautifulSoup4       |
| **Auth**         | JWT via FastAPI                           |
| **DevOps**       | Docker Compose, GitHub Actions            |
| **Testing**      | pytest, black                             |

---

## 🗂️ Documentation

- 📑 [API Spec](docs/API_SPEC.md): Endpoints and example requests/responses
- 🧬 [Data Model](docs/DATA_MODEL.md): Entity-relationship diagram and table schema
- ⚙️ [Setup Guide](docs/SETUP.md): Local dev and deployment
- 🧪 [Testing](docs/TESTING.md): Test strategy and CI
- 🧭 [Project Structure](docs/PROJECT_STRUCTURE.md)

---

_ResMatch — Empower your job search with data-driven decisions._
