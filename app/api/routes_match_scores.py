import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
import numpy as np
from app.db.session import get_db
from app.crud import job as crud_job
from app.crud.resume import get_resume_by_user
from app.crud.match_score import get_match_score, create_or_update_match_score
from app.api.routes_auth import get_current_user
from app.models.user import User
from app.services.similarity_service import similarity_service, SimilarityServiceError

logger = logging.getLogger(__name__)
router = APIRouter()


# New job-based match score endpoints (these should be in routes_jobs.py)
@router.get("/jobs/{job_id}/match-score")
def get_job_match_score(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get similarity score between resume and job description.
    """
    # Verify the job belongs to the user
    job = crud_job.get_job(db, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get existing match score from match_scores table
    match_score = get_match_score(db, job_id)

    if not match_score:
        # If no match score in table, check if job has match_score field
        if job.match_score is not None:
            resume = get_resume_by_user(db, current_user.id)
            if not resume:
                raise HTTPException(
                    status_code=404,
                    detail="Resume not found. Please upload a resume first.",
                )
            return {
                "job_id": str(job_id),
                "resume_id": str(resume.id),
                "similarity_score": job.match_score,
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Match score not found. Use POST /jobs/{job_id}/match to calculate.",
            )

    # Return response matching API spec
    return {
        "job_id": str(match_score.job_id),
        "resume_id": str(match_score.resume_id),
        "similarity_score": match_score.similarity_score,
    }
