# 📃 API Usage

This document provides request and response examples for using the ResMatch API.

---

## 🔍 Job Search

### Example: Search Jobs by Match Score

**Request:**

```
GET /jobs/search?keyword=python&sort_by=match_score&limit=2
```

**Response:**

```json
{
  "jobs": [
    {
      "title": "Senior Python Developer",
      "match_score": 0.87,
      "location": "Remote",
      "company": "AI Startup"
    },
    {
      "title": "Python Backend Engineer",
      "match_score": 0.72,
      "location": "Remote",
      "company": "Tech Corp"
    }
  ],
  "total_found": 2
}
```

---

## ➕ Save Job

**Request:**

```json
POST /jobs/save
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
GET /jobs/{job_id}/match-score?force_recalculate=false
```

**Response:**

```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "resume_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "similarity_score": 0.82,
  "status": "new"
}
```

---

## 📎 Apply to Job

**Request:**

```json
POST /jobs/{id}/apply
{
  "resume_id": "uuid"
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

## 📔 Skill Gap Analysis

**Request:**

```
GET /jobs/{job_id}/skill-gap-analysis?include_learning_recommendations=true&include_experience_analysis=true&include_education_analysis=true
```

**Response:**

```json
{
  "job_id": "662640fc-1959-4e0a-a51a-2a7821f49261",
  "resume_id": "3babee0b-ea76-4558-a902-d12b31e44693",
  "overall_match_percentage": 37.5,
  "match_summary": "Matched 3 of 8 required skills. Overall compatibility: 37.5%",
  "strengths": [
    {
      "skill": "Aws",
      "reason": "Intermediate level with 2 years experience meets Intermediate requirement"
    }
  ],
  "skill_gaps": [
    {
      "skill": "Flask",
      "required_level": "Intermediate",
      "current_level": "None",
      "priority": "Medium",
      "impact": "Required skill for Senior AI Python Developer position",
      "gap_severity": "Major"
    }
  ],
  "learning_recommendations": [
    {
      "skill": "Flask",
      "priority": "Medium",
      "estimated_learning_time": "4-8 weeks",
      "suggested_approach": "Focus on Flask fundamentals and practical application",
      "resources": ["Online courses", "Official documentation"],
      "immediate_actions": ["Start with Flask basics and practice"]
    }
  ],
  "experience_gap": null,
  "education_match": null,
  "recommended_next_steps": ["Priority learning: Flask"],
  "application_advice": "Limited 38% match. Focus on building fundamental skills required for this Senior AI Python Developer role before applying.",
  "analysis_timestamp": "2025-07-25T00:48:16.412742"
}
```

---

## 📄 Upload Resume

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

## 🧐 Resume Feedback (Job Specific)

**Request:**

```
GET /resume/feedback/{job_id}
```

**Response:**

```json
{
  "job_specific_feedback": [
    "**Skills Alignment:** Your skills in Python, FastAPI, database management, and AI/ML tools align well with the job requirements for an AI-Python Developer.",
    "**Experience Relevance:** Your experience as a Software Engineer working on AI integration and backend development demonstrates your ability to design and build scalable solutions.",
    "**Missing Qualifications:** While your resume showcases strong technical skills and relevant experience, consider adding more specific examples of projects where you've worked with ETL pipelines, API development, and AI/ML tools like SageMaker.",
    "**Highlighting Achievements:** Quantify your achievements where possible. For instance, mention any performance improvements or efficiency gains resulting from your contributions.",
    "**Specific Improvements:** Consider adding a project section and tailoring your summary with keywords from the job description like \"AWS architecture\", \"ETL pipelines\", and \"AI-driven solutions\"."
  ],
  "job_description_excerpt": "Senior AI Python Developer"
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
  "interviewing": 2,
  "rejected": 3,
  "offer": 1,
  "accepted": 0
}
```

---

For the full API reference, see [`API_SPEC.md`](API_SPEC.md).
