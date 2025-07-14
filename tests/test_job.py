# tests/test_job.py

import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime
from app.main import app
from app.schemas.job import JobRead, JobStatus
from app.models.user import User
from app.api.routes_auth import get_current_user

client = TestClient(app)


@pytest.fixture
def fake_user():
    return User(id=uuid4(), email="test@example.com", hashed_password="hashed")


@pytest.fixture
def fake_job(fake_user):
    return JobRead(
        id=uuid4(),
        user_id=fake_user.id,
        title="Backend Python Engineer",
        description="We are looking for an experienced Python developer...",
        company="Tech Startup",
        location="Remote",
        url="https://example.com/jobs/123",
        source="RemoteOK",
        date_posted=datetime(2024, 6, 15).date(),
        status=JobStatus.saved,
        match_score=0.85,
        job_embedding=[0.1, 0.2, 0.3] * 512,  # 1536 dimensions
        created_at=datetime(2024, 6, 15, 12, 0, 0),
        updated_at=datetime(2024, 6, 15, 12, 0, 0),
    )


@pytest.fixture(autouse=True)
def override_get_current_user(fake_user):
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield
    app.dependency_overrides.clear()


def auth_headers():
    return {"Authorization": "Bearer fake-jwt-token"}


# Test job search endpoint
def test_search_jobs(fake_user):
    """Test job search functionality (placeholder for external job board integration)."""
    with patch("app.crud.job.search_jobs_by_keyword") as mock_search:
        mock_search.return_value = []
        response = client.get(
            "/api/v1/jobs/search?keyword=python&location=remote",
            headers=auth_headers()
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)


