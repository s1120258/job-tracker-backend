import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def mock_embedding_service():
    """Mock embedding service for all tests."""
    with patch("app.services.embedding_service.embedding_service"):
        yield


@pytest.fixture(autouse=True)
def mock_db_session():
    """Mock database session for all tests."""
    mock_session = MagicMock()
    with patch("app.db.session.SessionLocal", return_value=mock_session):
        with patch("app.db.session.get_db") as mock_get_db:
            mock_get_db.return_value = iter([mock_session])
            yield mock_session


@pytest.fixture(autouse=True)
def mock_similarity_service():
    """Mock similarity service for all tests."""
    with patch("app.services.similarity_service.similarity_service"):
        yield
