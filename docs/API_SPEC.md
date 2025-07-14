# 📑 API Specification

This document describes the API endpoints for the ResMatch backend. All endpoints are prefixed from the root (no `/api/v1`).

---

For project overview, setup, and data model details, see the [README](../README.md) and other docs in this folder.

---

## 🔐 Authentication

- All endpoints require JWT authentication except `/auth/register` and `/auth/token`.
- Pass the JWT as a Bearer token in the `Authorization` header.

---

## 📝 Endpoints

### 1. Jobs

| Method | Path               | Description                     | Auth |
| ------ | ------------------ | ------------------------------- | ---- |
| GET    | `/jobs/search`     | Search jobs from job boards     | ✅   |
| POST   | `/jobs/save`       | Save a job for later            | ✅   |
| GET    | `/jobs`            | List saved/matched/applied jobs | ✅   |
| GET    | `/jobs/{id}`       | Get details of a specific job   | ✅   |
| PUT    | `/jobs/{id}`       | Update job status or notes      | ✅   |
| DELETE | `/jobs/{id}`       | Delete a saved job              | ✅   |
| POST   | `/jobs/{id}/match` | Calculate match score for a job | ✅   |
| POST   | `/jobs/{id}/apply` | Mark job as applied             | ✅   |

#### Example: Search Jobs

**Request:**

```
GET /jobs/search?keyword=python&location=remote&source=RemoteOK
```

**Response:**

```json
{
  "jobs": [
    {
      "title": "Backend Python Engineer",
      "description": "We are looking for an experienced Python developer...",
      "company": "Tech Startup",
      "location": "Remote",
      "url": "https://remoteok.io/remote-jobs/123456",
      "source": "RemoteOK",
      "date_posted": "2024-06-15"
    }
  ]
}
```

#### Example: Save Job

**Request:**

```json
{
  "title": "Backend Python Engineer",
  "description": "We are looking for an experienced Python developer...",
  "company": "Tech Startup",
  "location": "Remote",
  "url": "https://remoteok.io/remote-jobs/123456",
  "source": "RemoteOK",
  "date_posted": "2024-06-15"
}
```

**Response:**

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Backend Python Engineer",
  "description": "We are looking for an experienced Python developer...",
  "company": "Tech Startup",
  "location": "Remote",
  "url": "https://remoteok.io/remote-jobs/123456",
  "source": "RemoteOK",
  "date_posted": "2024-06-15",
  "status": "saved",
  "match_score": null,
  "job_embedding": [0.12, 0.34, 0.56],
  "created_at": "2024-06-15T12:00:00Z",
  "updated_at": "2024-06-15T12:00:00Z"
}
```

---

### 2. Resumes

| Method | Path      | Description                                | Auth |
| ------ | --------- | ------------------------------------------ | ---- |
| POST   | `/resume` | Upload/replace resume (PDF/DOCX)           | ✅   |
| GET    | `/resume` | Get current resume info and extracted text | ✅   |
| DELETE | `/resume` | Delete current resume                      | ✅   |

#### Example: Upload Resume

**Request:** `multipart/form-data` with file

**Response:**

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "file_name": "resume.pdf",
  "upload_date": "2024-06-15T12:00:00Z",
  "extracted_text": "John Doe is a software engineer...",
  "embedding": [0.12, 0.34, 0.56]
}
```

---

### 3. AI Resume Feedback

| Method | Path                        | Description                                      | Auth |
| ------ | --------------------------- | ------------------------------------------------ | ---- |
| GET    | `/resume/feedback`          | Get general LLM feedback for current resume      | ✅   |
| GET    | `/resume/feedback/{job_id}` | Get job-specific LLM feedback for current resume | ✅   |

#### Example: Get General Feedback

**Response:**

```json
{
  "general_feedback": [
    "Add more details to your experience section.",
    "Include relevant programming languages."
  ]
}
```

#### Example: Get Job-Specific Feedback

**Response:**

```json
{
  "job_specific_feedback": [
    "Emphasize experience with cloud technologies, as required by the job description.",
    "Highlight teamwork and communication skills."
  ],
  "job_description_excerpt": "We are looking for a software engineer with experience in AWS and team projects."
}
```

---

### 4. AI Resume-to-Job Matching

_Note: Matching endpoints are now integrated into the Jobs section above as `/jobs/{id}/match`_

#### Example: Calculate Match Score

**Request:**

```
POST /jobs/{job_id}/match
```

**Response:**

```json
{
  "job_id": "uuid",
  "resume_id": "uuid",
  "similarity_score": 0.82,
  "status": "matched"
}
```

#### Example: Apply to Job

**Request:**

```json
{
  "resume_id": "uuid",
  "cover_letter_template": "default"
}
```

**Response:**

```json
{
  "job_id": "uuid",
  "resume_id": "uuid",
  "status": "applied",
  "applied_at": "2024-06-15T12:00:00Z"
}
```

---

### 5. Analytics

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

### 6. Authentication

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
