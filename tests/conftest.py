import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_embedding_service():
    """Mock embedding service for all tests."""
    with patch("app.services.embedding_service.embedding_service"):
        yield
