# 📂 ResMatch

**ResMatch** is an AI-powered career support platform that finds high-fit jobs and delivers insights through resume and skill gap analysis — built with FastAPI, PostgreSQL, and OpenAI embeddings.

---

## 🎯 Project Overview

ResMatch provides an API-first backend tailored for developers building intelligent job search and career support platforms. It integrates:

- External job board integration and scraping
- Resume parsing and skill extraction
- Matching resumes to jobs using semantic similarity
- Skill gap analysis with learning recommendations

Whether you’re building a job tracking dashboard, career advisor, or candidate profiling tool, ResMatch provides the intelligence layer.

---

## 🚀 Key Features

### ✅ Job Search & Tracking

- Search jobs from external job boards and sort by AI-calculated match score or date.
- Save, apply to, and manage job applications with status tracking.

### 📄 Resume Management & Feedback

- Upload resumes (PDF/DOCX) and auto-extract content.
- Receive general and job-specific LLM feedback.

### 🤖 Matching & Gap Analysis

- Leverage OpenAI embeddings and pgvector to compute resume-to-job similarity scores.
- Detect missing skills and provide targeted learning plans by analyzing experience and education gaps.

### 📊 Job Application Analytics

- Visualize stats: applications by status, match scores, and historical trends.

### 🔐 User Authentication

- JWT-secured endpoints via OAuth2 Password Flow.

### 🧪 Dev & CI Tools

- Dockerized setup, automated testing (`pytest`), code formatting (`black`), and CI/CD via GitHub Actions.

---

## 🧰 Tech Stack

| Layer            | Tools                                     |
| ---------------- | ----------------------------------------- |
| **Backend**      | FastAPI (async, API-first)                |
| **Database**     | PostgreSQL, SQLAlchemy, Alembic, pgvector |
| **AI/Embedding** | OpenAI (embedding), vector search         |
| **Parsing**      | PyPDF2, python-docx, BeautifulSoup4       |
| **Auth**         | JWT, OAuth2                               |
| **DevOps**       | Docker Compose, GitHub Actions            |
| **Testing**      | pytest, black                             |

---

## 🗂️ Documentation

- 📑 [API Spec](docs/API_SPEC.md): REAT API endpoints
- 🧬 [Data Model](docs/DATA_MODEL.md): Entity-relationship diagram and table schema
- ⚙️ [Setup Guide](docs/SETUP.md): Local dev and deployment
- 🧪 [Testing](docs/TESTING.md): Test strategy and CI
- 🧭 [Project Structure](docs/PROJECT_STRUCTURE.md)

---

_ResMatch — Empower your job search with data-driven decisions._
