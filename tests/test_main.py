# tests/test_main.py

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from Job Tracker API"}


def test_ping_db():
    response = client.get("/ping-db")
    assert response.status_code == 200
    data = response.json()
    assert "db_connected" in data
    if data["db_connected"]:
        assert data["db_connected"] == True
    else:
        assert "error" in data and isinstance(data["error"], str)


def test_api_versioning():
    """Test that API routes are properly versioned"""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
