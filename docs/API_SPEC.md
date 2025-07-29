# 📁 API Specification

This document describes the API endpoints for the ResMatch backend. All endpoints are prefixed from the root (no `/api/v1`).

---

## 🔐 Authentication

- All endpoints require JWT authentication except `/auth/register` and `/auth/token`.
- Pass the JWT as a Bearer token in the `Authorization` header.

---

## 📝 Endpoints

### 💼 Jobs

| Method | Path               | Description                                                        | Auth |
| ------ | ------------------ | ------------------------------------------------------------------ | ---- |
| GET    | `/jobs/search`     | Search jobs from external job boards with AI-powered match scoring | ✅   |
| POST   | `/jobs/save`       | Save a job manually                                                | ✅   |
| GET    | `/jobs`            | List saved/matched/applied jobs                                    | ✅   |
| GET    | `/jobs/{id}`       | Get details of a specific job                                      | ✅   |
| PUT    | `/jobs/{id}`       | Update job status or notes                                         | ✅   |
| DELETE | `/jobs/{id}`       | Delete a saved job                                                 | ✅   |
| POST   | `/jobs/{id}/apply` | Mark a job as applied                                              | ✅   |

### 📄 Resume

| Method | Path      | Description                                | Auth |
| ------ | --------- | ------------------------------------------ | ---- |
| POST   | `/resume` | Upload or replace resume                   | ✅   |
| GET    | `/resume` | Retrieve current resume and extracted text | ✅   |
| DELETE | `/resume` | Delete current resume                      | ✅   |

### 🔎 Match Score

| Method | Path                     | Description                             | Auth |
| ------ | ------------------------ | --------------------------------------- | ---- |
| GET    | `/jobs/{id}/match-score` | Get match score based on current resume | ✅   |

### 🖋️ Resume Feedback

| Method | Path                        | Description                                      | Auth |
| ------ | --------------------------- | ------------------------------------------------ | ---- |
| GET    | `/resume/feedback`          | Get general LLM feedback for current resume      | ✅   |
| GET    | `/resume/feedback/{job_id}` | Get job-specific LLM feedback for current resume | ✅   |

### 📔 Skill Gap Analysis & Extraction

| Method | Path                            | Description                               | Auth |
| ------ | ------------------------------- | ----------------------------------------- | ---- |
| GET    | `/jobs/{id}/skill-gap-analysis` | Analyze skill gaps between resume and job | ✅   |
| GET    | `/jobs/{id}/skills`             | Extract skills from job description       | ✅   |
| GET    | `/resume/skills`                | Extracted skills from resume              | ✅   |

### 📊 Analytics

| Method | Path                             | Description                               | Auth |
| ------ | -------------------------------- | ----------------------------------------- | ---- |
| GET    | `/analytics/status-summary`      | Get count of jobs by status               | ✅   |
| GET    | `/analytics/jobs-over-time`      | Get jobs count over time (weekly/monthly) | ✅   |
| GET    | `/analytics/match-score-summary` | Get average match score across jobs       | ✅   |

### 🔑 Auth

| Method | Path             | Description           |
| ------ | ---------------- | --------------------- |
| POST   | `/auth/register` | Register new user     |
| POST   | `/auth/token`    | Login (JWT)           |
| GET    | `/auth/me`       | Get current user info |

---

🔗 **Live interactive API docs**: visit [`/docs`](https://res-match-api.onrender.com/docs) (Swagger UI)

For project setup and database schema, refer to the [README](../README.md) and related documentation.
