# tests/test_application.py

import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, MagicMock
from uuid import uuid4
from app.main import app
from app.schemas.application import ApplicationRead, ApplicationStatus
from app.models.user import User
from app.api.routes_auth import get_current_user

client = TestClient(app)


@pytest.fixture
def fake_user():
    return User(id=uuid4(), email="test@example.com", hashed_password="hashed")


@pytest.fixture
def fake_application(fake_user):
    return ApplicationRead(
        id=uuid4(),
        user_id=fake_user.id,
        company_name="Acme Corp",
        position_title="Engineer",
        job_description_text="Job desc",
        job_embedding=[0.1, 0.2, 0.3] * 512,  # 1536 dimensions
        application_status=ApplicationStatus.applied,
        applied_date="2024-06-15",
        interview_date=None,
        offer_date=None,
        notes="note",
        created_at="2024-06-15T12:00:00Z",
        updated_at="2024-06-15T12:00:00Z",
    )


@pytest.fixture(autouse=True)
def override_get_current_user(fake_user):
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield
    app.dependency_overrides.clear()


def auth_headers():
    return {"Authorization": "Bearer fake-jwt-token"}


def test_list_applications(fake_user, fake_application):
    with patch(
        "app.crud.application.get_applications", return_value=[fake_application]
    ):
        response = client.get("/api/v1/applications", headers=auth_headers())
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["company_name"] == fake_application.company_name
        assert "job_embedding" in data[0]


def test_create_application(fake_user, fake_application):
    with patch(
        "app.crud.application.create_application", return_value=fake_application
    ):
        payload = {
            "company_name": "Acme Corp",
            "position_title": "Engineer",
            "job_description_text": "Job desc",
            "application_status": "applied",
            "applied_date": "2024-06-15",
            "interview_date": None,
            "offer_date": None,
            "notes": "note",
        }
        response = client.post(
            "/api/v1/applications", json=payload, headers=auth_headers()
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["company_name"] == payload["company_name"]
        assert "job_embedding" in data


def test_get_application(fake_user, fake_application):
    with patch("app.crud.application.get_application", return_value=fake_application):
        response = client.get(
            f"/api/v1/applications/{fake_application.id}", headers=auth_headers()
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(fake_application.id)
        assert "job_embedding" in data


def test_get_application_not_found(fake_user):
    with patch("app.crud.application.get_application", return_value=None):
        response = client.get(f"/api/v1/applications/{uuid4()}", headers=auth_headers())
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_application(fake_user, fake_application):
    with patch(
        "app.crud.application.get_application", return_value=fake_application
    ), patch("app.crud.application.update_application", return_value=fake_application):
        payload = {
            "company_name": "Acme Corp",
            "position_title": "Engineer",
            "job_description_text": "Job desc",
            "application_status": "applied",
            "applied_date": "2024-06-15",
            "interview_date": None,
            "offer_date": None,
            "notes": "note",
        }
        response = client.put(
            f"/api/v1/applications/{fake_application.id}",
            json=payload,
            headers=auth_headers(),
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(fake_application.id)
        assert "job_embedding" in data


def test_delete_application(fake_user, fake_application):
    with patch(
        "app.crud.application.get_application", return_value=fake_application
    ), patch("app.crud.application.delete_application", return_value=True):
        response = client.delete(
            f"/api/v1/applications/{fake_application.id}", headers=auth_headers()
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_application_not_found(fake_user):
    with patch("app.crud.application.get_application", return_value=None):
        response = client.delete(
            f"/api/v1/applications/{uuid4()}", headers=auth_headers()
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
