# 📃 API Usage Examples - ResMatch API

This document provides request and response examples for using the ResMatch API.

---

## 🔍 Job Search

### Example: Search by Match Score

**Request:**

```
GET /jobs/search?keyword=python&sort_by=match_score&limit=5
```

**Response:**

```json
{
  "jobs": [
    {
      "title": "Senior Python Developer",
      "match_score": 0.87,
      "location": "Remote",
      "url": "https://remoteok.io/remote-jobs/789012"
    }
  ],
  "total_found": 1,
  "sort_by": "match_score"
}
```

---

## 🔍 Job Detail

**Request:**

```
GET /jobs/1234
```

**Response:**

```json
{
  "title": "Backend Python Engineer",
  "description": "We are looking for...",
  "company": "Tech Startup",
  "location": "Remote"
}
```

---

## ➕ Save Job

**Request:**

```
POST /jobs
```

```json
{
  "title": "Backend Python Engineer",
  "url": "https://remoteok.io/remote-jobs/123456"
}
```

**Response:**

```json
{
  "id": "uuid",
  "status": "saved"
}
```

---

## 🔎 Match Score

**Request:**

```
GET /jobs/{id}/match-score
```

**Response:**

```json
{
  "similarity_score": 0.82
}
```

---

## 🧠 Skill Gap Analysis

**Request:**

```
GET /jobs/{id}/skill-gap-analysis
```

**Response:**

```json
{
  "overall_match_percentage": 78,
  "skill_gaps": [{ "skill": "Docker", "gap_severity": "Minor" }]
}
```

---

## 📔 Resume Upload

**Request:**

```
POST /resume
Content-Type: multipart/form-data
```

**Response:**

```json
{
  "file_name": "resume.pdf",
  "upload_date": "2024-06-15T12:00:00Z"
}
```

---

## 🧐 Resume Feedback

**Request:**

```
GET /resume/feedback
```

**Response:**

```json
{
  "general_feedback": ["Add more details to your experience section."]
}
```

**Request (Job-Specific):**

```
GET /resume/feedback/{job_id}
```

**Response:**

```json
{
  "job_specific_feedback": ["Highlight AWS experience."]
}
```

---

## 🔢 Apply to Job

**Request:**

```
POST /jobs/{id}/apply
```

```json
{
  "resume_id": "uuid"
}
```

**Response:**

```json
{
  "status": "applied",
  "applied_at": "2024-06-15T12:00:00Z"
}
```

---

## 📊 Analytics Summary

**Request:**

```
GET /analytics/status-summary
```

**Response:**

```json
{
  "applied": 5,
  "interviewing": 2
}
```

---

For the full API reference, see [`API_SPEC.md`](API_SPEC.md).