# Test save job endpoint
def test_save_job(fake_user, fake_job):
    """Test saving a job from search results."""
    with patch("app.crud.job.create_job", return_value=fake_job):
        payload = {
            "title": "Backend Python Engineer",
            "description": "We are looking for an experienced Python developer...",
            "company": "Tech Startup",
            "location": "Remote",
            "url": "https://example.com/jobs/123",
            "source": "RemoteOK",
            "date_posted": "2024-06-15"
        }
        response = client.post(
            "/api/v1/jobs/save",
            json=payload,
            headers=auth_headers()
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["status"] == "saved"
        assert "job_embedding" in data


# Test list jobs endpoint
def test_list_jobs(fake_user, fake_job):
    """Test listing saved jobs with optional status filtering."""
    with patch("app.crud.job.get_jobs", return_value=[fake_job]):
        response = client.get("/api/v1/jobs", headers=auth_headers())
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["title"] == fake_job.title
        assert "job_embedding" in data[0]


def test_list_jobs_with_status_filter(fake_user, fake_job):
    """Test listing jobs filtered by status."""
    with patch("app.crud.job.get_jobs", return_value=[fake_job]):
        response = client.get(
            "/api/v1/jobs?status=saved",
            headers=auth_headers()
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


# Test get specific job endpoint
def test_get_job(fake_user, fake_job):
    """Test retrieving a specific job by ID."""
    with patch("app.crud.job.get_job", return_value=fake_job):
        response = client.get(
            f"/api/v1/jobs/{fake_job.id}",
            headers=auth_headers()
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(fake_job.id)
        assert data["title"] == fake_job.title
        assert "job_embedding" in data


def test_get_job_not_found(fake_user):
    """Test retrieving a non-existent job."""
    with patch("app.crud.job.get_job", return_value=None):
        response = client.get(
            f"/api/v1/jobs/{uuid4()}",
            headers=auth_headers()
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_job_unauthorized(fake_user, fake_job):
    """Test that users can't access jobs they don't own."""
    # Create a job owned by different user
    other_job = fake_job.model_copy()
    other_job.user_id = uuid4()

    with patch("app.crud.job.get_job", return_value=other_job):
        response = client.get(
            f"/api/v1/jobs/{other_job.id}",
            headers=auth_headers()
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


# Test update job endpoint
def test_update_job(fake_user, fake_job):
    """Test updating a job's details."""
    updated_job = fake_job.model_copy()
    updated_job.status = JobStatus.matched

    with patch("app.crud.job.get_job", return_value=fake_job), \
         patch("app.crud.job.update_job", return_value=updated_job):
        payload = {
            "status": "matched",
            "notes": "Updated notes"
        }
        response = client.put(
            f"/api/v1/jobs/{fake_job.id}",
            json=payload,
            headers=auth_headers()
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(fake_job.id)


def test_update_job_not_found(fake_user):
    """Test updating a non-existent job."""
    with patch("app.crud.job.get_job", return_value=None):
        response = client.put(
            f"/api/v1/jobs/{uuid4()}",
            json={"status": "matched"},
            headers=auth_headers()
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# Test delete job endpoint
def test_delete_job(fake_user, fake_job):
    """Test deleting a job."""
    with patch("app.crud.job.get_job", return_value=fake_job), \
         patch("app.crud.job.delete_job", return_value=True):
        response = client.delete(
            f"/api/v1/jobs/{fake_job.id}",
            headers=auth_headers()
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_job_not_found(fake_user):
    """Test deleting a non-existent job."""
    with patch("app.crud.job.get_job", return_value=None):
        response = client.delete(
            f"/api/v1/jobs/{uuid4()}",
            headers=auth_headers()
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# Test job matching endpoint
def test_match_job_to_resume(fake_user, fake_job):
    """Test calculating match score between job and user's resume."""
    from app.models.resume import Resume
    from app.models.match_score import MatchScore

    fake_resume = Resume(
        id=uuid4(),
        user_id=fake_user.id,
        file_name="resume.pdf",
        extracted_text="Python developer experience",
        embedding=[0.2, 0.3, 0.4] * 512,
        upload_date=datetime(2024, 6, 15, 12, 0, 0)
    )

    fake_match_score = MatchScore(
        id=uuid4(),
        user_id=fake_user.id,
        job_id=fake_job.id,
        resume_id=fake_resume.id,
        similarity_score=0.82,
        created_at=datetime(2024, 6, 15, 12, 0, 0)
    )

    with patch("app.crud.job.get_job", return_value=fake_job), \
         patch("app.crud.resume.get_resume_by_user", return_value=fake_resume), \
         patch("app.services.similarity_service.calculate_similarity", return_value=0.82), \
         patch("app.crud.job.update_job_match_score", return_value=fake_job), \
         patch("app.crud.match_score.create_or_update_match_score", return_value=fake_match_score):

        response = client.post(
            f"/api/v1/jobs/{fake_job.id}/match",
            headers=auth_headers()
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == str(fake_job.id)
        assert data["resume_id"] == str(fake_resume.id)
        assert data["similarity_score"] == 0.82
        assert data["status"] == "matched"


def test_match_job_no_resume(fake_user, fake_job):
    """Test matching when user has no resume uploaded."""
    with patch("app.crud.job.get_job", return_value=fake_job), \
         patch("app.crud.resume.get_resume_by_user", return_value=None):

        response = client.post(
            f"/api/v1/jobs/{fake_job.id}/match",
            headers=auth_headers()
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "resume" in data["detail"].lower()


# Test job application endpoint
def test_apply_to_job(fake_user, fake_job):
    """Test marking a job as applied."""
    applied_job = fake_job.model_copy()
    applied_job.status = JobStatus.applied

    with patch("app.crud.job.get_job", return_value=fake_job), \
         patch("app.crud.job.mark_job_applied", return_value=applied_job):

        payload = {
            "resume_id": str(uuid4()),
            "cover_letter_template": "default"
        }
        response = client.post(
            f"/api/v1/jobs/{fake_job.id}/apply",
            json=payload,
            headers=auth_headers()
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == str(fake_job.id)
        assert data["status"] == "applied"
        assert "applied_at" in data


def test_apply_to_job_not_found(fake_user):
    """Test applying to a non-existent job."""
    with patch("app.crud.job.get_job", return_value=None):
        payload = {
            "resume_id": str(uuid4()),
            "cover_letter_template": "default"
        }
        response = client.post(
            f"/api/v1/jobs/{uuid4()}/apply",
            json=payload,
            headers=auth_headers()
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# Test invalid job status
def test_invalid_job_status():
    """Test that invalid job status values are rejected."""
    response = client.get(
        "/api/v1/jobs?status=invalid_status",
        headers=auth_headers()
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Test authentication required
def test_jobs_require_authentication():
    """Test that all job endpoints require authentication."""
    endpoints = [
        ("GET", "/api/v1/jobs/search"),
        ("POST", "/api/v1/jobs/save"),
        ("GET", "/api/v1/jobs"),
        ("GET", f"/api/v1/jobs/{uuid4()}"),
        ("PUT", f"/api/v1/jobs/{uuid4()}"),
        ("DELETE", f"/api/v1/jobs/{uuid4()}"),
        ("POST", f"/api/v1/jobs/{uuid4()}/match"),
        ("POST", f"/api/v1/jobs/{uuid4()}/apply"),
    ]

    for method, endpoint in endpoints:
        response = client.request(method, endpoint)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED