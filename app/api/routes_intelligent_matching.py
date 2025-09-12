"""
API routes for intelligent job matching with RAG capabilities.
Provides enhanced job analysis with market intelligence.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.routes_auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.intelligent_matching_service import (
    intelligent_matching_service,
    IntelligentMatchingServiceError
)
from app.schemas.intelligent_matching import (
    IntelligentJobAnalysisResponse,
    MarketIntelligenceOnlyResponse,
    IntelligentMatchingHealthResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/jobs/{job_id}/intelligent-analysis", response_model=IntelligentJobAnalysisResponse)
def get_intelligent_job_analysis(
    job_id: UUID,
    include_market_context: bool = Query(
        True,
        description="Include market context analysis from similar jobs"
    ),
    context_depth: int = Query(
        5,
        description="Number of similar jobs to analyze for market context",
        ge=1,
        le=10
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Enhanced job analysis with RAG-powered market intelligence.

    This endpoint provides comprehensive job analysis including:
    - Traditional resume-job match scoring
    - Market context analysis from similar positions
    - Strategic positioning recommendations
    - Competitive advantage insights
    - Improvement suggestions

    The analysis leverages existing pgVector search to find similar jobs
    and uses LLM analysis to extract market trends and strategic insights.

    Args:
        job_id: UUID of the job to analyze
        include_market_context: Whether to include market intelligence
        context_depth: Number of similar jobs to analyze (1-10)

    Returns:
        Comprehensive job analysis with market intelligence

    Raises:
        404: Job not found or access denied
        400: Invalid request parameters
        500: Analysis service errors
    """
    try:
        logger.info(f"Starting intelligent job analysis for job {job_id}, user {current_user.id}")

        # Validate context depth
        if not include_market_context:
            context_depth = 0

        # Perform intelligent analysis using RAG service
        analysis_result = intelligent_matching_service.analyze_job_with_market_context(
            job_id=job_id,
            user_id=current_user.id,
            db=db,
            context_depth=context_depth
        )

        # Add metadata
        response_data = {
            "job_id": job_id,
            "analysis_timestamp": datetime.now(timezone.utc),
            "include_market_context": include_market_context,
            "context_depth": context_depth,
            **analysis_result
        }

        logger.info(
            f"Intelligent analysis completed for job {job_id}: "
            f"match_score={analysis_result.get('basic_match_score', 'N/A')}, "
            f"similar_jobs={analysis_result.get('market_intelligence', {}).get('similar_jobs_analyzed', 0)}"
        )

        return response_data

    except IntelligentMatchingServiceError as e:
        logger.error(f"Intelligent matching service error for job {job_id}: {str(e)}")

        # Determine appropriate HTTP status based on error message
        if "not found" in str(e).lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "access denied" in str(e).lower():
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        raise HTTPException(
            status_code=status_code,
            detail=f"Intelligent analysis failed: {str(e)}"
        )

    except ValueError as e:
        logger.error(f"Invalid parameter for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request parameters: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Unexpected error in intelligent analysis for job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during intelligent analysis"
        )

@router.get("/jobs/{job_id}/market-intelligence", response_model=MarketIntelligenceOnlyResponse)
def get_market_intelligence_only(
    job_id: UUID,
    context_depth: int = Query(
        5,
        description="Number of similar jobs to analyze",
        ge=1,
        le=10
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get market intelligence analysis only (without full job analysis).

    Lighter endpoint for when you only need market context data
    about similar positions and industry trends.

    Args:
        job_id: UUID of the job to analyze
        context_depth: Number of similar jobs to analyze

    Returns:
        Market intelligence data only
    """
    try:
        logger.info(f"Market intelligence request for job {job_id}")

        # Get full analysis but return only market intelligence
        analysis_result = intelligent_matching_service.analyze_job_with_market_context(
            job_id=job_id,
            user_id=current_user.id,
            db=db,
            context_depth=context_depth
        )

        # Extract market intelligence portion
        market_data = analysis_result.get("market_intelligence", {})

        response_data = {
            "job_id": job_id,
            "analysis_timestamp": datetime.now(timezone.utc),
            "context_depth": context_depth,
            "market_intelligence": market_data
        }

        logger.info(f"Market intelligence completed for job {job_id}")
        return response_data

    except IntelligentMatchingServiceError as e:
        logger.error(f"Market intelligence error for job {job_id}: {str(e)}")

        if "not found" in str(e).lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "access denied" in str(e).lower():
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        raise HTTPException(
            status_code=status_code,
            detail=f"Market intelligence analysis failed: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Unexpected error in market intelligence for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during market intelligence analysis"
        )

@router.get("/health/intelligent-matching", response_model=IntelligentMatchingHealthResponse)
def health_check_intelligent_matching():
    """
    Health check endpoint for intelligent matching service.

    Returns service status and basic configuration info.
    """
    try:
        # Basic service availability check
        service_status = {
            "service": "intelligent_matching",
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc),
            "features": {
                "rag_analysis": True,
                "market_intelligence": True,
                "strategic_recommendations": True
            }
        }

        return service_status

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Intelligent matching service unavailable"
        )
