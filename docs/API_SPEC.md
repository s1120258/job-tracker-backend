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

| Method | Path                            | Description                                                        | Auth |
| ------ | ------------------------------- | ------------------------------------------------------------------ | ---- |
| GET    | `/jobs/search`                  | Search jobs from external job boards with AI-powered match scoring | ✅   |
| POST   | `/jobs/save`                    | Save a job for later                                               | ✅   |
| GET    | `/jobs`                         | List saved/matched/applied jobs                                    | ✅   |
| GET    | `/jobs/{id}`                    | Get details of a specific job                                      | ✅   |
| PUT    | `/jobs/{id}`                    | Update job status or notes                                         | ✅   |
| DELETE | `/jobs/{id}`                    | Delete a saved job                                                 | ✅   |
| POST   | `/jobs/{id}/match`              | Calculate match score for a job                                    | ✅   |
| POST   | `/jobs/{id}/apply`              | Mark job as applied                                                | ✅   |
| POST   | `/jobs/{id}/skill-gap-analysis` | Analyze skill gaps between resume and job requirements             | ✅   |
| POST   | `/jobs/{id}/extract-skills`     | Extract skills and requirements from job description               | ✅   |

**Search Parameters:**

- `keyword` (required): Search keyword for job titles, descriptions, and tags
- `location` (optional): Filter by job location
- `source` (optional): Specific job board source (e.g., "remoteok")
- `sort_by` (optional): Sort order - "date" (newest first) or "match_score" (highest match first)
- `limit` (optional): Maximum number of results (1-100, default: 20)
- `fetch_full_description` (optional): Whether to fetch complete job descriptions (default: true)

**Note:** For saved jobs management (filtering, listing), use the `GET /jobs` endpoint instead.

#### Example: Search Jobs (by Date)

**Request:**

```
GET /jobs/search?keyword=python&location=remote&source=remoteok&sort_by=match_score
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
      "date_posted": "2024-06-15",
      "salary": null,
      "board_type": "remoteok",
      "match_score": null
    }
  ],
  "total_found": 1,
  "sort_by": "date",
  "match_statistics": null,
  "search_params": {
    "keyword": "python",
    "location": "remote",
    "source": "remoteok",
    "limit": 20,
    "sort_by": "date"
  },
  "available_sources": ["remoteok"]
}
```

#### Example: Search Jobs (by Match Score)

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
      "description": "Looking for experienced Python developer with ML expertise...",
      "company": "AI Startup",
      "location": "Remote",
      "url": "https://remoteok.io/remote-jobs/789012",
      "source": "RemoteOK",
      "date_posted": "2024-06-14",
      "salary": "$100k-150k",
      "board_type": "remoteok",
      "match_score": 0.87
    },
    {
      "title": "Python Backend Engineer",
      "description": "Join our backend team building scalable APIs...",
      "company": "Tech Corp",
      "location": "Remote",
      "url": "https://remoteok.io/remote-jobs/345678",
      "source": "RemoteOK",
      "date_posted": "2024-06-13",
      "salary": "$80k-120k",
      "board_type": "remoteok",
      "match_score": 0.72
    }
  ],
  "total_found": 2,
  "sort_by": "match_score",
  "match_statistics": {
    "average_score": 0.795,
    "highest_score": 0.87,
    "lowest_score": 0.72,
    "jobs_with_scores": 2
  },
  "search_params": {
    "keyword": "python",
    "location": null,
    "source": null,
    "limit": 5,
    "sort_by": "match_score"
  },
  "available_sources": ["remoteok"]
}
```

**Note:** Match score sorting requires an uploaded resume with embedding. Jobs are ranked by similarity to your resume (0.0-1.0 scale).

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
| POST   | `/resume/extract-skills`    | Extract skills from current user's resume        | ✅   |

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

### 4. Skill Gap Analysis & Skill Extraction

| Method | Path                            | Description                                            | Auth |
| ------ | ------------------------------- | ------------------------------------------------------ | ---- |
| POST   | `/jobs/{id}/skill-gap-analysis` | Analyze skill gaps between resume and job requirements | ✅   |
| POST   | `/jobs/{id}/extract-skills`     | Extract skills and requirements from job description   | ✅   |
| POST   | `/resume/extract-skills`        | Extract skills from current user's resume              | ✅   |

#### Example: Skill Gap Analysis

**Request:**

```
POST /jobs/{job_id}/skill-gap-analysis
Content-Type: application/json

