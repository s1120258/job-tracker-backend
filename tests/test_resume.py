import io
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from uuid import uuid4
from app.main import app
from app.models.user import User
from app.schemas.resume import ResumeRead

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


def auth_headers():
    """Helper function to create auth headers for testing."""
    return {"Authorization": "Bearer test-token"}


def test_upload_resume_pdf_unit(fake_user):
    pdf_bytes = io.BytesIO(b"%PDF-1.4 test pdf content")
    fake_resume = ResumeRead(
        id=uuid4(),
        user_id=fake_user.id,
        file_name="resume.pdf",
        upload_date="2024-06-15T12:00:00Z",
        extracted_text="Extracted PDF text",
        embedding=[0.1, 0.2, 0.3] * 512,  # 1536 dimensions
    )

    with patch("PyPDF2.PdfReader") as mock_pdf_reader, patch(
        "app.crud.resume.create_or_replace_resume", return_value=fake_resume
    ):
        mock_pdf_reader.return_value.pages = [
            MagicMock(extract_text=lambda: "Extracted PDF text")
        ]
        response = client.post(
            "/api/v1/resume",
            files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["file_name"] == "resume.pdf"
    assert data["extracted_text"] == "Extracted PDF text"
    assert "embedding" in data


def test_upload_resume_docx_unit(fake_user):
    docx_bytes = io.BytesIO(b"PK\x03\x04 test docx content")
    fake_resume = ResumeRead(
        id=uuid4(),
        user_id=fake_user.id,
        file_name="resume.docx",
        upload_date="2024-06-15T12:00:00Z",
        extracted_text="Extracted DOCX text",
        embedding=[0.1, 0.2, 0.3] * 512,  # 1536 dimensions
    )

    with patch("docx.Document") as mock_docx, patch(
        "app.crud.resume.create_or_replace_resume", return_value=fake_resume
    ):
        mock_docx.return_value.paragraphs = [MagicMock(text="Extracted DOCX text")]
        response = client.post(
            "/api/v1/resume",
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
    assert "embedding" in data


def test_upload_resume_unsupported_type(fake_user):
    txt_bytes = io.BytesIO(b"plain text")
    response = client.post(
        "/api/v1/resume",
        files={"file": ("resume.txt", txt_bytes, "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported file type"


def test_get_resume_unit(fake_user):
    fake_resume = ResumeRead(
        id=uuid4(),
        user_id=fake_user.id,
        file_name="resume.pdf",
        upload_date="2024-06-15T12:00:00Z",
        extracted_text="Some extracted text",
        embedding=[0.1, 0.2, 0.3] * 512,  # 1536 dimensions
    )

    with patch("app.crud.resume.get_resume_by_user", return_value=fake_resume):
        response = client.get("/api/v1/resume")
    assert response.status_code == 200
    data = response.json()
    assert data["file_name"] == "resume.pdf"
    assert data["extracted_text"] == "Some extracted text"
    assert "embedding" in data
    assert "llm_feedback" not in data


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


def test_get_resume_feedback_general(fake_user):
    feedback = [
        "Add more details to your experience section.",
        "Include relevant programming languages.",
    ]
    fake_resume = ResumeRead(
        id=uuid4(),
        user_id=fake_user.id,
        file_name="resume.pdf",
        upload_date="2024-06-15T12:00:00Z",
        extracted_text="Some extracted text",
        embedding=[0.1, 0.2, 0.3] * 512,  # 1536 dimensions
    )
    with patch("app.crud.resume.get_resume_by_user", return_value=fake_resume), patch(
        "app.services.resume_feedback.get_general_feedback", return_value=feedback
    ):
        response = client.get("/api/v1/resume/feedback")
    assert response.status_code == 200
    data = response.json()
    assert "general_feedback" in data
    assert data["general_feedback"] == feedback


def test_get_resume_feedback_job_specific(fake_user):
    """Requesting feedback with a non-existent job_id should return 404 now that legacy support is removed."""
    fake_resume = ResumeRead(
        id=uuid4(),
        user_id=fake_user.id,
        file_name="resume.pdf",
        upload_date="2024-06-15T12:00:00Z",
        extracted_text="Some extracted text",
        embedding=[0.1, 0.2, 0.3] * 512,
    )

    with patch("app.crud.resume.get_resume_by_user", return_value=fake_resume), patch(
        "app.crud.job.get_job", return_value=None
    ):
        response = client.get(f"/api/v1/resume/feedback/{uuid4()}")

    assert response.status_code == 404


def test_get_resume_feedback_with_job_id(fake_user):
    """Test getting job-specific feedback using job_id from jobs table."""
    from app.models.job import Job, JobStatus
    import numpy as np

    feedback = [
        "Emphasize your Python and FastAPI experience",
        "Add more details about your remote work experience",
    ]
    job_excerpt = "Looking for experienced Python developer with FastAPI knowledge"

    fake_resume = ResumeRead(
        id=uuid4(),
        user_id=fake_user.id,
        file_name="resume.pdf",
        upload_date="2024-06-15T12:00:00Z",
        extracted_text="Python developer with 5 years experience",
        embedding=[0.1, 0.2, 0.3] * 512,
    )

    fake_job = Job(
        id=uuid4(),
        user_id=fake_user.id,
        title="Senior Python Developer",
        description="Looking for experienced Python developer with FastAPI knowledge and remote work experience",
        company="Tech Corp",
        location="Remote",
        url="https://example.com/job/456",
        source="LinkedIn",
        date_posted="2024-06-15",
        status=JobStatus.saved,
        job_embedding=np.array([0.2] * 1536),
    )

    with patch("app.crud.resume.get_resume_by_user", return_value=fake_resume), patch(
        "app.crud.job.get_job", return_value=fake_job
    ), patch(
        "app.services.resume_feedback.get_job_specific_feedback_with_description",
        return_value=(feedback, job_excerpt),
    ):

        response = client.get(
            f"/api/v1/resume/feedback/{fake_job.id}", headers=auth_headers()
        )

    assert response.status_code == 200
    data = response.json()
    assert "job_specific_feedback" in data
    assert data["job_specific_feedback"] == feedback
    assert data["job_description_excerpt"] == job_excerpt


def test_get_resume_feedback_job_not_found(fake_user):
    """Test feedback request for non-existent job."""
    fake_resume = ResumeRead(
        id=uuid4(),
        user_id=fake_user.id,
        file_name="resume.pdf",
        upload_date="2024-06-15T12:00:00Z",
        extracted_text="Some text",
        embedding=[0.1, 0.2, 0.3] * 512,
    )

    with patch("app.crud.resume.get_resume_by_user", return_value=fake_resume), patch(
        "app.crud.job.get_job", return_value=None
    ):

        response = client.get(
            f"/api/v1/resume/feedback/{uuid4()}", headers=auth_headers()
        )

    assert response.status_code == 404


def test_get_resume_feedback_job_unauthorized(fake_user):
    """Test that users can't get feedback for jobs they don't own."""
    from app.models.job import Job, JobStatus
    import numpy as np

    fake_resume = ResumeRead(
        id=uuid4(),
        user_id=fake_user.id,
        file_name="resume.pdf",
        upload_date="2024-06-15T12:00:00Z",
        extracted_text="Some text",
        embedding=[0.1, 0.2, 0.3] * 512,
    )

    # Job owned by different user
    other_job = Job(
        id=uuid4(),
        user_id=uuid4(),  # Different user
        title="Python Developer",
        description="Job description",
        company="Other Corp",
        location="Remote",
        url="https://example.com/job/789",
        source="Indeed",
        date_posted="2024-06-15",
        status=JobStatus.saved,
        job_embedding=np.array([0.3] * 1536),
    )

    with patch("app.crud.resume.get_resume_by_user", return_value=fake_resume), patch(
        "app.crud.job.get_job", return_value=other_job
    ):

        response = client.get(
            f"/api/v1/resume/feedback/{other_job.id}", headers=auth_headers()
        )

    assert response.status_code == 403
