# 📑 API Specification

This document describes the API endpoints for the Job Tracker backend. All endpoints are prefixed from the root (no `/api/v1`).

---

For project overview, setup, and data model details, see the [README](../README.md) and other docs in this folder.

---

## 🔐 Authentication

- All endpoints require JWT authentication except `/auth/register` and `/auth/token`.
- Pass the JWT as a Bearer token in the `Authorization` header.

---

## 📝 Endpoints

### 1. Applications

| Method | Path                 | Description                            | Auth |
| ------ | -------------------- | -------------------------------------- | ---- |
| GET    | `/applications`      | List all job applications (filterable) | ✅   |
| POST   | `/applications`      | Create a new job application           | ✅   |
| GET    | `/applications/{id}` | Get details of a job application       | ✅   |
| PUT    | `/applications/{id}` | Update a job application               | ✅   |
| DELETE | `/applications/{id}` | Delete a job application               | ✅   |

#### Example: Create Application

**Request:**

```json
{
  "company_name": "Acme Corp",
  "position_title": "Software Engineer",
  "application_status": "applied",
  "applied_date": "2024-06-15",
  "interview_date": null,
  "offer_date": null,
  "notes": "First round scheduled",
  "job_description_text": "We are looking for..."
}
```

**Response:**

```json
{
  "id": "uuid",
  "company_name": "Acme Corp",
  "position_title": "Software Engineer",
  "application_status": "applied",
  "applied_date": "2024-06-15",
  "interview_date": null,
  "offer_date": null,
  "notes": "First round scheduled",
  "job_description_text": "We are looking for...",
  "created_at": "2024-06-15T12:00:00Z",
  "updated_at": "2024-06-15T12:00:00Z"
}
```

---

### 2. Resumes

| Method | Path             | Description                                               | Auth |
| ------ | ---------------- | --------------------------------------------------------- | ---- |
| POST   | `/resume/upload` | Upload/replace resume (PDF/DOCX)                          | ✅   |
| GET    | `/resume`        | Get current resume info, extracted text, and LLM feedback | ✅   |
| DELETE | `/resume`        | Delete current resume                                     | ✅   |

#### Example: Upload Resume

**Request:** `multipart/form-data` with file

**Response:**

```json
{
  "id": "uuid",
  "file_name": "resume.pdf",
  "upload_date": "2024-06-15T12:00:00Z",
  "extracted_text": "John Doe is a software engineer...",
  "llm_feedback": "Consider adding more detail to your experience section."
}
```

---

### 3. AI Resume-to-Job Matching

| Method | Path                                 | Description                                             | Auth |
| ------ | ------------------------------------ | ------------------------------------------------------- | ---- |
| GET    | `/applications/{id}/match-score`     | Get similarity score between resume and job description | ✅   |
| POST   | `/applications/{id}/recompute-match` | Recompute match score                                   | ✅   |

#### Example: Get Match Score

**Response:**

```json
{
  "application_id": "uuid",
  "resume_id": "uuid",
  "similarity_score": 0.82
}
```

---

### 4. Analytics

| Method | Path                                | Description                                       | Auth |
| ------ | ----------------------------------- | ------------------------------------------------- | ---- |
| GET    | `/analytics/status-summary`         | Get count of applications by status               | ✅   |
| GET    | `/analytics/applications-over-time` | Get applications count over time (weekly/monthly) | ✅   |
| GET    | `/analytics/match-score-summary`    | Get average match score across applications       | ✅   |

#### Example: Status Summary

**Response:**

```json
{
  "applied": 5,
  "interviewing": 2,
  "rejected": 3,
  "offer": 1,
  "accepted": 0
}
```

---

### 5. Authentication

| Method | Path             | Description           |
| ------ | ---------------- | --------------------- |
| POST   | `/auth/register` | Register new user     |
| POST   | `/auth/token`    | Login (JWT)           |
| GET    | `/auth/me`       | Get current user info |

#### Example: Register

**Request:**

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**

```json
{
  "id": "uuid",
  "email": "user@example.com"
}
```

#### Example: Login

**Request:** `application/x-www-form-urlencoded` (`username`, `password`)

**Response:**

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

#### Example: Get Current User

**Response:**

```json
{
  "id": "uuid",
  "email": "user@example.com"
}
```

---

For error responses and more details, see the OpenAPI schema or API docs at `/docs` when running the backend.
