# 🧠 ResMatch – AI-Powered Career Support Platform

**ResMatch** is an AI-powered career support platform that intelligently matches resumes with external job postings, identifies skill gaps, and offers actionable insights through a fully integrated frontend and API-first backend.

---

## 🔗 Project Overview

- **🌐 Live Application**: [res-match-ui.vercel.app](https://res-match-ui.vercel.app) — Full-stack AI career platform
- **📱 Frontend Repository**: [`res-match-ui`](https://github.com/s1120258/res-match-ui) — React + Vite interface
- **🔄 API Explorer**: [res-match-api.onrender.com/docs](https://res-match-api.onrender.com/docs) — Interactive Swagger UI

---

## 🧰 Tech Stack

| Layer          | Tools                                                      |
| -------------- | ---------------------------------------------------------- |
| **Backend**    | Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic           |
| **Frontend**   | React, Vite, TypeScript, Chakra UI, Framer Motion          |
| **AI/ML Core** | **OpenAI GPT-3.5-turbo, text-embedding-ada-002, pgvector** |
| **Vector DB**  | **PostgreSQL + pgVector extension (1536-dim embeddings)**  |
| **DevOps**     | Docker, GitHub Actions, Vercel, Render                     |
| **Auth**       | OAuth2, JWT                                                |
| **Parsing**    | PyPDF2, python-docx, BeautifulSoup4                        |
| **Testing**    | pytest, black (backend), React Testing Library (frontend)  |

### 🤖 AI/ML Capabilities

- **Semantic Job Matching**: Vector embeddings with cosine similarity
- **LLM-Powered Analysis**: Intelligent skill extraction and gap analysis
- **Document Processing**: PDF/DOCX parsing with automated text extraction
- **Skill Normalization**: Dynamic standardization using language models
- **Performance**: ~50ms embeddings, ~1ms similarity, sub-second responses

---

## 📝 Core Features

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

### 🔒 Security & Authentication

- OAuth2 password flow with JWT tokens
- Secure endpoints with token refresh mechanism
- bcrypt password hashing and SQL injection prevention

---

## 📁 Documentation

### 📖 Technical Documentation

- **[🧠 TECHNICAL_ARCHITECTURE.md](./docs/TECHNICAL_ARCHITECTURE.md)** — Comprehensive AI/ML system architecture and implementation details
- [📁 API_SPEC.md](./docs/API_SPEC.md) — Complete API reference with AI-powered endpoint descriptions
- [🗂️ DATA_MODEL.md](./docs/DATA_MODEL.md) — Database schema and vector storage specifications

### 🛠️ Development Setup

- [⚙️ SETUP.md](./docs/SETUP.md) — Environment setup and installation guide
- [🧪 TESTING.md](./docs/TESTING.md) — Testing strategies and best practices

---

## 🏆 Technical Highlights

- **AI-First Architecture**: Built on OpenAI's state-of-the-art language models
- **Vector-Powered Search**: High-performance semantic matching with pgVector
- **Scalable Design**: Service-oriented architecture with comprehensive error handling
- **Production Ready**: Docker deployment, CI/CD, monitoring, and cost optimization
- **Modern Stack**: Async API, mobile-first UI, comprehensive test coverage

**📖 For detailed technical implementation, see [TECHNICAL_ARCHITECTURE.md](./docs/TECHNICAL_ARCHITECTURE.md)**

---

_ResMatch — Empower your job search with data-driven intelligence._
