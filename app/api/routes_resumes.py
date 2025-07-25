# app/api/routes_resumes.py

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.db.session import get_db
from app.schemas.resume import ResumeCreate, ResumeRead
from app.crud import resume as crud_resume
from app.crud import job as crud_job
from app.api.routes_auth import get_current_user
from app.models.user import User
from app.services.skill_extraction_service import (
    skill_extraction_service,
    SkillExtractionServiceError,
)
from app.schemas.skill_analysis import ResumeSkillsResponse
from app.schemas.job import ResumeSkillExtractionResponse
from datetime import datetime

router = APIRouter()


@router.post("/resume", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contents = await file.read()
    file_name = file.filename

    # Extract text
    extracted_text = None
    if file_name.lower().endswith(".pdf"):
        import io
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(contents))
        extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif file_name.lower().endswith(".docx"):
        import io
        from docx import Document

        doc = Document(io.BytesIO(contents))
        extracted_text = "\n".join([p.text for p in doc.paragraphs])
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    resume_in = ResumeCreate(file_name=file_name, extracted_text=extracted_text)
    db_resume = crud_resume.create_or_replace_resume(
        db, user_id=current_user.id, resume_in=resume_in
    )
    return db_resume


@router.get("/resume", response_model=ResumeRead)
def get_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = crud_resume.get_resume_by_user(db, user_id=current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.delete("/resume", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = crud_resume.delete_resume_by_user(db, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resume not found")
    return None


@router.get("/resume/feedback")
def get_resume_feedback_general(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = crud_resume.get_resume_by_user(db, user_id=current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    from app.services.resume_feedback import get_general_feedback

    feedback = get_general_feedback(resume.extracted_text)
    return {"general_feedback": feedback}


@router.get("/resume/feedback/{job_id}")
def get_resume_feedback_job_specific(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Fetch the caller's resume first
    resume = crud_resume.get_resume_by_user(db, user_id=current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Fetch job and ensure ownership
    job = crud_job.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Job does not belong to current user",
        )

    from app.services.resume_feedback import get_job_specific_feedback_with_description

    feedback, job_excerpt = get_job_specific_feedback_with_description(
        resume.extracted_text, job.description, job.title
    )

    return {
        "job_specific_feedback": feedback,
        "job_description_excerpt": job_excerpt,
    }


@router.get("/resume/skills", response_model=ResumeSkillExtractionResponse)
def extract_resume_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Extract skills from the current user's resume.

    This endpoint analyzes the user's uploaded resume to identify:
    - Technical skills with experience levels
    - Soft skills
    - Programming languages, frameworks, and tools
    - Certifications and education
    - Total years of experience
    """
    # Get user's current resume
    resume = crud_resume.get_resume_by_user(db, user_id=current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Validate resume has extracted text
    if not resume.extracted_text or not resume.extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Resume text not available. Please re-upload your resume.",
        )

    try:
        # Extract skills from resume text with normalization
        skills_data = skill_extraction_service.extract_skills_from_resume(
            resume_text=resume.extracted_text, normalize=True
        )

        # Create ResumeSkillsResponse from extracted data
        resume_skills_response = ResumeSkillsResponse(**skills_data)

        response = ResumeSkillExtractionResponse(
            resume_id=resume.id,
            skills_data=resume_skills_response,
            extraction_timestamp=datetime.utcnow(),
        )

        return response

    except SkillExtractionServiceError as e:
        raise HTTPException(
            status_code=500, detail=f"Skill extraction failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Internal server error during skill extraction"
        )
