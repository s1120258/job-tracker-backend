# 🧠 ResMatch – AI-Powered Career Support Platform

**ResMatch** leverages cutting-edge AI technology to revolutionize career development. Using **large language models** and **vector embeddings**, it provides intelligent job matching, comprehensive skill gap analysis, and personalized career insights through a production-ready, scalable architecture.

---

## 🔗 Project Overview

- **🌐 Live Application**: [resmatchai.com](https://resmatchai.com/) — Full-stack AI career platform
- **📱 Frontend Repository**: [`res-match-ui`](https://github.com/s1120258/res-match-ui) — React + Vite interface
- **🔄 API Explorer**: [resmatch-api.ddns.net/docs](https://resmatch-api.ddns.net/docs) — Interactive Swagger UI

---

## 🧰 Tech Stack

| Layer          | Tools                                                     |
| -------------- | --------------------------------------------------------- |
| **Backend**    | Python, FastAPI, SQLAlchemy, Alembic                      |
| **Database**   | PostgreSQL + pgVector extension                           |
| **Frontend**   | React, Vite, TypeScript, Chakra UI, Framer Motion         |
| **AI/ML Core** | OpenAI LLMs, Text Embeddings, Vector Similarity Search    |
| **DevOps**     | Docker, GitHub Actions, AWS EC2, Supabase, NGINX          |
| **Auth**       | OAuth2, JWT                                               |
| **Parsing**    | PyPDF2, python-docx, BeautifulSoup4                       |
| **Testing**    | pytest, black (backend), React Testing Library (frontend) |

---

## 📝 Core Features

### ✅ Job Search & Management

- Search and save jobs from external boards and sort by match score
- Track applications with statuses and scores

### 📄 Resume Management

- Upload resumes (PDF/DOCX)
- Automatically extract skills and analyze resume content
- Generate AI-powered feedback

### 🤖 AI-Powered Matching & Analysis

- **Semantic Job Matching**: Vector embeddings with 85% human judgment correlation
- **Intelligent Skill Gap Analysis**: LLM-powered skill extraction and normalization
- **Learning Path Recommendations**: Personalized development roadmaps with time estimates
- **Document Processing**: PDF/DOCX parsing with automated text extraction

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

## 🏆 Technical Achievements

- **⚡ High Performance**: ~50ms embeddings, ~1ms similarity search, sub-second API responses
- **🤖 AI-First Architecture**: Production-grade LLM integration with advanced language models
- **📊 Vector Database**: PostgreSQL + pgVector for high-performance semantic matching
- **🏢 Enterprise Ready**: Service-oriented design, OAuth2/JWT security, comprehensive testing
- **🚀 DevOps Excellence**: Docker deployment, CI/CD pipelines, monitoring, and cost optimization

**📖 For detailed technical implementation, see [TECHNICAL_ARCHITECTURE.md](./docs/TECHNICAL_ARCHITECTURE.md)**

---

_ResMatch — Empower your job search with data-driven intelligence._

