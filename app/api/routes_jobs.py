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
    JobStatus,
)
from app.crud import job as crud_job
from app.crud.resume import get_resume_by_user
from app.crud.match_score import create_or_update_match_score
from app.api.routes_auth import get_current_user
from app.models.user import User
from app.services.similarity_service import similarity_service, SimilarityServiceError
from app.services.job_scraper_service import job_scraper_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/jobs/search")
def search_jobs(
    keyword: Optional[str] = Query(None, description="Search keyword"),
    location: Optional[str] = Query(None, description="Job location"),
    source: Optional[str] = Query(
        None, description="Job board source (e.g., 'remoteok')"
    ),
    search_external: bool = Query(
        True, description="Whether to search external job boards"
    ),
    search_saved: bool = Query(False, description="Whether to search saved jobs"),
    limit: int = Query(
        20, description="Maximum number of jobs to return", ge=1, le=100
    ),
    fetch_full_description: bool = Query(
        True, description="Whether to fetch full job descriptions (external only)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search jobs from external job boards and/or saved jobs.

    By default, searches external job boards. Use search_saved=True to also include saved jobs.
    """
    all_jobs = []

    # Search external job boards if requested
    if search_external and keyword:
        try:
            logger.info("Searching external job boards for keyword: %s", keyword)
            external_jobs = job_scraper_service.search_jobs(
                keyword=keyword,
                location=location or "",
                source=source,
                limit=limit,
                fetch_full_description=fetch_full_description,
            )

            # Convert external jobs to the expected format
            for job in external_jobs:
                search_result = {
                    "title": job.get("title", ""),
                    "description": job.get("description", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", ""),
                    "url": job.get("url", ""),
                    "source": job.get("source", "External"),
                    "date_posted": job.get("posted_at"),
                    "salary": job.get("salary"),
                    "board_type": job.get("board_type", "unknown"),
                }
                all_jobs.append(search_result)

            logger.info("Found %d external jobs", len(external_jobs))

        except Exception as e:
            logger.error("Error searching external job boards: %s", e)
            # Continue to search saved jobs if external search fails

    # Search saved jobs if requested
    if search_saved:
        try:
            if keyword:
                saved_jobs = crud_job.search_jobs_by_keyword(
                    db, current_user.id, keyword
                )
            else:
                saved_jobs = crud_job.get_jobs(db, current_user.id)

            # Convert saved jobs to search result format
            for job in saved_jobs:
                # Apply location and source filters
                if (
                    not location
                    or (job.location and location.lower() in job.location.lower())
                ) and (
                    not source or (job.source and source.lower() in job.source.lower())
                ):
                    search_result = {
                        "title": job.title,
                        "description": job.description,
                        "company": job.company,
                        "location": job.location,
                        "url": job.url,
                        "source": job.source or "Saved",
                        "date_posted": job.date_posted,
                        "salary": getattr(job, "salary", None),
                        "board_type": "saved",
                        "job_id": str(job.id),  # Include job ID for saved jobs
                    }
                    all_jobs.append(search_result)

            logger.info("Found %d saved jobs", len([job for job in saved_jobs]))

        except Exception as e:
            logger.error("Error searching saved jobs: %s", e)

    # If no search type is enabled, return error
    if not search_external and not search_saved:
        raise HTTPException(
            status_code=400,
            detail="At least one of search_external or search_saved must be True",
        )

    # Apply overall limit if needed
    if len(all_jobs) > limit:
        all_jobs = all_jobs[:limit]

    return {
        "jobs": all_jobs,
        "total_found": len(all_jobs),
        "search_params": {
            "keyword": keyword,
            "location": location,
            "source": source,
            "search_external": search_external,
            "search_saved": search_saved,
            "limit": limit,
        },
        "available_sources": (
            job_scraper_service.get_available_sources() if search_external else []
        ),
    }


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
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Job does not belong to current user",
        )
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
            status_code=400,
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
        hasattr(job.job_embedding, "size") and job.job_embedding.size == 0
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
            status=JobStatus.matched,
        )

    except SimilarityServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unexpected error in calculate_match_score: {str(e)}", exc_info=True
        )
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
        applied_at=datetime.utcnow(),
    )
