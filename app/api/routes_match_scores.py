import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
import numpy as np
from app.db.session import get_db
from app.crud.application import get_application
from app.crud.resume import get_resume_by_user
from app.crud.match_score import get_match_score, create_or_update_match_score
from app.api.routes_auth import get_current_user
from app.models.user import User
from app.services.similarity_service import similarity_service, SimilarityServiceError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/applications/{application_id}/match-score")
def get_match_score_endpoint(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get similarity score between resume and job description.
    """
    # Verify the application belongs to the user
    application = get_application(db, application_id)
    if not application or application.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Application not found")

    # Get existing match score
    match_score = get_match_score(db, application_id)

    if not match_score:
        raise HTTPException(
            status_code=404,
            detail="Match score not found. Use recompute-match endpoint to calculate.",
        )

    # Return response matching API spec
    return {
        "application_id": str(match_score.application_id),
        "resume_id": str(match_score.resume_id),
        "similarity_score": match_score.similarity_score,
    }


@router.post("/applications/{application_id}/recompute-match")
def recompute_match_score(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recompute match score.
    """
    # Verify the application belongs to the user
    application = get_application(db, application_id)
    if not application or application.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Application not found")

    # Get user's resume
    resume = get_resume_by_user(db, current_user.id)
    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found. Please upload a resume first.",
        )

    # Check if embeddings exist - handle NumPy arrays properly
    if resume.embedding is None or (
        hasattr(resume.embedding, "size") and resume.embedding.size == 0
    ):
        raise HTTPException(
            status_code=400,
            detail="Resume embedding not available. Please re-upload your resume.",
        )

    if application.job_embedding is None or (
        hasattr(application.job_embedding, "size")
        and application.job_embedding.size == 0
    ):
        raise HTTPException(
            status_code=400, detail="Job description embedding not available."
        )

    try:
        # Calculate similarity score
        similarity_score = similarity_service.calculate_similarity_score(
            resume.embedding, application.job_embedding
        )

        # Store the match score
        match_score = create_or_update_match_score(
            db, application_id, resume.id, similarity_score
        )

        # Return response matching API spec
        return {
            "application_id": str(match_score.application_id),
            "resume_id": str(match_score.resume_id),
            "similarity_score": match_score.similarity_score,
        }

    except SimilarityServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unexpected error in recompute_match_score: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while computing match score",
        )
