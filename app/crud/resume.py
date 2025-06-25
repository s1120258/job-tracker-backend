# app/crud/resume.py

from sqlalchemy.orm import Session
from uuid import UUID
from app.models.resume import Resume
from app.schemas.resume import ResumeCreate


def get_resume_by_user(db: Session, user_id: UUID):
    return db.query(Resume).filter(Resume.user_id == user_id).first()


def create_or_replace_resume(db: Session, user_id: UUID, resume_in: ResumeCreate):
    old_resume = get_resume_by_user(db, user_id)
    if old_resume:
        db.delete(old_resume)
        db.commit()
    db_resume = Resume(user_id=user_id, **resume_in.dict())
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
