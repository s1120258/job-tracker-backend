import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, MagicMock
from uuid import uuid4
import numpy as np
from app.main import app
from app.models.user import User
from app.models.application import Application, ApplicationStatus
from app.models.job import Job, JobStatus
from app.models.resume import Resume
from app.models.match_score import MatchScore
from app.api.routes_auth import get_current_user

client = TestClient(app)


@pytest.fixture
def fake_user():
    return User(id=uuid4(), email="test@example.com", hashed_password="hashed")


@pytest.fixture
def fake_application(fake_user):
    return Application(
        id=uuid4(),
        user_id=fake_user.id,
        company_name="Acme Corp",
        position_title="Software Engineer",
        job_description_text="Job description",
        job_embedding=np.array([0.1] * 1536),  # Add embedding
        application_status=ApplicationStatus.applied,
        applied_date="2024-06-15",
    )


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
def fake_match_score(fake_application, fake_resume):
    return MatchScore(
        id=uuid4(),
        application_id=fake_application.id,
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


class TestGetMatchScore:
    """Test cases for GET /applications/{id}/match-score endpoint."""

    def test_get_match_score_success(
        self, fake_user, fake_application, fake_match_score, fake_resume
    ):
        """Test successful retrieval of match score"""
        with patch(
            "app.api.routes_match_scores.get_application", return_value=fake_application
        ), patch(
            "app.api.routes_match_scores.get_match_score", return_value=fake_match_score
        ):

            response = client.get(
                f"/api/v1/applications/{fake_application.id}/match-score",
                headers=auth_headers(),
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["application_id"] == str(fake_application.id)
            assert data["resume_id"] == str(fake_resume.id)
            assert data["similarity_score"] == 0.85

    def test_get_match_score_not_found(self, fake_user, fake_application):
        """Test when match score does not exist"""
        with patch(
            "app.api.routes_match_scores.get_application", return_value=fake_application
        ), patch("app.api.routes_match_scores.get_match_score", return_value=None):

            response = client.get(
                f"/api/v1/applications/{fake_application.id}/match-score",
                headers=auth_headers(),
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "not found" in data["detail"].lower()

    def test_get_match_score_application_not_found(self, fake_user):
        """Test when application does not exist"""
        with patch("app.api.routes_match_scores.get_application", return_value=None):
            response = client.get(
                f"/api/v1/applications/{uuid4()}/match-score", headers=auth_headers()
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "not found" in data["detail"].lower()

    def test_get_match_score_wrong_user(self, fake_user, fake_application):
        """Test when application belongs to different user"""
        wrong_user_application = Application(
            id=fake_application.id,
            user_id=uuid4(),  # Different user
            company_name="Acme Corp",
            position_title="Software Engineer",
            job_description_text="Job description",
            job_embedding=np.array([0.1] * 1536),  # Add embedding
            application_status=ApplicationStatus.applied,
            applied_date="2024-06-15",
        )

        with patch(
            "app.api.routes_match_scores.get_application",
            return_value=wrong_user_application,
        ):
            response = client.get(
                f"/api/v1/applications/{fake_application.id}/match-score",
                headers=auth_headers(),
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "not found" in data["detail"].lower()


class TestRecomputeMatchScore:
    """Test cases for POST /applications/{id}/recompute-match endpoint."""

    def test_recompute_match_score_success(
        self, fake_user, fake_application, fake_resume
    ):
        """Test successful recomputation of match score"""
        with patch(
            "app.api.routes_match_scores.get_application", return_value=fake_application
        ), patch(
            "app.api.routes_match_scores.get_resume_by_user", return_value=fake_resume
        ), patch(
            "app.api.routes_match_scores.similarity_service.calculate_similarity_score",
            return_value=0.85,
        ), patch(
            "app.api.routes_match_scores.create_or_update_match_score"
        ) as mock_create:

            mock_match_score = MatchScore(
                id=uuid4(),
                application_id=fake_application.id,
                resume_id=fake_resume.id,
                similarity_score=0.85,
            )
            mock_create.return_value = mock_match_score

            response = client.post(
                f"/api/v1/applications/{fake_application.id}/recompute-match",
                headers=auth_headers(),
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["application_id"] == str(fake_application.id)
            assert data["resume_id"] == str(fake_resume.id)
            assert data["similarity_score"] == 0.85

    def test_recompute_match_score_application_not_found(self, fake_user):
        """Test when application does not exist"""
        with patch("app.api.routes_match_scores.get_application", return_value=None):
            response = client.post(
                f"/api/v1/applications/{uuid4()}/recompute-match",
                headers=auth_headers(),
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "not found" in data["detail"].lower()

    def test_recompute_match_score_wrong_user(self, fake_user, fake_application):
        """Test when application belongs to different user"""
        wrong_user_application = Application(
            id=fake_application.id,
            user_id=uuid4(),  # Different user
            company_name="Acme Corp",
            position_title="Software Engineer",
            job_description_text="Job description",
            job_embedding=np.array([0.1] * 1536),  # Add embedding
            application_status=ApplicationStatus.applied,
            applied_date="2024-06-15",
        )

        with patch(
            "app.api.routes_match_scores.get_application",
            return_value=wrong_user_application,
        ):
            response = client.post(
                f"/api/v1/applications/{fake_application.id}/recompute-match",
                headers=auth_headers(),
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "not found" in data["detail"].lower()

    def test_recompute_match_score_resume_not_found(self, fake_user, fake_application):
        """Test when user has no resume"""
        with patch(
            "app.api.routes_match_scores.get_application", return_value=fake_application
        ), patch("app.api.routes_match_scores.get_resume_by_user", return_value=None):

            response = client.post(
                f"/api/v1/applications/{fake_application.id}/recompute-match",
                headers=auth_headers(),
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "resume" in data["detail"].lower()

    def test_recompute_match_score_no_resume_embedding(
        self, fake_user, fake_application, fake_resume
    ):
        """Test when resume has no embedding"""
        resume_no_embedding = Resume(
            id=fake_resume.id,
            user_id=fake_user.id,
            file_name="resume.pdf",
            extracted_text="Some text",
            embedding=None,  # No embedding
            upload_date="2024-06-15T12:00:00Z",
        )

        with patch(
            "app.api.routes_match_scores.get_application", return_value=fake_application
        ), patch(
            "app.api.routes_match_scores.get_resume_by_user",
            return_value=resume_no_embedding,
        ):

            response = client.post(
                f"/api/v1/applications/{fake_application.id}/recompute-match",
                headers=auth_headers(),
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert "embedding" in data["detail"].lower()

    def test_recompute_match_score_no_job_embedding(
        self, fake_user, fake_application, fake_resume
    ):
        """Test when job has no embedding"""
        application_no_embedding = Application(
            id=fake_application.id,
            user_id=fake_user.id,
            company_name="Acme Corp",
            position_title="Software Engineer",
            job_description_text="Job description",
            job_embedding=None,  # No embedding
            application_status=ApplicationStatus.applied,
            applied_date="2024-06-15",
        )

        with patch(
            "app.api.routes_match_scores.get_application",
            return_value=application_no_embedding,
        ), patch(
            "app.api.routes_match_scores.get_resume_by_user", return_value=fake_resume
        ):

            response = client.post(
                f"/api/v1/applications/{fake_application.id}/recompute-match",
                headers=auth_headers(),
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert "embedding" in data["detail"].lower()


class TestAuthentication:
    """Test authentication requirements."""

    def test_get_match_score_no_auth(self, fake_application):
        """Test that match score endpoint requires authentication"""
        # Clear dependency overrides for this test
        from app.main import app

        app.dependency_overrides.clear()

        response = client.get(f"/api/v1/applications/{fake_application.id}/match-score")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_recompute_match_score_no_auth(self, fake_application):
        """Test that recompute endpoint requires authentication"""
        # Clear dependency overrides for this test
        from app.main import app

        app.dependency_overrides.clear()

        response = client.post(
            f"/api/v1/applications/{fake_application.id}/recompute-match"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestResponseFormat:
    """Test response format matches API specification."""

    def test_match_score_response_format(
        self, fake_user, fake_application, fake_match_score
    ):
        """Test that match score response format matches API specification"""
        with patch(
            "app.api.routes_match_scores.get_application", return_value=fake_application
        ), patch(
            "app.api.routes_match_scores.get_match_score", return_value=fake_match_score
        ):

            response = client.get(
                f"/api/v1/applications/{fake_application.id}/match-score",
                headers=auth_headers(),
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check required fields from API spec
            assert "application_id" in data
            assert "resume_id" in data
            assert "similarity_score" in data

            # Check data types
            assert isinstance(data["application_id"], str)
            assert isinstance(data["resume_id"], str)
            assert isinstance(data["similarity_score"], (int, float))

            # Check value ranges
            assert 0.0 <= data["similarity_score"] <= 1.0

    def test_recompute_match_score_response_format(
        self, fake_user, fake_application, fake_resume, fake_match_score
    ):
        """Test that recompute response format matches API specification"""
        with patch(
            "app.api.routes_match_scores.get_application", return_value=fake_application
        ), patch(
            "app.api.routes_match_scores.get_resume_by_user", return_value=fake_resume
        ), patch(
            "app.api.routes_match_scores.similarity_service.calculate_similarity_score",
            return_value=0.82,
        ), patch(
            "app.api.routes_match_scores.create_or_update_match_score",
            return_value=fake_match_score,
        ):

            response = client.post(
                f"/api/v1/applications/{fake_application.id}/recompute-match",
                headers=auth_headers(),
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check required fields from API spec
            assert "application_id" in data
            assert "resume_id" in data
            assert "similarity_score" in data

            # Check data types
            assert isinstance(data["application_id"], str)
            assert isinstance(data["resume_id"], str)
            assert isinstance(data["similarity_score"], (int, float))

            # Check value ranges
            assert 0.0 <= data["similarity_score"] <= 1.0


# ============================================================================
# NEW JOB-BASED MATCH SCORE TESTS
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
        user_id=fake_job.user_id,
        job_id=fake_job.id,
        resume_id=fake_resume.id,
        similarity_score=0.82,
    )


class TestJobMatchScores:
    """Test cases for new job-based match score endpoints."""

    def test_get_job_match_score_success(self, fake_user, fake_job, fake_job_match_score):
        """Test successful retrieval of job match score"""
        with patch("app.crud.job.get_job", return_value=fake_job), \
             patch("app.crud.match_score.get_match_score", return_value=fake_job_match_score):

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
        with patch("app.crud.job.get_job", return_value=fake_job), \
             patch("app.crud.match_score.get_match_score", return_value=None):

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
            assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeprecatedApplicationEndpoints:
    """Test that deprecated application-based endpoints return appropriate responses."""

    def test_deprecated_application_match_score(self, fake_user, fake_application):
        """Test that deprecated application match-score endpoint returns 410 Gone"""
        response = client.get(
            f"/api/v1/applications/{fake_application.id}/match-score",
            headers=auth_headers(),
        )
        assert response.status_code == status.HTTP_410_GONE
        data = response.json()
        assert "deprecated" in data["detail"].lower()
        assert "jobs" in data["detail"].lower()

    def test_deprecated_application_recompute_match(self, fake_user, fake_application):
        """Test that deprecated application recompute-match endpoint returns 410 Gone"""
        response = client.post(
            f"/api/v1/applications/{fake_application.id}/recompute-match",
            headers=auth_headers(),
        )
        assert response.status_code == status.HTTP_410_GONE
        data = response.json()
        assert "deprecated" in data["detail"].lower()
        assert "jobs" in data["detail"].lower()
