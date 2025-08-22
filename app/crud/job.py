# app/crud/job.py

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.job import Job, JobStatus
from app.models.match_score import MatchScore
from app.schemas.job import JobCreate, JobUpdate
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


def get_job(db: Session, job_id: UUID) -> Optional[Job]:
    """Get a single job by ID."""
    return db.query(Job).filter(Job.id == job_id).first()


def get_jobs(
    db: Session, user_id: UUID, status: Optional[JobStatus] = None
) -> List[Job]:
    """Get jobs for a user, optionally filtered by status."""
    query = db.query(Job).filter(Job.user_id == user_id)
    if status:
        query = query.filter(Job.status == status)
    return query.order_by(Job.created_at.desc()).all()


def get_jobs_by_status(db: Session, user_id: UUID, status: JobStatus) -> List[Job]:
    """Get jobs for a user filtered by specific status."""
    return (
        db.query(Job)
        .filter(and_(Job.user_id == user_id, Job.status == status))
        .order_by(Job.created_at.desc())
        .all()
    )


def create_job(db: Session, user_id: UUID, job_in: JobCreate) -> Job:
    """Create a new job (save from search results or manual entry)."""
    # Generate embedding if not provided
    if not job_in.job_embedding:
        try:
            job_embedding = embedding_service.generate_embedding(job_in.description)
            job_data = job_in.model_dump()
            job_data["job_embedding"] = job_embedding
        except Exception as e:
            logger.error(f"Failed to generate job embedding: {str(e)}")
            job_data = job_in.model_dump()
    else:
        job_data = job_in.model_dump()

    db_job = Job(**job_data, user_id=user_id)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def save_job(db: Session, user_id: UUID, job_in: JobCreate) -> Job:
    """Save a job with 'saved' status (convenience method)."""
    # Duplicate check: return existing job if user already saved this url
    existing = (
        db.query(Job).filter(Job.user_id == user_id, Job.url == job_in.url).first()
    )
    if existing:
        return existing

    job_data = job_in.model_dump()
    job_data["status"] = JobStatus.saved

    # Generate embedding if not provided
    if not job_data.get("job_embedding"):
        try:
            job_embedding = embedding_service.generate_embedding(job_in.description)
            job_data["job_embedding"] = job_embedding
        except Exception as e:
            logger.error(f"Failed to generate job embedding: {str(e)}")

    db_job = Job(**job_data, user_id=user_id)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def update_job(db: Session, job_id: UUID, job_in: JobUpdate) -> Optional[Job]:
    """Update an existing job."""
    db_job = get_job(db, job_id)
    if not db_job:
        return None

    update_data = job_in.model_dump(exclude_unset=True)

    # Regenerate embedding if description changed
    if "description" in update_data and not update_data.get("job_embedding"):
        try:
            job_embedding = embedding_service.generate_embedding(
                update_data["description"]
            )
            update_data["job_embedding"] = job_embedding
        except Exception as e:
            logger.error(f"Failed to generate job embedding: {str(e)}")

    for field, value in update_data.items():
        setattr(db_job, field, value)

    db.commit()
    db.refresh(db_job)
    return db_job


def update_job_status(db: Session, job_id: UUID, status: JobStatus) -> Optional[Job]:
    """Update job status (convenience method)."""
    db_job = get_job(db, job_id)
    if not db_job:
        return None

    db_job.status = status
    db.commit()
    db.refresh(db_job)
    return db_job


def update_job_match_score(
    db: Session, job_id: UUID, match_score: float
) -> Optional[Job]:
    """Update job match score and set status to 'matched'."""
    db_job = get_job(db, job_id)
    if not db_job:
        return None

    db_job.match_score = match_score
    db_job.status = JobStatus.matched
    db.commit()
    db.refresh(db_job)
    return db_job


def mark_job_applied(db: Session, job_id: UUID) -> Optional[Job]:
    """Mark a job as applied (convenience method)."""
    return update_job_status(db, job_id, JobStatus.applied)


def delete_job(db: Session, job_id: UUID) -> bool:
    """Delete a job."""
    db_job = get_job(db, job_id)
    if not db_job:
        return False
    db.delete(db_job)
    db.commit()
    return True


def search_jobs_by_keyword(db: Session, user_id: UUID, keyword: str) -> List[Job]:
    """Search saved jobs by keyword in title, description, or company."""
    keyword_filter = f"%{keyword.lower()}%"
    return (
        db.query(Job)
        .filter(
            and_(
                Job.user_id == user_id,
                Job.title.ilike(keyword_filter)
                | Job.description.ilike(keyword_filter)
                | Job.company.ilike(keyword_filter),
            )
        )
        .order_by(Job.created_at.desc())
        .all()
    )


def get_job_count_by_status(db: Session, user_id: UUID) -> dict:
    """Get count of jobs grouped by status."""
    from sqlalchemy import func

    status_counts = (
        db.query(Job.status, func.count(Job.id).label("count"))
        .filter(Job.user_id == user_id)
        .group_by(Job.status)
        .all()
    )

    # Initialize all statuses with 0
    result = {status.value: 0 for status in JobStatus}

    # Fill in actual counts
    for status_enum, count in status_counts:
        result[status_enum.value] = count

    return result


def get_match_score(db: Session, job_id: UUID) -> Optional[MatchScore]:
    """Get match score for a specific job."""
    return db.query(MatchScore).filter(MatchScore.job_id == job_id).first()
