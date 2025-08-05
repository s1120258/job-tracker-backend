# tests/test_user.py

import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, MagicMock
from app.main import app
from app.schemas.user import UserRead
from uuid import uuid4

client = TestClient(app)


@pytest.fixture
def user_create():
    return {
        "email": "test@example.com",
        "firstname": "Test",
        "lastname": "User",
        "password": "testpass",
    }


@pytest.fixture
def user_db():
    return UserRead(
        id=uuid4(), email="test@example.com", firstname="Test", lastname="User"
    )


@pytest.fixture
def user_db_with_password():
    # For login endpoint, needs hashed_password
    user = MagicMock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.firstname = "Test"
    user.lastname = "User"
    user.hashed_password = "hashed"
    return user


@pytest.fixture
def token_response():
    return {"access_token": "fake-jwt-token", "token_type": "bearer"}


def test_register_success(user_create, user_db):
    """Test successful registration."""
    with patch("app.crud.user.get_user_by_email", return_value=None), patch(
        "app.crud.user.create_user", return_value=user_db
    ):
        response = client.post("/api/v1/auth/register", json=user_create)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == user_create["email"]


def test_register_existing_email(user_create, user_db):
    """Test registration with an existing email."""
    with patch("app.crud.user.get_user_by_email", return_value=user_db):
        response = client.post("/api/v1/auth/register", json=user_create)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Email already registered"


@pytest.mark.parametrize(
    "email,password,db_user,verify,expected_status,expected_detail",
    [
        (
            "test@example.com",
            "wrongpass",
            MagicMock(hashed_password="hashed"),
            False,
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect email or password",
        ),
        (
            "nouser@example.com",
            "testpass",
            None,
            True,
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect email or password",
        ),
    ],
)
def test_login_failures(
    email, password, db_user, verify, expected_status, expected_detail
):
    """Test login failures for wrong password and wrong email."""
    with patch("app.crud.user.get_user_by_email", return_value=db_user), patch(
        "app.core.security.verify_password", return_value=verify
    ):
        response = client.post(
            "/api/v1/auth/token",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == expected_status
        assert response.json()["detail"] == expected_detail


def test_login_success(user_db_with_password, token_response):
    """Test successful login."""
    with patch(
        "app.crud.user.get_user_by_email", return_value=user_db_with_password
    ), patch("app.core.security.verify_password", return_value=True), patch(
        "app.core.security.create_access_token",
        return_value=token_response["access_token"],
    ):
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "test@example.com", "password": "testpass"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["access_token"] == token_response["access_token"]
        assert data["token_type"] == "bearer"


def test_me_success(user_db_with_password, token_response):
    """Test /me endpoint with valid token."""
    # Only patch user and password verification
    with patch(
        "app.crud.user.get_user_by_email", return_value=user_db_with_password
    ), patch("app.core.security.verify_password", return_value=True):
        login_resp = client.post(
            "/api/v1/auth/token",
            data={"username": "test@example.com", "password": "testpass"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_resp.json()["access_token"]
        # Patch again for /me
        with patch(
            "app.crud.user.get_user_by_email", return_value=user_db_with_password
        ):
            response = client.get(
                "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["firstname"] == "Test"
            assert data["lastname"] == "User"
            assert "id" in data


def test_me_invalid_token():
    """Test /me endpoint with invalid token."""
    with patch("app.crud.user.get_user_by_email", return_value=None):
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalidtoken"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.parametrize(
    "payload,missing_field",
    [
        ({"password": "testpass", "firstname": "Test", "lastname": "User"}, "email"),
        (
            {"email": "test@example.com", "firstname": "Test", "lastname": "User"},
            "password",
        ),
        (
            {"email": "test@example.com", "password": "testpass", "lastname": "User"},
            "firstname",
        ),
        (
            {"email": "test@example.com", "password": "testpass", "firstname": "Test"},
            "lastname",
        ),
    ],
)
def test_register_missing_fields(payload, missing_field):
    """Test registration with missing required fields."""
    with patch("app.crud.user.get_user_by_email", return_value=None), patch(
        "app.crud.user.create_user", return_value=None
    ):
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert missing_field in str(response.json())
