import io
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from uuid import uuid4
from app.main import app
from app.models.user import User

client = TestClient(app)


@pytest.fixture
def fake_user():
    return User(id=uuid4(), email="test@example.com", hashed_password="hashed")


@pytest.fixture(autouse=True)
def override_get_current_user(fake_user):
    from app.api.routes_auth import get_current_user

    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield
    app.dependency_overrides.clear()


def test_upload_resume_pdf_unit(fake_user):
    pdf_bytes = io.BytesIO(b"%PDF-1.4 test pdf content")
    fake_resume = MagicMock(
        id=uuid4(),
        file_name="resume.pdf",
        upload_date="2024-06-15T12:00:00Z",
        extracted_text="Extracted PDF text",
        llm_feedback=None,
    )
    with patch("PyPDF2.PdfReader") as mock_pdf_reader, patch(
        "app.crud.resume.create_or_replace_resume", return_value=fake_resume
    ):
        mock_pdf_reader.return_value.pages = [
            MagicMock(extract_text=lambda: "Extracted PDF text")
        ]
        response = client.post(
            "/api/v1/resume/upload",
            files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["file_name"] == "resume.pdf"
    assert data["extracted_text"] == "Extracted PDF text"


def test_upload_resume_docx_unit(fake_user):
    docx_bytes = io.BytesIO(b"PK\x03\x04 test docx content")
    fake_resume = MagicMock(
        id=uuid4(),
        file_name="resume.docx",
        upload_date="2024-06-15T12:00:00Z",
        extracted_text="Extracted DOCX text",
        llm_feedback=None,
    )
    with patch("docx.Document") as mock_docx, patch(
        "app.crud.resume.create_or_replace_resume", return_value=fake_resume
    ):
        mock_docx.return_value.paragraphs = [MagicMock(text="Extracted DOCX text")]
        response = client.post(
            "/api/v1/resume/upload",
            files={
                "file": (
                    "resume.docx",
                    docx_bytes,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["file_name"] == "resume.docx"
    assert data["extracted_text"] == "Extracted DOCX text"


def test_upload_resume_unsupported_type(fake_user):
    txt_bytes = io.BytesIO(b"plain text")
    response = client.post(
        "/api/v1/resume/upload",
        files={"file": ("resume.txt", txt_bytes, "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported file type"


def test_get_resume_unit(fake_user):
    fake_resume = MagicMock(
        id=uuid4(),
        file_name="resume.pdf",
        upload_date="2024-06-15T12:00:00Z",
        extracted_text="Some extracted text",
        llm_feedback="Feedback",
    )
    with patch("app.crud.resume.get_resume_by_user", return_value=fake_resume):
        response = client.get("/api/v1/resume")
    assert response.status_code == 200
    data = response.json()
    assert data["file_name"] == "resume.pdf"
    assert data["extracted_text"] == "Some extracted text"
    assert data["llm_feedback"] == "Feedback"


def test_get_resume_not_found_unit(fake_user):
    with patch("app.crud.resume.get_resume_by_user", return_value=None):
        response = client.get("/api/v1/resume")
    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"


def test_delete_resume_unit(fake_user):
    with patch("app.crud.resume.delete_resume_by_user", return_value=True):
        response = client.delete("/api/v1/resume")
    assert response.status_code == 204


def test_delete_resume_not_found_unit(fake_user):
    with patch("app.crud.resume.delete_resume_by_user", return_value=False):
        response = client.delete("/api/v1/resume")
    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"
