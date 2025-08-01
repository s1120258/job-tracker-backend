# app/api/routes_jobs.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
from app.db.session import get_db
from app.schemas.job import (
    JobCreate,
    JobUpdate,
    JobRead,
    JobMatchResponse,
    JobApplyRequest,
    JobApplyResponse,
    JobStatus,
    JobSummaryRequest,
    JobSummaryResponse,
)
from app.models.job import JobStatus as ModelJobStatus
from app.crud import job as crud_job
from app.crud.resume import get_resume_by_user
from app.crud.match_score import create_or_update_match_score
from app.api.routes_auth import get_current_user
from app.models.user import User
from app.services.similarity_service import similarity_service, SimilarityServiceError
from app.services.job_scraper_service import job_scraper_service, JobBoardType
from app.services.embedding_service import embedding_service, EmbeddingServiceError
from app.services.skill_extraction_service import (
    skill_extraction_service,
    SkillExtractionServiceError,
)
from app.services.skill_analysis_service import (
    skill_analysis_service,
    SkillAnalysisServiceError,
)
from app.services.llm_service import llm_service, LLMServiceError
from app.schemas.skill_analysis import (
    SkillGapAnalysisResponse,
    ResumeSkillsResponse,
    JobSkillsResponse,
)
from app.schemas.job import JobSkillExtractionResponse, ResumeSkillExtractionResponse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def calculate_job_match_score(
    job_description: str, user_resume_embedding: list[float]
) -> float:
    """
    Calculate match score between job description and user resume.

    Args:
        job_description: Job description text
        user_resume_embedding: User's resume embedding vector

    Returns:
        float: Match score between 0 and 1
    """
    try:
        # Generate embedding for job description
        job_embedding = embedding_service.generate_embedding(job_description)

        # Calculate similarity score
        similarity_score = similarity_service.calculate_similarity_score(
            user_resume_embedding, job_embedding
        )

        return similarity_score

    except (EmbeddingServiceError, SimilarityServiceError) as e:
        logger.error("Error calculating match score: %s", e)
        return 0.0
    except Exception as e:
        logger.error("Unexpected error in match score calculation: %s", e)
        return 0.0