{
  "include_learning_recommendations": true,
  "include_experience_analysis": true,
  "include_education_analysis": true
}
```

**Response:**

```json
{
  "job_id": "uuid",
  "resume_id": "uuid",
  "overall_match_percentage": 78,
  "match_summary": "Strong Python background with some cloud gaps",
  "strengths": [
    {
      "skill": "Python",
      "reason": "5+ years experience exceeds requirement"
    },
    {
      "skill": "FastAPI",
      "reason": "Direct experience with required framework"
    }
  ],
  "skill_gaps": [
    {
      "skill": "Docker",
      "required_level": "Intermediate",
      "current_level": "Beginner",
      "priority": "Medium",
      "impact": "Important for deployment workflows",
      "gap_severity": "Minor"
    }
  ],
  "learning_recommendations": [
    {
      "skill": "Docker",
      "priority": "Medium",
      "estimated_learning_time": "2-3 months",
      "suggested_approach": "Hands-on practice with containerization",
      "resources": ["Docker documentation", "Online tutorials"],
      "immediate_actions": [
        "Install Docker Desktop",
        "Complete beginner tutorial"
      ]
    }
  ],
  "experience_gap": {
    "required_years": 4,
    "candidate_years": 5,
    "gap": -1,
    "assessment": "Candidate exceeds experience requirements"
  },
  "education_match": {
    "required": "Bachelor's degree in Computer Science",
    "candidate": "Bachelor's in Computer Science",
    "matches": true,
    "assessment": "Education requirements fully met"
  },
  "recommended_next_steps": [
    "Practice Docker containerization",
    "Apply with confidence highlighting Python expertise"
  ],
  "application_advice": "Strong candidate with excellent Python skills. Minor Docker gap easily addressable through focused learning.",
  "analysis_timestamp": "2024-01-15T12:00:00Z"
}
```

#### Example: Extract Job Skills

**Request:**

```
POST /jobs/{job_id}/extract-skills
```

**Response:**

```json
{
  "job_id": "uuid",
  "skills_data": {
    "required_skills": [
      {
        "name": "Python",
        "level": "Senior",
        "category": "programming_language",
        "importance": "critical"
      },
      {
        "name": "FastAPI",
        "level": "Intermediate",
        "category": "framework",
        "importance": "high"
      }
    ],
    "preferred_skills": [
      {
        "name": "Docker",
        "level": "Intermediate",
        "category": "tool",
        "importance": "medium"
      }
    ],
    "programming_languages": ["Python"],
    "frameworks": ["FastAPI"],
    "tools": ["Docker", "Git"],
    "experience_required": "3-5 years",
    "education_required": "Bachelor's degree in Computer Science",
    "seniority_level": "Senior"
  },
  "extraction_timestamp": "2024-01-15T12:00:00Z"
}
```

#### Example: Extract Resume Skills

**Request:**

```
POST /resume/extract-skills
```

**Response:**

```json
{
  "resume_id": "uuid",
  "skills_data": {
    "technical_skills": [
      {
        "name": "Python",
        "level": "Advanced",
        "years_experience": 5,
        "evidence": "5 years Python development experience"
      },
      {
        "name": "FastAPI",
        "level": "Intermediate",
        "years_experience": 2,
        "evidence": "Built REST APIs with FastAPI"
      }
    ],
    "soft_skills": ["Problem Solving", "Communication", "Teamwork"],
    "programming_languages": ["Python", "JavaScript"],
    "frameworks": ["FastAPI", "Django"],
    "tools": ["Git", "VS Code"],
    "domains": ["Web Development", "API Development"],
    "education": ["Bachelor's in Computer Science"],
    "total_experience_years": 5
  },
  "extraction_timestamp": "2024-01-15T12:00:00Z"
}
```

---

### 5. AI Resume-to-Job Matching

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

| Method | Path                             | Description                               | Auth |
| ------ | -------------------------------- | ----------------------------------------- | ---- |
| GET    | `/analytics/status-summary`      | Get count of jobs by status               | ✅   |
| GET    | `/analytics/jobs-over-time`      | Get jobs count over time (weekly/monthly) | ✅   |
| GET    | `/analytics/match-score-summary` | Get average match score across jobs       | ✅   |

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

### Skill Normalization & Intelligence

#### LLM-Based Skill Normalization

##### Normalize Skills

`POST /api/v1/jobs/skills/normalize`

Normalize skill names using LLM intelligence to standardize variations and abbreviations.

**Request Body:**

```json
{
  "skills": ["JS", "React.js", "nodejs", "AWS Lambda"],
  "context": "Frontend development" // optional
}
```

**Response:**

```json
{
  "status": "success",
  "total_processed": 4,
  "normalized_skills": [
    {
      "original": "JS",
      "canonical": "JavaScript",
      "category": "programming_language",
      "confidence": 0.95,
      "aliases": ["JS", "Javascript", "ECMAScript"],
      "related_skills": ["TypeScript", "Node.js"]
    },
    {
      "original": "React.js",
      "canonical": "React",
      "category": "frontend_framework",
      "confidence": 0.99,
      "aliases": ["React.js", "ReactJS"],
      "related_skills": ["Redux", "JSX", "Next.js"]
    },
    {
      "original": "nodejs",
      "canonical": "Node.js",
      "category": "runtime_environment",
      "confidence": 0.97,
      "aliases": ["nodejs", "NodeJS", "Node"],
      "related_skills": ["Express.js", "npm"]
    },
    {
      "original": "AWS Lambda",
      "canonical": "AWS Lambda",
      "category": "serverless_platform",
      "confidence": 1.0,
      "aliases": ["Lambda", "AWS Lambda Functions"],
      "related_skills": ["API Gateway", "CloudWatch"]
    }
  ],
  "skill_groupings": [
    {
      "group_name": "JavaScript Ecosystem",
      "skills": ["JavaScript", "React", "Node.js"]
    },
    {
      "group_name": "AWS Services",
      "skills": ["AWS Lambda"]
    }
  ]
}
```

**Features:**

- Dynamic skill normalization without static dictionaries
- Confidence scoring for normalization quality
- Skill categorization and grouping suggestions
- Context-aware processing for domain-specific skills
- Support for up to 50 skills per request

##### Compare Skills

`POST /api/v1/jobs/skills/compare`

Analyze semantic similarity between two skills using LLM intelligence.

**Request Body:**

```json
{
  "skill1": "React",
  "skill2": "Vue.js",
  "context": "Frontend frameworks" // optional
}
```

**Response:**

```json
{
  "status": "success",
  "skill1": "React",
  "skill2": "Vue.js",
  "similarity_analysis": {
    "similarity_score": 0.85,
    "confidence": 0.92,
    "relationship_type": "closely_related",
    "explanation": "Both are JavaScript frameworks with similar component-based architecture",
    "transferable_concepts": [
      "Component lifecycle",
      "State management",
      "Virtual DOM"
    ],
    "key_differences": [
      "Template syntax vs JSX",
      "Ecosystem size",
      "Performance characteristics"
    ],
    "learning_effort": "low",
    "substitutable_in_jobs": true
  }
}
```

**Relationship Types:**

- `identical` - Same skill with different names
- `closely_related` - Similar skills with high transferability
- `somewhat_related` - Some overlap but different domains
- `different_domains` - Different areas but may complement
- `unrelated` - No meaningful relationship

**Learning Effort Levels:**

- `minimal` - Almost no additional learning needed
- `low` - Few days to weeks of learning
- `moderate` - Few weeks to months
- `high` - Several months of dedicated learning
- `extensive` - Year+ of learning and experience

##### Batch Normalize Skills

`POST /api/v1/jobs/skills/batch-normalize`

Normalize multiple skill lists with different contexts in a single request.

**Request Body:**

```json
{
  "skill_batches": [
    {
      "skills": ["python", "flask", "django"],
      "context": "Backend development",
      "batch_id": "backend"
    },
    {
      "skills": ["react", "vue", "angular"],
      "context": "Frontend frameworks",
      "batch_id": "frontend"
    },
    {
      "skills": ["aws", "azure", "gcp"],
      "context": "Cloud platforms",
      "batch_id": "cloud"
    }
  ]
}
```

**Response:**

```json
{
  "status": "completed",
  "total_batches": 3,
  "successful_batches": 3,
  "failed_batches": 0,
  "results": [
    {
      "batch_id": "backend",
      "status": "success",
      "total_processed": 3,
      "normalized_skills": [
        {
          "original": "python",
          "canonical": "Python",
          "category": "programming_language",
          "confidence": 0.99
        }
        // ... more normalized skills
      ],
      "skill_groupings": [
        {
          "group_name": "Python Web Frameworks",
          "skills": ["Flask", "Django"]
        }
      ]
    }
    // ... more batch results
  ]
}
```

**Batch Limits:**

- Maximum 10 batches per request
- Maximum 20 skills per batch
- Each batch processed independently

##### Enhanced Gap Analysis Integration

The existing skill gap analysis endpoints now use these intelligent normalization features:

- **Automatic skill normalization** during extraction
- **Smart skill matching** that recognizes similar technologies
- **Transferability analysis** for related skills
- **Learning path optimization** based on existing skills

**Example Enhanced Gap Analysis Response:**

```json
{
  "intelligent_matches": [
    {
      "candidate_skill": "React",
      "required_skill": "Vue.js",
      "match_strength": 0.8,
      "reasoning": "Both are component-based frontend frameworks with transferable concepts"
    }
  ],
  "skill_gaps": [
    {
      "missing_skill": "Docker",
      "priority": "high",
      "learning_difficulty": "moderate",
      "estimated_time": "2-4 weeks",
      "prerequisites": ["Basic Linux commands"],
      "learning_path": ["Container concepts", "Docker basics", "Docker Compose"]
    }
  ],
  "normalized_analysis": {
    "total_required": 8,
    "direct_matches": 5,
    "transferable_matches": 2,
    "complete_gaps": 1,
    "match_percentage": 87.5
  },
  "learning_strategy": {
    "immediate_focus": ["Docker", "Kubernetes"],
    "medium_term": ["AWS certification"],
    "leverage_existing": "Use Python knowledge to learn DevOps automation",
    "estimated_ready_time": "6-8 weeks"
  }
}
```

**Key Advantages:**

1. **No Static Dictionaries**: Uses LLM intelligence for dynamic skill understanding
2. **Context-Aware**: Processes skills differently based on job domain and industry
3. **Confidence Scoring**: Provides reliability metrics for normalization decisions
4. **Transferability Analysis**: Recognizes when skills are similar enough to be substitutable
5. **Learning Path Optimization**: Suggests efficient learning strategies based on existing skills
6. **Comprehensive Fallbacks**: Graceful degradation when AI services are unavailable

---

For error responses and more details, see the OpenAPI schema or API docs at `/docs` when running the backend.
