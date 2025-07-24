import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json
from datetime import datetime

from app.main import app
from app.models.user import User
from app.models.job import Job, JobStatus
from app.models.resume import Resume
from app.services.skill_extraction_service import SkillExtractionServiceError

# Constants for API paths
API_V1_PREFIX = "/api/v1"


@pytest.fixture
def client():
    """Create test client."""
    from app.api.routes_auth import get_current_user
    from app.models.user import User

    # Override authentication dependency for testing
    def override_get_current_user():
        import uuid

        mock_user = User()
        mock_user.id = uuid.UUID("12345678-1234-5678-9012-123456789abc")
        mock_user.email = "test@example.com"
        return mock_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)

    yield client

    # Clean up dependency overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user():
    """Mock user for testing."""
    import uuid

    user = Mock(spec=User)
    user.id = uuid.UUID("12345678-1234-5678-9012-123456789abc")
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_job():
    """Mock job for testing."""
    import uuid

    job = Mock(spec=Job)
    job.id = uuid.UUID("87654321-4321-8765-2109-987654321def")
    job.user_id = uuid.UUID("12345678-1234-5678-9012-123456789abc")
    job.title = "Senior Python Developer"
    job.description = "Looking for a senior Python developer with FastAPI experience and Docker knowledge."
    job.company = "Tech Corp"
    job.status = JobStatus.saved
    return job


@pytest.fixture
def mock_resume():
    """Mock resume for testing."""
    import uuid

    resume = Mock(spec=Resume)
    resume.id = uuid.UUID("abcdef12-3456-7890-abcd-ef1234567890")
    resume.user_id = uuid.UUID("12345678-1234-5678-9012-123456789abc")
    resume.file_name = "resume.pdf"
    resume.extracted_text = "Experienced Python developer with 5 years in web development. Skilled in FastAPI, Django, and REST APIs. Some experience with containerization."
    return resume


@pytest.fixture
def mock_skill_gap_analysis_response():
    """Mock skill gap analysis response from service."""
    return {
        "overall_match_percentage": 78,
        "match_summary": "Strong Python background with some cloud gaps",
        "strengths": [
            {"skill": "Python", "reason": "5+ years experience exceeds requirement"},
            {"skill": "FastAPI", "reason": "Direct experience with required framework"},
        ],
        "skill_gaps": [
            {
                "skill": "Docker",
                "required_level": "Intermediate",
                "current_level": "Beginner",
                "priority": "Medium",
                "impact": "Important for deployment workflows",
                "gap_severity": "Minor",
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
                    "Complete beginner tutorial",
                ],
            }
        ],
        "experience_gap": {
            "required_years": 4,
            "candidate_years": 5,
            "gap": -1,
            "assessment": "Candidate exceeds experience requirements",
        },
        "education_match": {
            "required": "Bachelor's degree in Computer Science",
            "candidate": "Bachelor's in Computer Science",
            "matches": True,
            "assessment": "Education requirements fully met",
        },
        "recommended_next_steps": [
            "Practice Docker containerization",
            "Apply with confidence highlighting Python expertise",
        ],
        "application_advice": "Strong candidate with excellent Python skills. Minor Docker gap easily addressable through focused learning.",
    }


@pytest.fixture
def mock_resume_skills_response():
    """Mock resume skills extraction response."""
    return {
        "technical_skills": [
            {
                "name": "Python",
                "level": "Advanced",
                "years_experience": 5,
                "evidence": "5 years Python development",
            },
            {
                "name": "FastAPI",
                "level": "Intermediate",
                "years_experience": 2,
                "evidence": "Built REST APIs with FastAPI",
            },
        ],
        "soft_skills": ["Problem Solving", "Communication", "Teamwork"],
        "programming_languages": ["Python", "JavaScript"],
        "frameworks": ["FastAPI", "Django"],
        "tools": ["Git", "VS Code"],
        "domains": ["Web Development", "API Development"],
        "education": ["Bachelor's in Computer Science"],
        "total_experience_years": 5,
    }


