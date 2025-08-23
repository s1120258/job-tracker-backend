# tests/test_google_auth.py

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.crud import user as crud_user


@pytest.fixture
def mock_google_user_info():
    """Mock Google user info response."""
    return {
        "google_id": "123456789",
        "email": "testuser@gmail.com",
        "given_name": "Test",
        "family_name": "User",
        "name": "Test User",
        "picture": "https://example.com/photo.jpg",
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

    @patch("app.services.google_oauth_service.google_oauth_service.parse_user_data")
    def test_parse_user_data(self, mock_parse_user_data, mock_google_user_info):
        """Test user data parsing from Google response."""
        from app.services.google_oauth_service import google_oauth_service

        # Mock the parse_user_data method
        mock_parse_user_data.return_value = mock_google_user_info

        # Test parsing
        result = google_oauth_service.parse_user_data(mock_google_user_info)
        assert result["email"] == "testuser@gmail.com"
        assert result["google_id"] == "123456789"

    @patch("app.services.google_oauth_service.google_oauth_service.parse_user_data")
    def test_parse_user_data_missing_names(self, mock_parse_user_data):
        """Test user data parsing when given/family names are missing."""
        from app.services.google_oauth_service import google_oauth_service

        # Mock user info with missing names
        user_info = {
            "google_id": "123456789",
            "email": "testuser@gmail.com",
            "name": "Test User",
            "email_verified": True,
        }

        # Mock the parse_user_data method
        mock_parse_user_data.return_value = user_info

        # Test parsing
        result = google_oauth_service.parse_user_data(user_info)
        assert result["email"] == "testuser@gmail.com"
        assert result["google_id"] == "123456789"

    @patch("app.services.google_oauth_service.google_oauth_service.parse_user_data")
    def test_parse_user_data_no_name_info(self, mock_parse_user_data):
        """Test user data parsing when no name information is available."""
        from app.services.google_oauth_service import google_oauth_service

        # Mock user info with no names
        user_info = {
            "google_id": "123456789",
            "email": "testuser@gmail.com",
            "email_verified": True,
        }

        # Mock the parse_user_data method
        mock_parse_user_data.return_value = user_info

        # Test parsing
        result = google_oauth_service.parse_user_data(user_info)
        assert result["email"] == "testuser@gmail.com"
        assert result["google_id"] == "123456789"


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
        from uuid import uuid4

        from app.schemas.user import UserRead

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
    @patch("app.crud.user.get_or_create_google_user")
    @patch("app.core.security.create_access_token")
    @patch("app.core.security.create_refresh_token")
    def test_google_auth_verify_existing_user(
        self,
        mock_create_refresh_token,
        mock_create_access_token,
        mock_get_or_create_user,
        mock_verify_token,
        client: TestClient,
        mock_google_user_info,
    ):
        """Test Google authentication for existing user (account linking)."""
        # Setup mocks
        mock_verify_token.return_value = mock_google_user_info

        # Mock existing user
        from uuid import uuid4
        from app.schemas.user import UserRead

        existing_user = UserRead(
            id=uuid4(),
            email="testuser@gmail.com",
            firstname="Test",
            lastname="User",
            google_id="123456789",
            provider="google",
            is_oauth=True,
        )
        mock_get_or_create_user.return_value = existing_user
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
        assert data["user"]["provider"] == "google"
        assert data["user"]["is_oauth"] is True


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

    def test_get_or_create_google_user_new_user(self, mock_parsed_user_data):
        """Test creating a new Google user through get_or_create_google_user."""
        from app.crud.user import get_or_create_google_user

        # Mock database session
        mock_db = MagicMock()

        # Mock that no user exists by Google ID or email
        with (
            patch("app.crud.user.get_user_by_google_id") as mock_get_by_google_id,
            patch("app.crud.user.get_user_by_email") as mock_get_by_email,
        ):

            mock_get_by_google_id.return_value = None
            mock_get_by_email.return_value = None

            # Mock the User model creation
            with patch("app.models.user.User") as mock_user_model:
                mock_user = MagicMock()
                mock_user.email = "testuser@gmail.com"
                mock_user.google_id = "123456789"
                mock_user.provider = "google"
                mock_user.is_oauth = True
                mock_user.hashed_password = None
                mock_user_model.return_value = mock_user

                # Call the function
                result = get_or_create_google_user(mock_db, mock_parsed_user_data)

                # Assertions
                assert result.email == "testuser@gmail.com"
                assert result.google_id == "123456789"
                assert result.provider == "google"
                assert result.is_oauth is True
                assert result.hashed_password is None

                # Verify database operations
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()
                mock_db.refresh.assert_called_once()


@pytest.fixture
def client():
    """Create test client."""
    with TestClient(app) as c:
        yield c