@router.get("/jobs/search")
def search_jobs(
    keyword: Optional[str] = Query(None, description="Search keyword"),
    location: Optional[str] = Query(None, description="Job location"),
    source: JobBoardType = Query(
        "remoteok", enum=["remoteok"], description="Job board source (e.g., 'remoteok')"
    ),
    sort_by: str = Query("date", enum=["date", "match_score"]),
    limit: int = Query(
        20, description="Maximum number of jobs to return", ge=1, le=100
    ),
    fetch_full_description: bool = Query(
        True, description="Whether to fetch full job descriptions"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search jobs from external job boards.

    Can sort by date (newest first) or match_score (highest match first).
    Match score sorting requires an uploaded resume with embedding.

    For saved jobs management, use GET /jobs endpoint.
    """
    all_jobs = []

    # Check if user resume is required for match score sorting
    user_resume = None
    if sort_by == "match_score":
        user_resume = get_resume_by_user(db, current_user.id)
        if (
            user_resume is None
            or user_resume.embedding is None
            or (
                hasattr(user_resume.embedding, "size")
                and user_resume.embedding.size == 0
            )
            or (
                hasattr(user_resume.embedding, "__len__")
                and len(user_resume.embedding) == 0
            )
        ):
            raise HTTPException(
                status_code=400,
                detail="Resume with embedding required for match score sorting. Please upload a resume first.",
            )

    # Search external job boards
    if keyword:
        try:
            logger.info("Searching external job boards for keyword: %s", keyword)
            # Adjust limit for match score sorting to get more candidates
            search_limit = limit if sort_by == "date" else min(limit * 2, 100)

            external_jobs = job_scraper_service.search_jobs(
                keyword=keyword,
                location=location or "",
                source=source.value if source else None,
                limit=search_limit,
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
                    "match_score": None,  # Will be calculated if needed
                }

                # Calculate match score if sorting by match_score
                if sort_by == "match_score" and user_resume:
                    try:
                        match_score = calculate_job_match_score(
                            job_description=job.get("description", ""),
                            user_resume_embedding=user_resume.embedding,
                        )
                        search_result["match_score"] = match_score
                        logger.info(
                            "Calculated match score %.2f for job: %s",
                            match_score,
                            job.get("title", ""),
                        )
                    except Exception as e:
                        logger.warning(
                            "Failed to calculate match score for job '%s': %s",
                            job.get("title", ""),
                            e,
                        )
                        search_result["match_score"] = 0.0

                all_jobs.append(search_result)

            logger.info("Found %d external jobs", len(external_jobs))

        except Exception as e:
            logger.error("Error searching external job boards: %s", e)
            # Continue to search saved jobs if external search fails

        # If no keyword provided, return error
    if not keyword:
        raise HTTPException(
            status_code=400,
            detail="Search keyword is required for external job board search",
        )

    # Sort jobs based on specified criteria
    if sort_by == "match_score":
        # Sort by match score descending (highest match first)
        all_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        logger.info("Sorted %d jobs by match score", len(all_jobs))
    else:
        # Sort by date posted descending (newest first)
        all_jobs.sort(key=lambda x: x.get("date_posted") or "", reverse=True)
        logger.info("Sorted %d jobs by date", len(all_jobs))

    # Apply overall limit if needed
    if len(all_jobs) > limit:
        all_jobs = all_jobs[:limit]

    # Calculate match score statistics for match_score sorting
    match_stats = None
    if sort_by == "match_score" and all_jobs:
        match_scores = [
            job.get("match_score", 0)
            for job in all_jobs
            if job.get("match_score") is not None
        ]
        if match_scores:
            match_stats = {
                "average_score": sum(match_scores) / len(match_scores),
                "highest_score": max(match_scores),
                "lowest_score": min(match_scores),
                "jobs_with_scores": len(match_scores),
            }

    return {
        "jobs": all_jobs,
        "total_found": len(all_jobs),
        "sort_by": sort_by,
        "match_statistics": match_stats,
        "search_params": {
            "keyword": keyword,
            "location": location,
            "source": source,
            "limit": limit,
            "sort_by": sort_by,
        },
        "available_sources": job_scraper_service.get_available_sources(),
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
    model_status = ModelJobStatus(status.value) if status is not None else None
    return crud_job.get_jobs(db, user_id=current_user.id, status=model_status)


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


@router.get("/jobs/{job_id}/match-score", response_model=JobMatchResponse)
def get_or_calculate_match_score(
    job_id: UUID,
    force_recalculate: bool = Query(
        False, description="Force recalculation even if match score already exists"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get or calculate match score between job and resume."""
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

    # Check if we already have a match score for this job
    existing_match = crud_job.get_match_score(db, job_id)

    # If force_recalculate is not requested and we have existing score, return it
    if existing_match and not force_recalculate:
        logger.info(f"Returning existing match score for job {job_id}")
        return JobMatchResponse(
            job_id=job_id,
            resume_id=existing_match.resume_id,
            similarity_score=existing_match.similarity_score,
            status=JobStatus.matched,
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

        action = "Recalculated" if existing_match else "Calculated new"
        logger.info(f"{action} match score {similarity_score:.3f} for job {job_id}")

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


@router.get("/jobs/{job_id}/skills", response_model=JobSkillExtractionResponse)
def extract_job_skills(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Extract skills and requirements from a specific job description.

    This endpoint analyzes a job posting to identify:
    - Required vs preferred skills
    - Skill categories and importance levels
    - Experience and education requirements
    """
    # Verify the job belongs to the user
    job = crud_job.get_job(db, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        # Extract skills from job description with normalization
        skills_data = skill_extraction_service.extract_skills_from_job(
            job_description=job.description, job_title=job.title, normalize=True
        )

        # Create JobSkillsResponse from extracted data
        job_skills_response = JobSkillsResponse(**skills_data)

        response = JobSkillExtractionResponse(
            job_id=job_id,
            skills_data=job_skills_response,
            extraction_timestamp=datetime.utcnow(),
        )

        logger.info(f"Successfully extracted skills from job {job_id}")
        return response

    except SkillExtractionServiceError as e:
        logger.error(f"Skill extraction service error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Skill extraction failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error extracting job skills: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error during skill extraction"
        )


@router.get(
    "/jobs/{job_id}/skill-gap-analysis", response_model=SkillGapAnalysisResponse
)
def analyze_skill_gap(
    job_id: UUID,
    resume_id: Optional[UUID] = Query(
        None, description="Specific resume ID to use (optional)"
    ),
    include_learning_recommendations: bool = Query(
        True, description="Whether to include learning recommendations"
    ),
    include_experience_analysis: bool = Query(
        True, description="Whether to include experience gap analysis"
    ),
    include_education_analysis: bool = Query(
        True, description="Whether to include education matching"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Perform comprehensive skill gap analysis between user's resume and job requirements.

    This endpoint analyzes the match between a user's skills (from their resume) and
    the requirements of a specific job, providing detailed insights including:
    - Skill strengths and gaps
    - Learning recommendations
    - Experience and education gap analysis
    - Application advice
    """
    # Verify the job belongs to the user
    job = crud_job.get_job(db, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get user's resume (use specific resume_id if provided, otherwise get user's current resume)
    if resume_id:
        resume = get_resume_by_user(db, current_user.id)
        if not resume or resume.id != resume_id:
            raise HTTPException(status_code=404, detail="Resume not found")
    else:
        resume = get_resume_by_user(db, current_user.id)
        if not resume:
            raise HTTPException(
                status_code=404,
                detail="Resume not found. Please upload a resume first.",
            )

    # Validate resume has extracted text
    if not resume.extracted_text or not resume.extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Resume text not available. Please re-upload your resume.",
        )

    try:
        # Extract skills from both resume and job first
        resume_skills_data = skill_extraction_service.extract_skills_from_resume(
            resume_text=resume.extracted_text, normalize=True
        )
        job_skills_data = skill_extraction_service.extract_skills_from_job(
            job_description=job.description, job_title=job.title, normalize=True
        )

        # Perform skill gap analysis using the extracted skills data
        analysis_data = skill_analysis_service.analyze_skill_gap(
            resume_skills_data=resume_skills_data,
            job_skills_data=job_skills_data,
            job_title=job.title,
            normalize=True,
        )

        # Create response with additional metadata
        response_data = SkillGapAnalysisResponse(
            job_id=job_id,
            resume_id=resume.id,
            analysis_timestamp=datetime.utcnow().isoformat(),
            **analysis_data,
        )

        logger.info(
            f"Successfully completed skill gap analysis for job {job_id} and resume {resume.id}"
        )

        return response_data

    except (SkillExtractionServiceError, SkillAnalysisServiceError) as e:
        logger.error(f"Skill service error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Skill analysis failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in skill gap analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error during skill gap analysis"
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


@router.post("/jobs/summary", response_model=JobSummaryResponse)
def generate_job_summary(
    summary_request: JobSummaryRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate a concise summary from a full job description.

    This endpoint is useful for:
    - Displaying short summaries in job detail pages
    - Showing brief descriptions in modal dialogs
    - Converting HTML job descriptions to readable summaries

    The LLM will clean HTML formatting and generate an engaging summary
    with key points that job seekers need to know.
    """
    try:
        # Generate summary using LLM service
        summary_data = llm_service.generate_job_summary(
            job_description=summary_request.job_description,
            job_title=summary_request.job_title,
            company_name=summary_request.company_name,
            max_length=summary_request.max_length
        )

        # Create response
        response = JobSummaryResponse(
            original_length=summary_data["original_length"],
            summary=summary_data["summary"],
            summary_length=summary_data["summary_length"],
            key_points=summary_data["key_points"],
            generated_at=summary_data["generated_at"],
        )

        logger.info(
            f"Successfully generated job summary for user {current_user.id}: "
            f"{summary_data['original_length']} chars -> {summary_data['summary_length']} words"
        )

        return response

    except LLMServiceError as e:
        logger.error(f"LLM service error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate job summary: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error generating job summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during summary generation"
        )
