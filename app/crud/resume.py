# app/crud/resume.py

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.schemas.resume import ResumeCreate
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


def get_resume_by_user(db: Session, user_id: UUID):
    return db.query(Resume).filter(Resume.user_id == user_id).first()


def create_or_replace_resume(db: Session, user_id: UUID, resume_in: ResumeCreate):
    # Check if user already has a resume
    old_resume = get_resume_by_user(db, user_id)
    if old_resume:
        db.delete(old_resume)
        db.commit()

    # Generate embedding if not provided
    if not resume_in.embedding and resume_in.extracted_text:
        try:
            embedding = embedding_service.generate_embedding(resume_in.extracted_text)
            resume_data = resume_in.model_dump()
            resume_data["embedding"] = embedding
        except Exception as e:
            logger.error(f"Failed to generate resume embedding: {str(e)}")
            resume_data = resume_in.model_dump()
    else:
        resume_data = resume_in.model_dump()

    db_resume = Resume(user_id=user_id, **resume_data)
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    return db_resume


def delete_resume_by_user(db: Session, user_id: UUID):
    resume = get_resume_by_user(db, user_id)
    if not resume:
        return False
    db.delete(resume)
    db.commit()
    return True
