"""
Unit tests for skill-related API endpoints.

Tests cover:
- /jobs/{job_id}/skills (Job skill extraction)
- /resume/skills (Resume skill extraction)
- /jobs/{job_id}/skill-gap-analysis (Skill gap analysis)
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime
from uuid import UUID, uuid4

from app.main import app
from app.api.routes_auth import get_current_user
from app.models.user import User
from app.services.skill_extraction_service import SkillExtractionServiceError
from app.services.skill_analysis_service import SkillAnalysisServiceError

# Test client
client = TestClient(app)

# API prefix for versioning
API_V1_PREFIX = "/api/v1"


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    user = Mock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_job(mock_user):
    """Mock job object"""
    job = Mock()
    job.id = uuid4()
    job.user_id = mock_user.id
    job.title = "Senior Python Developer"
    job.description = "We are looking for a senior Python developer with experience in FastAPI, PostgreSQL, and AWS."
    return job


@pytest.fixture
def mock_resume(mock_user):
    """Mock resume object"""
    resume = Mock()
    resume.id = uuid4()
    resume.user_id = mock_user.id
    resume.extracted_text = "Experienced Python developer with 5 years of experience in web development using Django and FastAPI."
    return resume


@pytest.fixture
def mock_skills_data():
    """Mock skill extraction response data"""
    return {
        "required_skills": [
            {
                "name": "Python",
                "level": "Senior",
                "category": "programming_language",
                "importance": "critical",
            }
        ],
        "preferred_skills": [
            {
                "name": "AWS",
                "level": "Intermediate",
                "category": "cloud_platform",
                "importance": "medium",
            }
        ],
        "programming_languages": ["Python"],
        "frameworks": ["FastAPI"],
        "tools": [],
        "cloud_platforms": ["AWS"],
        "databases": ["PostgreSQL"],
        "soft_skills": [],
        "certifications": [],
        "experience_required": "5+ years",
        "education_required": "Bachelor's degree",
        "seniority_level": "Senior",
    }


@pytest.fixture
def mock_resume_skills_data():
    """Mock resume skill extraction response data"""
    return {
        "technical_skills": [
            {
                "name": "Python",
                "level": "Advanced",
                "years_experience": 5,
                "evidence": "5 years as Python developer",
            }
        ],
        "soft_skills": ["Communication", "Problem Solving"],
        "certifications": [],
        "programming_languages": ["Python"],
        "frameworks": ["Django", "FastAPI"],
        "tools": ["Git"],
        "domains": ["Web Development"],
        "education": ["Bachelor's in Computer Science"],
        "total_experience_years": 5,
    }


@pytest.fixture
def mock_gap_analysis_data(mock_job, mock_resume):
    """Mock skill gap analysis response data"""
    return {
        "overall_match_percentage": 75.0,
        "match_summary": "Strong technical background with some gaps in cloud technologies",
        "strengths": [
            {
                "skill": "Python",
                "reason": "5+ years experience matches senior requirement",
            }
        ],
        "skill_gaps": [
            {
                "skill": "AWS",
                "required_level": "Intermediate",
                "current_level": "None",
                "priority": "High",
                "impact": "Critical for cloud deployment responsibilities",
                "gap_severity": "Major",
            }
        ],
        "learning_recommendations": [
            {
                "skill": "AWS",
                "priority": "High",
                "estimated_learning_time": "3-6 months",
                "suggested_approach": "Start with AWS Certified Cloud Practitioner",
                "resources": ["AWS Training", "Cloud Academy"],
                "immediate_actions": ["Sign up for AWS free tier"],
            }
        ],
        "experience_gap": {
            "required_years": 5,
            "candidate_years": 5,
            "gap": 0,
            "assessment": "Experience requirements met",
        },
        "education_match": {
            "required": "Bachelor's in Computer Science",
            "candidate": "Bachelor's in Computer Science",
            "matches": True,
            "assessment": "Education requirements fully met",
        },
        "recommended_next_steps": [
            "Focus on AWS certification and hands-on cloud projects"
        ],
        "application_advice": "Strong candidate with core skills. Address cloud technology gaps through learning plan.",
    }


@pytest.fixture(autouse=True)
def setup_auth(mock_user):
    """Setup authentication for all tests"""

    def mock_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.clear()


class TestJobSkillsExtraction:
    """Test job skills extraction endpoint (/jobs/{job_id}/skills)"""

    @patch("app.api.routes_jobs.crud_job.get_job")
    @patch("app.api.routes_jobs.skill_extraction_service.extract_skills_from_job")
    def test_extract_job_skills_success(
        self, mock_extract_skills, mock_get_job, mock_user, mock_job, mock_skills_data
    ):
        """Test successful job skills extraction"""
        # Setup mocks
        mock_get_job.return_value = mock_job
        mock_extract_skills.return_value = mock_skills_data

        # Make request
        response = client.get(f"{API_V1_PREFIX}/jobs/{mock_job.id}/skills")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == str(mock_job.id)
        assert "skills_data" in data
        assert "extraction_timestamp" in data
        assert data["skills_data"]["required_skills"][0]["name"] == "Python"

        # Verify service was called correctly with normalization enabled
        mock_extract_skills.assert_called_once_with(
            job_description=mock_job.description,
            job_title=mock_job.title,
            normalize=True,
        )

    @patch("app.api.routes_jobs.crud_job.get_job")
    def test_extract_job_skills_job_not_found(self, mock_get_job, mock_user):
        """Test job not found error"""
        mock_get_job.return_value = None

        non_existent_job_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"{API_V1_PREFIX}/jobs/{non_existent_job_id}/skills")

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    @patch("app.api.routes_jobs.crud_job.get_job")
    @patch("app.api.routes_jobs.skill_extraction_service.extract_skills_from_job")
    def test_extract_job_skills_service_error(
        self, mock_extract_skills, mock_get_job, mock_user, mock_job
    ):
        """Test skill extraction service error"""
        mock_get_job.return_value = mock_job
        mock_extract_skills.side_effect = SkillExtractionServiceError("Service error")

        response = client.get(f"{API_V1_PREFIX}/jobs/{mock_job.id}/skills")

        assert response.status_code == 500
        assert "Skill extraction failed" in response.json()["detail"]


class TestResumeSkillsExtraction:
    """Test resume skills extraction endpoint (/resume/skills)"""

    @patch("app.api.routes_resumes.crud_resume.get_resume_by_user")
    @patch("app.api.routes_resumes.skill_extraction_service.extract_skills_from_resume")
    def test_extract_resume_skills_success(
        self,
        mock_extract_skills,
        mock_get_resume,
        mock_user,
        mock_resume,
        mock_resume_skills_data,
    ):
        """Test successful resume skills extraction"""
        # Setup mocks
        mock_get_resume.return_value = mock_resume
        mock_extract_skills.return_value = mock_resume_skills_data

        # Make request
        response = client.get(f"{API_V1_PREFIX}/resume/skills")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["resume_id"] == str(mock_resume.id)
        assert "skills_data" in data
        assert "extraction_timestamp" in data
        assert data["skills_data"]["technical_skills"][0]["name"] == "Python"
        assert data["skills_data"]["total_experience_years"] == 5

        # Verify service was called correctly with normalization enabled
        mock_extract_skills.assert_called_once_with(
            resume_text=mock_resume.extracted_text, normalize=True
        )

    @patch("app.api.routes_resumes.crud_resume.get_resume_by_user")
    def test_extract_resume_skills_no_resume(self, mock_get_resume, mock_user):
        """Test when user has no resume"""
        mock_get_resume.return_value = None

        response = client.get(f"{API_V1_PREFIX}/resume/skills")

        assert response.status_code == 404
        assert "Resume not found" in response.json()["detail"]

    @patch("app.api.routes_resumes.crud_resume.get_resume_by_user")
    def test_extract_resume_skills_empty_text(
        self, mock_get_resume, mock_user, mock_resume
    ):
        """Test when resume has no extracted text"""
        mock_resume.extracted_text = ""
        mock_get_resume.return_value = mock_resume

        response = client.get(f"{API_V1_PREFIX}/resume/skills")

        assert response.status_code == 400
        assert "Resume text not available" in response.json()["detail"]


class TestSkillGapAnalysis:
    """Test skill gap analysis endpoint (/jobs/{job_id}/skill-gap-analysis)"""

    @patch("app.api.routes_jobs.crud_job.get_job")
    @patch("app.api.routes_jobs.get_resume_by_user")
    @patch("app.api.routes_jobs.skill_extraction_service.extract_skills_from_resume")
    @patch("app.api.routes_jobs.skill_extraction_service.extract_skills_from_job")
    @patch("app.api.routes_jobs.skill_analysis_service.analyze_skill_gap")
    def test_analyze_skill_gap_success(
        self,
        mock_analyze_gap,
        mock_extract_job_skills,
        mock_extract_resume_skills,
        mock_get_resume,
        mock_get_job,
        mock_user,
        mock_job,
        mock_resume,
        mock_gap_analysis_data,
    ):
        """Test successful skill gap analysis"""
        # Setup mocks
        mock_get_job.return_value = mock_job
        mock_get_resume.return_value = mock_resume
        mock_extract_resume_skills.return_value = {
            "technical_skills": [],
            "programming_languages": ["Python"],
        }
        mock_extract_job_skills.return_value = {
            "required_skills": [],
            "programming_languages": ["Python"],
        }
        mock_analyze_gap.return_value = mock_gap_analysis_data

        # Make request
        response = client.get(f"{API_V1_PREFIX}/jobs/{mock_job.id}/skill-gap-analysis")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == str(mock_job.id)
        assert data["resume_id"] == str(mock_resume.id)
        assert data["overall_match_percentage"] == 75.0
        assert "analysis_timestamp" in data
        assert len(data["strengths"]) == 1
        assert len(data["skill_gaps"]) == 1

        # Verify services were called correctly with normalization enabled
        mock_extract_resume_skills.assert_called_once_with(
            resume_text=mock_resume.extracted_text, normalize=True
        )
        mock_extract_job_skills.assert_called_once_with(
            job_description=mock_job.description,
            job_title=mock_job.title,
            normalize=True,
        )
        mock_analyze_gap.assert_called_once_with(
            resume_skills_data={
                "technical_skills": [],
                "programming_languages": ["Python"],
            },
            job_skills_data={
                "required_skills": [],
                "programming_languages": ["Python"],
            },
            job_title=mock_job.title,
            normalize=True,
        )

    @patch("app.api.routes_jobs.crud_job.get_job")
    def test_analyze_skill_gap_job_not_found(self, mock_get_job, mock_user):
        """Test job not found error"""
        mock_get_job.return_value = None

        non_existent_job_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(
            f"{API_V1_PREFIX}/jobs/{non_existent_job_id}/skill-gap-analysis"
        )

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    @patch("app.api.routes_jobs.crud_job.get_job")
    @patch("app.api.routes_jobs.get_resume_by_user")
    def test_analyze_skill_gap_no_resume(
        self, mock_get_resume, mock_get_job, mock_user, mock_job
    ):
        """Test when user has no resume"""
        mock_get_job.return_value = mock_job
        mock_get_resume.return_value = None

        response = client.get(f"{API_V1_PREFIX}/jobs/{mock_job.id}/skill-gap-analysis")

        assert response.status_code == 404
        assert "Resume not found" in response.json()["detail"]

    @patch("app.api.routes_jobs.crud_job.get_job")
    @patch("app.api.routes_jobs.get_resume_by_user")
    def test_analyze_skill_gap_empty_resume_text(
        self, mock_get_resume, mock_get_job, mock_user, mock_job, mock_resume
    ):
        """Test when resume has no extracted text"""
        mock_get_job.return_value = mock_job
        mock_resume.extracted_text = ""
        mock_get_resume.return_value = mock_resume

        response = client.get(f"{API_V1_PREFIX}/jobs/{mock_job.id}/skill-gap-analysis")

        assert response.status_code == 400
        assert "Resume text not available" in response.json()["detail"]

    @patch("app.api.routes_jobs.crud_job.get_job")
    @patch("app.api.routes_jobs.get_resume_by_user")
    @patch("app.api.routes_jobs.skill_extraction_service.extract_skills_from_resume")
    @patch("app.api.routes_jobs.skill_extraction_service.extract_skills_from_job")
    @patch("app.api.routes_jobs.skill_analysis_service.analyze_skill_gap")
    def test_analyze_skill_gap_service_error(
        self,
        mock_analyze_gap,
        mock_extract_job_skills,
        mock_extract_resume_skills,
        mock_get_resume,
        mock_get_job,
        mock_user,
        mock_job,
        mock_resume,
    ):
        """Test skill analysis service error"""
        mock_get_job.return_value = mock_job
        mock_get_resume.return_value = mock_resume
        mock_extract_resume_skills.return_value = {"technical_skills": []}
        mock_extract_job_skills.side_effect = SkillExtractionServiceError(
            "Service error"
        )

        response = client.get(f"{API_V1_PREFIX}/jobs/{mock_job.id}/skill-gap-analysis")

        assert response.status_code == 500
        assert "Skill analysis failed" in response.json()["detail"]
