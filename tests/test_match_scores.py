import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, MagicMock
from uuid import uuid4
import numpy as np
from app.main import app
from app.models.user import User

from app.models.job import Job, JobStatus
from app.models.resume import Resume
from app.models.match_score import MatchScore
from app.api.routes_auth import get_current_user

client = TestClient(app)


@pytest.fixture
def fake_user():
    return User(id=uuid4(), email="test@example.com", hashed_password="hashed")


@pytest.fixture
def fake_resume(fake_user):
    return Resume(
        id=uuid4(),
        user_id=fake_user.id,
        file_name="resume.pdf",
        extracted_text="Some text",
        embedding=np.array([0.2] * 1536),  # Add embedding
        upload_date="2024-06-15T12:00:00Z",
    )


@pytest.fixture
def fake_match_score(fake_job, fake_resume):
    return MatchScore(
        id=uuid4(),
        job_id=fake_job.id,
        resume_id=fake_resume.id,
        similarity_score=0.85,
    )


@pytest.fixture(autouse=True)
def override_get_current_user(fake_user):
    """Override get_current_user dependency for most tests."""
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield
    # Don't clear here, let the clear_dependency_overrides fixture handle it


def auth_headers():
    """Helper function to create auth headers for testing."""
    return {"Authorization": "Bearer test-token"}


# ============================================================================
# JOB-BASED MATCH SCORE TESTS
# ============================================================================


@pytest.fixture
def fake_job(fake_user):
    """Create a fake job for testing."""
    return Job(
        id=uuid4(),
        user_id=fake_user.id,
        title="Backend Python Engineer",
        description="Looking for Python developer with FastAPI experience",
        company="Tech Startup",
        location="Remote",
        url="https://example.com/job/123",
        source="RemoteOK",
        date_posted="2024-06-15",
        status=JobStatus.saved,
        job_embedding=np.array([0.1] * 1536),
    )


@pytest.fixture
def fake_job_match_score(fake_job, fake_resume):
    """Create a fake match score for job-based testing."""
    return MatchScore(
        id=uuid4(),
        job_id=fake_job.id,
        resume_id=fake_resume.id,
        similarity_score=0.82,
    )


class TestJobMatchScores:
    """Test cases for new job-based match score endpoints."""

    def test_get_job_match_score_success(
        self, fake_user, fake_job, fake_job_match_score
    ):
        """Test successful retrieval of job match score"""
        with patch("app.crud.job.get_job", return_value=fake_job), patch(
            "app.api.routes_match_scores.get_match_score",
            return_value=fake_job_match_score,
        ):

            response = client.get(
                f"/api/v1/jobs/{fake_job.id}/match-score",
                headers=auth_headers(),
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check required fields
            assert "job_id" in data
            assert "resume_id" in data
            assert "similarity_score" in data

            # Check data types and values
            assert isinstance(data["job_id"], str)
            assert isinstance(data["resume_id"], str)
            assert isinstance(data["similarity_score"], (int, float))
            assert 0.0 <= data["similarity_score"] <= 1.0

    def test_get_job_match_score_not_found(self, fake_user):
        """Test retrieving match score for non-existent job"""
        with patch("app.crud.job.get_job", return_value=None):
            response = client.get(
                f"/api/v1/jobs/{uuid4()}/match-score",
                headers=auth_headers(),
            )
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_job_match_score_no_match(self, fake_user, fake_job):
        """Test retrieving match score when none exists"""
        # Set job.match_score to None to trigger 404
        fake_job.match_score = None

        with patch("app.crud.job.get_job", return_value=fake_job), patch(
            "app.api.routes_match_scores.get_match_score", return_value=None
        ):

            response = client.get(
                f"/api/v1/jobs/{fake_job.id}/match-score",
                headers=auth_headers(),
            )
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_job_match_score_unauthorized(self, fake_user, fake_job):
        """Test that users can't access match scores for jobs they don't own"""
        # Create job owned by different user
        other_job = fake_job
        other_job.user_id = uuid4()

        with patch("app.crud.job.get_job", return_value=other_job):
            response = client.get(
                f"/api/v1/jobs/{other_job.id}/match-score",
                headers=auth_headers(),
            )
            assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeprecatedApplicationEndpoints:
    """Test that deprecated application-based endpoints return appropriate responses."""

    def test_deprecated_application_match_score(self, fake_user):
        """Test that deprecated application match-score endpoint returns 410 Gone"""
        response = client.get(
            f"/api/v1/applications/{uuid4()}/match-score",
            headers=auth_headers(),
        )
        assert response.status_code == status.HTTP_410_GONE
        data = response.json()
        assert "deprecated" in data["detail"].lower()
        assert "jobs" in data["detail"].lower()

    def test_deprecated_application_recompute_match(self, fake_user):
        """Test that deprecated application recompute-match endpoint returns 410 Gone"""
        response = client.post(
            f"/api/v1/applications/{uuid4()}/recompute-match",
            headers=auth_headers(),
        )
        assert response.status_code == status.HTTP_410_GONE
        data = response.json()
        assert "deprecated" in data["detail"].lower()
        assert "jobs" in data["detail"].lower()