@pytest.fixture
def mock_job_skills_response():
    """Mock job skills extraction response."""
    return {
        "required_skills": [
            {
                "name": "Python",
                "level": "Senior",
                "category": "programming_language",
                "importance": "critical",
            },
            {
                "name": "FastAPI",
                "level": "Intermediate",
                "category": "framework",
                "importance": "high",
            },
        ],
        "preferred_skills": [
            {
                "name": "Docker",
                "level": "Intermediate",
                "category": "tool",
                "importance": "medium",
            }
        ],
        "programming_languages": ["Python"],
        "frameworks": ["FastAPI"],
        "tools": ["Docker", "Git"],
        "experience_required": "3-5 years",
        "education_required": "Bachelor's degree in Computer Science",
        "seniority_level": "Senior",
    }


class TestSkillGapAnalysisAPI:
    """Integration tests for skill gap analysis API endpoints."""

    @patch("app.api.routes_jobs.get_current_user")
    @patch("app.api.routes_jobs.crud_job.get_job")
    @patch("app.api.routes_jobs.get_resume_by_user")
    @patch("app.api.routes_jobs.skill_extraction_service.analyze_skill_gap")
    def test_analyze_skill_gap_success(
        self,
        mock_analyze_skill_gap,
        mock_get_resume,
        mock_get_job,
        mock_get_current_user,
        client,
        mock_user,
        mock_job,
        mock_resume,
        mock_skill_gap_analysis_response,
    ):
        """Test successful skill gap analysis."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_get_job.return_value = mock_job
        mock_get_resume.return_value = mock_resume
        mock_analyze_skill_gap.return_value = mock_skill_gap_analysis_response

        # Make request
        response = client.post(f"{API_V1_PREFIX}/jobs/{mock_job.id}/skill-gap-analysis")

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["job_id"] == str(mock_job.id)
        assert data["resume_id"] == str(mock_resume.id)
        assert data["overall_match_percentage"] == 78
        assert len(data["strengths"]) == 2
        assert len(data["skill_gaps"]) == 1
        assert len(data["learning_recommendations"]) == 1
        assert "analysis_timestamp" in data

        # Verify service was called correctly
        mock_analyze_skill_gap.assert_called_once_with(
            resume_text=mock_resume.extracted_text,
            job_description=mock_job.description,
            job_title=mock_job.title,
        )

    @patch("app.api.routes_jobs.get_current_user")
    @patch("app.api.routes_jobs.crud_job.get_job")
    def test_analyze_skill_gap_job_not_found(
        self, mock_get_job, mock_get_current_user, client, mock_user
    ):
        """Test skill gap analysis with non-existent job."""
        mock_get_current_user.return_value = mock_user
        mock_get_job.return_value = None

        response = client.post(
            f"{API_V1_PREFIX}/jobs/00000000-0000-0000-0000-000000000000/skill-gap-analysis"
        )

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    @patch("app.api.routes_jobs.get_current_user")
    @patch("app.api.routes_jobs.crud_job.get_job")
    @patch("app.api.routes_jobs.get_resume_by_user")
    def test_analyze_skill_gap_no_resume(
        self,
        mock_get_resume,
        mock_get_job,
        mock_get_current_user,
        client,
        mock_user,
        mock_job,
    ):
        """Test skill gap analysis without user resume."""
        mock_get_current_user.return_value = mock_user
        mock_get_job.return_value = mock_job
        mock_get_resume.return_value = None

        response = client.post(f"{API_V1_PREFIX}/jobs/{mock_job.id}/skill-gap-analysis")

        assert response.status_code == 404
        assert "Resume not found" in response.json()["detail"]

    @patch("app.api.routes_jobs.get_current_user")
    @patch("app.api.routes_jobs.crud_job.get_job")
    @patch("app.api.routes_jobs.get_resume_by_user")
    def test_analyze_skill_gap_empty_resume_text(
        self,
        mock_get_resume,
        mock_get_job,
        mock_get_current_user,
        client,
        mock_user,
        mock_job,
        mock_resume,
    ):
        """Test skill gap analysis with empty resume text."""
        mock_get_current_user.return_value = mock_user
        mock_get_job.return_value = mock_job
        mock_resume.extracted_text = ""
        mock_get_resume.return_value = mock_resume

        response = client.post(f"{API_V1_PREFIX}/jobs/{mock_job.id}/skill-gap-analysis")

        assert response.status_code == 400
        assert "Resume text not available" in response.json()["detail"]

    @patch("app.api.routes_jobs.get_current_user")
    @patch("app.api.routes_jobs.crud_job.get_job")
    @patch("app.api.routes_jobs.get_resume_by_user")
    @patch("app.api.routes_jobs.skill_extraction_service.analyze_skill_gap")
    def test_analyze_skill_gap_service_error(
        self,
        mock_analyze_skill_gap,
        mock_get_resume,
        mock_get_job,
        mock_get_current_user,
        client,
        mock_user,
        mock_job,
        mock_resume,
    ):
        """Test skill gap analysis with service error."""
        mock_get_current_user.return_value = mock_user
        mock_get_job.return_value = mock_job
        mock_get_resume.return_value = mock_resume
        mock_analyze_skill_gap.side_effect = SkillExtractionServiceError(
            "Service unavailable"
        )

        response = client.post(f"{API_V1_PREFIX}/jobs/{mock_job.id}/skill-gap-analysis")

        assert response.status_code == 500
        assert "Skill analysis failed" in response.json()["detail"]

    @patch("app.api.routes_jobs.get_current_user")
    @patch("app.api.routes_jobs.crud_job.get_job")
    @patch("app.api.routes_jobs.get_resume_by_user")
    @patch("app.api.routes_jobs.skill_extraction_service.analyze_skill_gap")
    def test_analyze_skill_gap_with_request_body(
        self,
        mock_analyze_skill_gap,
        mock_get_resume,
        mock_get_job,
        mock_get_current_user,
        client,
        mock_user,
        mock_job,
        mock_resume,
        mock_skill_gap_analysis_response,
    ):
        """Test skill gap analysis with custom request parameters."""
        mock_get_current_user.return_value = mock_user
        mock_get_job.return_value = mock_job
        mock_get_resume.return_value = mock_resume
        mock_analyze_skill_gap.return_value = mock_skill_gap_analysis_response

        request_body = {
            "include_learning_recommendations": True,
            "include_experience_analysis": True,
            "include_education_analysis": False,
        }

        response = client.post(
            f"{API_V1_PREFIX}/jobs/{mock_job.id}/skill-gap-analysis", json=request_body
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_match_percentage"] == 78


class TestJobSkillExtractionAPI:
    """Integration tests for job skill extraction API endpoints."""

    @patch("app.api.routes_jobs.get_current_user")
    @patch("app.api.routes_jobs.crud_job.get_job")
    @patch("app.api.routes_jobs.skill_extraction_service.extract_skills_from_job")
    def test_extract_job_skills_success(
        self,
        mock_extract_skills,
        mock_get_job,
        mock_get_current_user,
        client,
        mock_user,
        mock_job,
        mock_job_skills_response,
    ):
        """Test successful job skills extraction."""
        mock_get_current_user.return_value = mock_user
        mock_get_job.return_value = mock_job
        mock_extract_skills.return_value = mock_job_skills_response

        response = client.post(f"{API_V1_PREFIX}/jobs/{mock_job.id}/extract-skills")

        assert response.status_code == 200
        data = response.json()

        assert data["job_id"] == str(mock_job.id)
        assert "skills_data" in data
        assert "extraction_timestamp" in data

        skills_data = data["skills_data"]
        assert len(skills_data["required_skills"]) == 2
        assert len(skills_data["preferred_skills"]) == 1
        assert skills_data["seniority_level"] == "Senior"

        mock_extract_skills.assert_called_once_with(
            job_description=mock_job.description, job_title=mock_job.title
        )

    @patch("app.api.routes_jobs.get_current_user")
    @patch("app.api.routes_jobs.crud_job.get_job")
    def test_extract_job_skills_job_not_found(
        self, mock_get_job, mock_get_current_user, client, mock_user
    ):
        """Test job skills extraction with non-existent job."""
        mock_get_current_user.return_value = mock_user
        mock_get_job.return_value = None

        response = client.post(
            f"{API_V1_PREFIX}/jobs/00000000-0000-0000-0000-000000000000/extract-skills"
        )

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    @patch("app.api.routes_jobs.get_current_user")
    @patch("app.api.routes_jobs.crud_job.get_job")
    @patch("app.api.routes_jobs.skill_extraction_service.extract_skills_from_job")
    def test_extract_job_skills_service_error(
        self,
        mock_extract_skills,
        mock_get_job,
        mock_get_current_user,
        client,
        mock_user,
        mock_job,
    ):
        """Test job skills extraction with service error."""
        mock_get_current_user.return_value = mock_user
        mock_get_job.return_value = mock_job
        mock_extract_skills.side_effect = SkillExtractionServiceError("Service error")

        response = client.post(f"{API_V1_PREFIX}/jobs/{mock_job.id}/extract-skills")

        assert response.status_code == 500
        assert "Skill extraction failed" in response.json()["detail"]


class TestResumeSkillExtractionAPI:
    """Integration tests for resume skill extraction API endpoints."""

    @patch("app.api.routes_resumes.get_current_user")
    @patch("app.api.routes_resumes.crud_resume.get_resume_by_user")
    @patch("app.api.routes_resumes.skill_extraction_service.extract_skills_from_resume")
    def test_extract_resume_skills_success(
        self,
        mock_extract_skills,
        mock_get_resume,
        mock_get_current_user,
        client,
        mock_user,
        mock_resume,
        mock_resume_skills_response,
    ):
        """Test successful resume skills extraction."""
        mock_get_current_user.return_value = mock_user
        mock_get_resume.return_value = mock_resume
        mock_extract_skills.return_value = mock_resume_skills_response

        response = client.post(f"{API_V1_PREFIX}/resume/extract-skills")

        assert response.status_code == 200
        data = response.json()

        assert data["resume_id"] == str(mock_resume.id)
        assert "skills_data" in data
        assert "extraction_timestamp" in data

        skills_data = data["skills_data"]
        assert len(skills_data["technical_skills"]) == 2
        assert skills_data["total_experience_years"] == 5
        assert "Python" in skills_data["programming_languages"]

        mock_extract_skills.assert_called_once_with(
            resume_text=mock_resume.extracted_text
        )

    @patch("app.api.routes_resumes.get_current_user")
    @patch("app.api.routes_resumes.crud_resume.get_resume_by_user")
    def test_extract_resume_skills_no_resume(
        self, mock_get_resume, mock_get_current_user, client, mock_user
    ):
        """Test resume skills extraction without user resume."""
        mock_get_current_user.return_value = mock_user
        mock_get_resume.return_value = None

        response = client.post(f"{API_V1_PREFIX}/resume/extract-skills")

        assert response.status_code == 404
        assert "Resume not found" in response.json()["detail"]

    @patch("app.api.routes_resumes.get_current_user")
    @patch("app.api.routes_resumes.crud_resume.get_resume_by_user")
    def test_extract_resume_skills_empty_text(
        self, mock_get_resume, mock_get_current_user, client, mock_user, mock_resume
    ):
        """Test resume skills extraction with empty resume text."""
        mock_get_current_user.return_value = mock_user
        mock_resume.extracted_text = ""
        mock_get_resume.return_value = mock_resume

        response = client.post(f"{API_V1_PREFIX}/resume/extract-skills")

        assert response.status_code == 400
        assert "Resume text not available" in response.json()["detail"]

    @patch("app.api.routes_resumes.get_current_user")
    @patch("app.api.routes_resumes.crud_resume.get_resume_by_user")
    @patch("app.api.routes_resumes.skill_extraction_service.extract_skills_from_resume")
    def test_extract_resume_skills_service_error(
        self,
        mock_extract_skills,
        mock_get_resume,
        mock_get_current_user,
        client,
        mock_user,
        mock_resume,
    ):
        """Test resume skills extraction with service error."""
        mock_get_current_user.return_value = mock_user
        mock_get_resume.return_value = mock_resume
        mock_extract_skills.side_effect = SkillExtractionServiceError("Service error")

        response = client.post(f"{API_V1_PREFIX}/resume/extract-skills")

        assert response.status_code == 500
        assert "Skill extraction failed" in response.json()["detail"]


class TestSkillNormalizationAPI:
    """Test cases for skill normalization API endpoints."""

    def test_normalize_skills_success(self, client, auth_headers, monkeypatch):
        """Test successful skill normalization endpoint."""

        def mock_normalize_skill_list(skills, context):
            return {
                "normalized_skills": [
                    {
                        "original": "JS",
                        "canonical": "JavaScript",
                        "category": "programming_language",
                        "confidence": 0.95,
                        "aliases": ["JS", "Javascript"],
                        "related_skills": ["TypeScript", "Node.js"],
                    },
                    {
                        "original": "React.js",
                        "canonical": "React",
                        "category": "frontend_framework",
                        "confidence": 0.99,
                        "aliases": ["React.js", "ReactJS"],
                        "related_skills": ["Redux", "JSX"],
                    },
                ],
                "suggested_groupings": [
                    {
                        "group_name": "JavaScript Ecosystem",
                        "skills": ["JavaScript", "React"],
                    }
                ],
            }

        monkeypatch.setattr(
            "app.services.skill_extraction_service.skill_extraction_service.normalize_skill_list",
            mock_normalize_skill_list,
        )

        request_data = {"skills": ["JS", "React.js"], "context": "Frontend development"}

        response = client.post(
            "/api/v1/jobs/skills/normalize", json=request_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["total_processed"] == 2
        assert len(data["normalized_skills"]) == 2
        assert data["normalized_skills"][0]["canonical"] == "JavaScript"
        assert len(data["skill_groupings"]) == 1

    def test_normalize_skills_empty_list(self, client, auth_headers):
        """Test normalization with empty skills list."""
        request_data = {"skills": [], "context": "Test context"}

        response = client.post(
            "/api/v1/jobs/skills/normalize", json=request_data, headers=auth_headers
        )

        assert response.status_code == 400
        assert "Skills list cannot be empty" in response.json()["detail"]

    def test_normalize_skills_too_many(self, client, auth_headers):
        """Test normalization with too many skills."""
        request_data = {
            "skills": [f"skill_{i}" for i in range(51)],  # 51 skills
            "context": "Test context",
        }

        response = client.post(
            "/api/v1/jobs/skills/normalize", json=request_data, headers=auth_headers
        )

        assert response.status_code == 400
        assert "Maximum 50 skills allowed" in response.json()["detail"]

    def test_normalize_skills_service_error(self, client, auth_headers, monkeypatch):
        """Test normalization with service error."""

        def mock_normalize_error(*args, **kwargs):
            raise SkillExtractionServiceError("Service error")

        monkeypatch.setattr(
            "app.services.skill_extraction_service.skill_extraction_service.normalize_skill_list",
            mock_normalize_error,
        )

        request_data = {"skills": ["Python", "Java"], "context": "Backend"}

        response = client.post(
            "/api/v1/jobs/skills/normalize", json=request_data, headers=auth_headers
        )

        assert response.status_code == 500
        assert "Skill normalization failed" in response.json()["detail"]

    def test_compare_skills_success(self, client, auth_headers, monkeypatch):
        """Test successful skill comparison endpoint."""

        def mock_compare_skills(skill1, skill2, context):
            return {
                "similarity_score": 0.85,
                "confidence": 0.92,
                "relationship_type": "closely_related",
                "explanation": "Both are JavaScript frameworks with similar component-based architecture",
                "transferable_concepts": ["Component lifecycle", "State management"],
                "key_differences": ["Syntax", "Ecosystem"],
                "learning_effort": "low",
                "substitutable_in_jobs": True,
            }

        monkeypatch.setattr(
            "app.services.skill_extraction_service.skill_extraction_service.compare_skills",
            mock_compare_skills,
        )

        request_data = {
            "skill1": "React",
            "skill2": "Vue.js",
            "context": "Frontend frameworks",
        }

        response = client.post(
            "/api/v1/jobs/skills/compare", json=request_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["skill1"] == "React"
        assert data["skill2"] == "Vue.js"
        assert data["similarity_analysis"]["similarity_score"] == 0.85
        assert data["similarity_analysis"]["relationship_type"] == "closely_related"

    def test_compare_skills_missing_skill(self, client, auth_headers):
        """Test skill comparison with missing skill."""
        request_data = {
            "skill1": "React",
            "skill2": "",  # Empty skill2
            "context": "Frontend",
        }

        response = client.post(
            "/api/v1/jobs/skills/compare", json=request_data, headers=auth_headers
        )

        assert response.status_code == 400
        assert "Both skill1 and skill2 must be provided" in response.json()["detail"]

    def test_compare_skills_service_error(self, client, auth_headers, monkeypatch):
        """Test skill comparison with service error."""

        def mock_compare_error(*args, **kwargs):
            raise SkillExtractionServiceError("Comparison failed")

        monkeypatch.setattr(
            "app.services.skill_extraction_service.skill_extraction_service.compare_skills",
            mock_compare_error,
        )

        request_data = {
            "skill1": "Python",
            "skill2": "Java",
            "context": "Programming languages",
        }

        response = client.post(
            "/api/v1/jobs/skills/compare", json=request_data, headers=auth_headers
        )

        assert response.status_code == 500
        assert "Skill comparison failed" in response.json()["detail"]

    def test_batch_normalize_skills_success(self, client, auth_headers, monkeypatch):
        """Test successful batch skill normalization."""

        def mock_normalize_skill_list(skills, context):
            return {
                "normalized_skills": [
                    {"original": skill, "canonical": skill.title(), "confidence": 0.9}
                    for skill in skills
                ],
                "suggested_groupings": [],
            }

        monkeypatch.setattr(
            "app.services.skill_extraction_service.skill_extraction_service.normalize_skill_list",
            mock_normalize_skill_list,
        )

        request_data = {
            "skill_batches": [
                {
                    "skills": ["python", "java"],
                    "context": "Backend languages",
                    "batch_id": "backend",
                },
                {
                    "skills": ["react", "vue"],
                    "context": "Frontend frameworks",
                    "batch_id": "frontend",
                },
            ]
        }

        response = client.post(
            "/api/v1/jobs/skills/batch-normalize",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["total_batches"] == 2
        assert data["successful_batches"] == 2
        assert data["failed_batches"] == 0
        assert len(data["results"]) == 2

        # Check individual batch results
        backend_result = next(r for r in data["results"] if r["batch_id"] == "backend")
        assert backend_result["status"] == "success"
        assert backend_result["total_processed"] == 2

    def test_batch_normalize_empty_batches(self, client, auth_headers):
        """Test batch normalization with empty batch list."""
        request_data = {"skill_batches": []}

        response = client.post(
            "/api/v1/jobs/skills/batch-normalize",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "skill_batches cannot be empty" in response.json()["detail"]

    def test_batch_normalize_too_many_batches(self, client, auth_headers):
        """Test batch normalization with too many batches."""
        request_data = {
            "skill_batches": [
                {"skills": ["test"], "context": "test", "batch_id": f"batch_{i}"}
                for i in range(11)  # 11 batches
            ]
        }

        response = client.post(
            "/api/v1/jobs/skills/batch-normalize",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Maximum 10 batches allowed" in response.json()["detail"]

    def test_batch_normalize_mixed_results(self, client, auth_headers, monkeypatch):
        """Test batch normalization with mixed success/failure results."""

        def mock_normalize_skill_list(skills, context):
            if "error" in skills:
                raise Exception("Normalization failed")
            return {
                "normalized_skills": [
                    {"original": skill, "canonical": skill.title(), "confidence": 0.9}
                    for skill in skills
                ],
                "suggested_groupings": [],
            }

        monkeypatch.setattr(
            "app.services.skill_extraction_service.skill_extraction_service.normalize_skill_list",
            mock_normalize_skill_list,
        )

        request_data = {
            "skill_batches": [
                {
                    "skills": ["python", "java"],
                    "context": "Success batch",
                    "batch_id": "success",
                },
                {"skills": ["error"], "context": "Error batch", "batch_id": "error"},
                {
                    "skills": [],  # Empty skills
                    "context": "Empty batch",
                    "batch_id": "empty",
                },
                {
                    "skills": [f"skill_{i}" for i in range(25)],  # Too many skills
                    "context": "Large batch",
                    "batch_id": "large",
                },
            ]
        }

        response = client.post(
            "/api/v1/jobs/skills/batch-normalize",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["total_batches"] == 4
        assert data["successful_batches"] == 1  # Only the success batch
        assert data["failed_batches"] == 3

        # Check individual results
        results_by_id = {r["batch_id"]: r for r in data["results"]}

        assert results_by_id["success"]["status"] == "success"
        assert results_by_id["error"]["status"] == "error"
        assert results_by_id["empty"]["status"] == "error"
        assert "empty" in results_by_id["empty"]["error"]
        assert results_by_id["large"]["status"] == "error"
        assert "Maximum 20 skills" in results_by_id["large"]["error"]

    def test_normalize_skills_unauthorized(self, client):
        """Test skill normalization without authentication."""
        request_data = {"skills": ["Python", "Java"], "context": "Programming"}

        response = client.post("/api/v1/jobs/skills/normalize", json=request_data)

        assert response.status_code == 401

    def test_compare_skills_unauthorized(self, client):
        """Test skill comparison without authentication."""
        request_data = {"skill1": "React", "skill2": "Vue.js", "context": "Frontend"}

        response = client.post("/api/v1/jobs/skills/compare", json=request_data)

        assert response.status_code == 401

    def test_batch_normalize_unauthorized(self, client):
        """Test batch normalization without authentication."""
        request_data = {"skill_batches": [{"skills": ["test"], "context": "test"}]}

        response = client.post("/api/v1/jobs/skills/batch-normalize", json=request_data)

        assert response.status_code == 401


class TestSkillGapAnalysisPermissions:
    """Test permission and ownership checks for skill gap analysis."""

    @patch("app.api.routes_jobs.get_current_user")
    @patch("app.api.routes_jobs.crud_job.get_job")
    def test_analyze_skill_gap_wrong_user(
        self, mock_get_job, mock_get_current_user, client, mock_user, mock_job
    ):
        """Test skill gap analysis with job belonging to different user."""
        mock_get_current_user.return_value = mock_user
        mock_job.user_id = "different-user-id"  # Different from mock_user.id
        mock_get_job.return_value = mock_job

        response = client.post(f"{API_V1_PREFIX}/jobs/{mock_job.id}/skill-gap-analysis")

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    @patch("app.api.routes_jobs.get_current_user")
    @patch("app.api.routes_jobs.crud_job.get_job")
    def test_extract_job_skills_wrong_user(
        self, mock_get_job, mock_get_current_user, client, mock_user, mock_job
    ):
        """Test job skills extraction with job belonging to different user."""
        mock_get_current_user.return_value = mock_user
        mock_job.user_id = "different-user-id"
        mock_get_job.return_value = mock_job

        response = client.post(f"{API_V1_PREFIX}/jobs/{mock_job.id}/extract-skills")

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]
