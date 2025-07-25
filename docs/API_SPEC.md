# 📁 API Specification

This document describes the API endpoints for the ResMatch backend. All endpoints are prefixed from the root (`/`).

---

## 🔐 Authentication

- All endpoints require JWT authentication except `/auth/register` and `/auth/token`.
- Pass the JWT as a Bearer token in the `Authorization` header.

---

## 📝 Endpoints

### 💼 Jobs

| Method | Path                            | Description                                                        | Auth |
| ------ | ------------------------------- | ------------------------------------------------------------------ | ---- |
| GET    | `/jobs/search`                  | Search jobs from external job boards with AI-powered match scoring | ✅   |
| POST   | `/jobs/save`                    | Save a job manually                                                | ✅   |
| GET    | `/jobs`                         | List saved/matched/applied jobs                                    | ✅   |
| GET    | `/jobs/{id}`                    | Get details of a specific job                                      | ✅   |
| PUT    | `/jobs/{id}`                    | Update job status or notes                                         | ✅   |
| DELETE | `/jobs/{id}`                    | Delete a saved job                                                 | ✅   |
| GET    | `/jobs/{id}/match-score`        | Get match score based on current resume                            | ✅   |
| GET    | `/jobs/{id}/skills`             | Extract skills from job description                                | ✅   |
| GET    | `/jobs/{id}/skill-gap-analysis` | Analyze skill gaps between resume and job                          | ✅   |
| POST   | `/jobs/{id}/apply`              | Mark a job as applied                                              | ✅   |

### 📄 Resume

| Method | Path                    | Description                                | Auth |
| ------ | ----------------------- | ------------------------------------------ | ---- |
| POST   | `/resume`               | Upload or replace resume                   | ✅   |
| GET    | `/resume`               | Retrieve current resume and extracted text | ✅   |
| DELETE | `/resume`               | Delete current resume                      | ✅   |
| GET    | `/resume/skills`        | Extracted skills from resume               | ✅   |
| GET    | `/resume/feedback`      | General resume feedback                    | ✅   |
| GET    | `/resume/feedback/{id}` | Job-specific resume feedback               | ✅   |

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
