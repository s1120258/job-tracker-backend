# 🧠 ResMatch – AI-Powered Career Support Platform

**ResMatch** is an AI-powered career support platform that intelligently matches resumes with external job postings, identifies skill gaps, and offers actionable insights through a fully integrated frontend and API-first backend.

---

## 🔗 Project Structure

### 📦 Repositories

- **Backend**: [`res-match-api`](https://github.com/s1120258/res-match-api) — FastAPI-powered API with OpenAI embeddings and PostgreSQL
- **Frontend**: [`res-match-ui`](https://github.com/s1120258/res-match-ui) — React + Vite app for the user interface

### 🚀 Deployments

- **🔹 Live Demo**: [res-match-ui.vercel.app](https://res-match-ui.vercel.app)

  - Fully functional web app starting from the landing page

- **🔹 API Documentation (Swagger UI)**: [res-match-api.onrender.com/docs](https://res-match-api.onrender.com/docs)
  - Interactive API explorer via FastAPI's built-in Swagger UI

---

## 🧰 Tech Stack

| Layer           | Tools                                                     |
| --------------- | --------------------------------------------------------- |
| **Backend**     | Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic          |
| **Frontend**    | React, Vite, TypeScript, Chakra UI, Framer Motion         |
| **AI/Matching** | OpenAI (Embeddings), pgvector                             |
| **DevOps**      | Docker, GitHub Actions, Vercel, Render                    |
| **Auth**        | OAuth2, JWT                                               |
| **Parsing**     | PyPDF2, python-docx, BeautifulSoup4                       |
| **Testing**     | pytest, black (backend), React Testing Library (frontend) |

---

## 📝 Features Overview

### ✅ Job Search & Management

- Search and save jobs from external boards and sort by match score
- Track applications with statuses and scores

### 📄 Resume Management

- Upload resumes (PDF/DOCX)
- Automatically extract skills and analyze resume content
- Generate AI-powered feedback

### 🤖 Matching & Skill Gap Analysis

- Resume-to-job similarity scoring using OpenAI embeddings
- Detect missing skills and recommend learning paths

### 📊 Analytics & Reporting

- Visual summaries of applications, statuses, match scores, and trends

---

## 🔒 Authentication

- OAuth2 password flow
- JWT-secured endpoints
- Token refresh mechanism

---

## 📁 Documentation Index

### Backend Docs (`res-match-api`)

- [API_SPEC.md](./docs/API_SPEC.md)
- [DATA_MODEL.md](./docs/DATA_MODEL.md)
- [SETUP.md](./docs/SETUP.md)
- [TESTING.md](./docs/TESTING.md)
- [PROJECT_STRUCTURE.md](./docs/PROJECT_STRUCTURE.md)

### Frontend Docs (`res-match-ui`)

- [README.md](https://github.com/s1120258/res-match-ui/blob/main/README.md)
- [USER_FLOW.md](https://github.com/s1120258/res-match-ui/blob/main/docs/USER_FLOW.md)
- [DESIGN_SYSTEM.md](https://github.com/s1120258/res-match-ui/blob/main/docs/DESIGN_SYSTEM.md)

---

## ⚙️ Developer Notes

- Backend supports async API, Docker, and CI/CD via GitHub Actions
- Frontend is mobile-first, responsive, and built with Chakra UI
- Tests (unit, integration, E2E) are defined across both repos

---

_ResMatch — Empower your job search with data-driven intelligence._
