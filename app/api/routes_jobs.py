# app/api/routes_jobs.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.db.session import get_db
from app.schemas.job import (
    JobCreate,
    JobUpdate,
    JobRead,
    JobSearch,
    JobSearchResult,
    JobMatchRequest,
    JobMatchResponse,
    JobApplyRequest,
    JobApplyResponse,
    JobStatus
)
from app.crud import job as crud_job
from app.crud.resume import get_resume_by_user
from app.crud.match_score import create_or_update_match_score
from app.api.routes_auth import get_current_user
from app.models.user import User
from app.services.similarity_service import similarity_service, SimilarityServiceError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/jobs/search")
def search_jobs(
    keyword: Optional[str] = Query(None, description="Search keyword"),
    location: Optional[str] = Query(None, description="Job location"),
    source: Optional[str] = Query(None, description="Job board source"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search jobs from external job boards (placeholder for crawler integration).
    For now, this returns saved jobs matching the criteria.
    """
    # TODO: Integrate with actual job crawler (RemoteOK, Indeed, etc.)
    # For now, search within saved jobs
    if keyword:
        jobs = crud_job.search_jobs_by_keyword(db, current_user.id, keyword)
    else:
        jobs = crud_job.get_jobs(db, current_user.id)

    # Convert to search result format
    search_results = []
    for job in jobs:
        if (not location or (job.location and location.lower() in job.location.lower())) and \
           (not source or (job.source and source.lower() in job.source.lower())):
            search_results.append({
                "title": job.title,
                "description": job.description,
                "company": job.company,
                "location": job.location,
                "url": job.url,
                "source": job.source or "Manual",
                "date_posted": job.date_posted
            })

    return {"jobs": search_results}


@router.post("/jobs/save", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def save_job(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save a job with 'saved' status."""
    return crud_job.save_job(db, user_id=current_user.id, job_in=job_in)


@router.get("/jobs", response_model=List[JobRead])
def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List saved/matched/applied jobs, optionally filtered by status."""
    return crud_job.get_jobs(db, user_id=current_user.id, status=status)


@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details of a specific job."""
    job = crud_job.get_job(db, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/jobs/{job_id}", response_model=JobRead)
def update_job(
    job_id: UUID,
    job_in: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update job status or other information."""
    job = crud_job.get_job(db, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")

    updated_job = crud_job.update_job(db, job_id, job_in)
    if not updated_job:
        raise HTTPException(status_code=404, detail="Job not found")
    return updated_job


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a saved job."""
    job = crud_job.get_job(db, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")

    success = crud_job.delete_job(db, job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return None


@router.post("/jobs/{job_id}/match", response_model=JobMatchResponse)
def calculate_match_score(
    job_id: UUID,
    match_request: JobMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate match score between job and resume."""
    # Verify the job belongs to the user
    job = crud_job.get_job(db, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get user's resume
    resume = get_resume_by_user(db, current_user.id)
    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found. Please upload a resume first.",
        )

    # Check if embeddings exist
    if resume.embedding is None or (
        hasattr(resume.embedding, "size") and resume.embedding.size == 0
    ):
        raise HTTPException(
            status_code=400,
            detail="Resume embedding not available. Please re-upload your resume.",
        )

    if job.job_embedding is None or (
        hasattr(job.job_embedding, "size")
        and job.job_embedding.size == 0
    ):
        raise HTTPException(
            status_code=400, detail="Job description embedding not available."
        )

    try:
        # Calculate similarity score
        similarity_score = similarity_service.calculate_similarity_score(
            resume.embedding, job.job_embedding
        )

        # Update job with match score and status
        updated_job = crud_job.update_job_match_score(db, job_id, similarity_score)

        # Store the match score in match_scores table
        match_score = create_or_update_match_score(
            db, job_id, resume.id, similarity_score
        )

        return JobMatchResponse(
            job_id=job_id,
            resume_id=resume.id,
            similarity_score=similarity_score,
            status=JobStatus.matched
        )

    except SimilarityServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in calculate_match_score: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while computing match score",
        )


@router.post("/jobs/{job_id}/apply", response_model=JobApplyResponse)
def apply_to_job(
    job_id: UUID,
    apply_request: JobApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark job as applied."""
    # Verify the job belongs to the user
    job = crud_job.get_job(db, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")

    # Verify resume exists
    resume = get_resume_by_user(db, current_user.id)
    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found. Please upload a resume first.",
        )

    # Mark job as applied
    updated_job = crud_job.mark_job_applied(db, job_id)
    if not updated_job:
        raise HTTPException(status_code=404, detail="Job not found")

    # TODO: Integrate with actual application system
    # - Generate cover letter using apply_request.cover_letter_template
    # - Submit application via API or email
    # - Store application details

    return JobApplyResponse(
        job_id=job_id,
        resume_id=resume.id,
        status=JobStatus.applied,
        applied_at=datetime.utcnow()
    )