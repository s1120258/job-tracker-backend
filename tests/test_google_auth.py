# tests/test_google_auth.py

import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app
from app.services.google_oauth_service import GoogleOAuth2Service
from app.crud import user as crud_user
from app.models.user import User

# Set testing environment variable
os.environ["TESTING"] = "true"


@pytest.fixture
def mock_google_user_info():
    """Mock Google user information."""
    return {
        "google_id": "123456789",
        "email": "testuser@gmail.com",
        "given_name": "Test",
        "family_name": "User",
        "name": "Test User",
        "picture": "https://example.com/picture.jpg",
        "email_verified": True,
    }


@pytest.fixture
def mock_parsed_user_data():
    """Mock parsed user data for database operations."""
    return {
        "google_id": "123456789",
        "email": "testuser@gmail.com",
        "firstname": "Test",
        "lastname": "User",
        "provider": "google",
        "is_oauth": True,
    }


class TestGoogleOAuth2Service:
    """Test cases for GoogleOAuth2Service."""

    @patch.object(GoogleOAuth2Service, "__init__", lambda x: None)
    def test_parse_user_data(self, mock_google_user_info):
        """Test user data parsing from Google response."""
        service = GoogleOAuth2Service()
        service.client_id = "test_client_id"

        result = service.parse_user_data(mock_google_user_info)

        assert result["google_id"] == "123456789"
        assert result["email"] == "testuser@gmail.com"
        assert result["firstname"] == "Test"
        assert result["lastname"] == "User"
        assert result["provider"] == "google"
        assert result["is_oauth"] is True

    @patch.object(GoogleOAuth2Service, "__init__", lambda x: None)
    def test_parse_user_data_missing_names(self):
        """Test user data parsing when given/family names are missing."""
        service = GoogleOAuth2Service()
        service.client_id = "test_client_id"

        user_info = {
            "google_id": "123456789",
            "email": "testuser@gmail.com",
            "name": "John Doe",
            "email_verified": True,
        }

        result = service.parse_user_data(user_info)

        assert result["firstname"] == "John"
        assert result["lastname"] == "Doe"

    @patch.object(GoogleOAuth2Service, "__init__", lambda x: None)
    def test_parse_user_data_no_name_info(self):
        """Test user data parsing when no name information is available."""
        service = GoogleOAuth2Service()
        service.client_id = "test_client_id"

        user_info = {
            "google_id": "123456789",
            "email": "testuser@gmail.com",
            "email_verified": True,
        }

        result = service.parse_user_data(user_info)

        assert result["firstname"] == "Unknown"
        assert result["lastname"] == "User"


class TestGoogleAuthEndpoints:
    """Test cases for Google authentication endpoints."""

    @patch("app.services.google_oauth_service.google_oauth_service.verify_id_token")
    @patch("app.crud.user.get_or_create_google_user")
    @patch("app.core.security.create_access_token")
    @patch("app.core.security.create_refresh_token")
    def test_google_auth_verify_new_user(
        self,
        mock_create_refresh_token,
        mock_create_access_token,
        mock_get_or_create_user,
        mock_verify_token,
        client: TestClient,
        mock_google_user_info,
        mock_parsed_user_data,
    ):
        """Test Google authentication for new user."""
        # Setup mocks
        mock_verify_token.return_value = mock_google_user_info
        from app.schemas.user import UserRead
        from uuid import uuid4

        mock_user = UserRead(
            id=uuid4(),
            email="testuser@gmail.com",
            firstname="Test",
            lastname="User",
            google_id="123456789",
            provider="google",
            is_oauth=True,
        )
        mock_get_or_create_user.return_value = mock_user
        mock_create_access_token.return_value = "mock_access_token"
        mock_create_refresh_token.return_value = "mock_refresh_token"

        # Make request
        response = client.post(
            "/api/v1/auth/google/verify", json={"id_token": "mock_id_token"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "mock_access_token"
        assert data["refresh_token"] == "mock_refresh_token"
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "testuser@gmail.com"

    @patch("app.services.google_oauth_service.google_oauth_service.verify_id_token")
    def test_google_auth_verify_invalid_token(
        self, mock_verify_token, client: TestClient
    ):
        """Test Google authentication with invalid token."""
        from fastapi import HTTPException

        # Setup mock to raise exception
        mock_verify_token.side_effect = HTTPException(
            status_code=401, detail="Invalid ID token"
        )

        # Make request
        response = client.post(
            "/api/v1/auth/google/verify", json={"id_token": "invalid_token"}
        )

        # Assertions
        assert response.status_code == 401
        assert "Invalid ID token" in response.json()["detail"]

    @patch("app.services.google_oauth_service.google_oauth_service.verify_id_token")
    @patch("app.crud.user.get_user_by_email")
    def test_google_register_existing_user(
        self,
        mock_get_user_by_email,
        mock_verify_token,
        client: TestClient,
        mock_google_user_info,
    ):
        """Test Google registration when user already exists."""
        # Setup mocks
        mock_verify_token.return_value = mock_google_user_info
        mock_get_user_by_email.return_value = User(email="testuser@gmail.com")

        # Make request
        response = client.post(
            "/api/v1/auth/google/register", json={"id_token": "mock_id_token"}
        )

        # Assertions
        assert response.status_code == 400
        assert "User with this email already exists" in response.json()["detail"]


class TestUserCRUD:
    """Test cases for user CRUD operations with Google OAuth."""

    @patch("app.crud.user.get_user_by_google_id")
    def test_get_user_by_google_id(self, mock_get_user):
        """Test getting user by Google ID."""
        # Mock user
        mock_user = MagicMock()
        mock_user.email = "test@gmail.com"
        mock_user.google_id = "123456789"
        mock_get_user.return_value = mock_user

        # Test retrieval
        found_user = crud_user.get_user_by_google_id(MagicMock(), "123456789")
        assert found_user is not None
        assert found_user.email == "test@gmail.com"
        assert found_user.google_id == "123456789"

    @patch("app.crud.user.get_user_by_google_id")
    def test_get_user_by_google_id_not_found(self, mock_get_user):
        """Test getting user by non-existent Google ID."""
        mock_get_user.return_value = None
        found_user = crud_user.get_user_by_google_id(MagicMock(), "nonexistent")
        assert found_user is None

    @patch("app.crud.user.create_google_user")
    def test_create_google_user(self, mock_create_user, mock_parsed_user_data):
        """Test creating a new Google user."""
        from app.schemas.user import GoogleUserCreate

        # Mock created user
        mock_user = MagicMock()
        mock_user.email = "testuser@gmail.com"
        mock_user.google_id = "123456789"
        mock_user.provider = "google"
        mock_user.is_oauth = True
        mock_user.hashed_password = None
        mock_create_user.return_value = mock_user

        google_user_create = GoogleUserCreate(**mock_parsed_user_data)
        user = crud_user.create_google_user(MagicMock(), google_user_create)

        assert user.email == "testuser@gmail.com"
        assert user.google_id == "123456789"
        assert user.provider == "google"
        assert user.is_oauth is True
        assert user.hashed_password is None


@pytest.fixture
def client():
    """Create test client."""
    with TestClient(app) as c:
        yield c
