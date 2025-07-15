import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case
from app.db.session import get_db
from app.api.routes_auth import get_current_user
from app.models.user import User
from app.models.job import Job, JobStatus
from app.models.match_score import MatchScore

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/analytics/status-summary")
def get_status_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get count of jobs by status.
    """
    try:
        # Query jobs grouped by status
        status_counts = (
            db.query(
                Job.status,
                func.count(Job.id).label("count"),
            )
            .filter(Job.user_id == current_user.id)
            .group_by(Job.status)
            .all()
        )

        # Convert to dictionary format
        summary = {}
        for status_enum in JobStatus:
            summary[status_enum.value] = 0

        for status_enum, count in status_counts:
            summary[status_enum.value] = count

        return {"status_summary": summary, "total_jobs": sum(summary.values())}

    except Exception as e:
        logger.error(f"Error getting status summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving status summary",
        )


@router.get("/analytics/jobs-over-time")
def get_jobs_over_time(
    period: str = Query("weekly", description="Time period: weekly or monthly"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get jobs count over time (weekly/monthly).
    """
    try:
        if period not in ["weekly", "monthly"]:
            raise HTTPException(
                status_code=400, detail="Period must be either 'weekly' or 'monthly'"
            )

        # Calculate date range (last 12 periods)
        end_date = datetime.now()
        if period == "weekly":
            start_date = end_date - timedelta(weeks=12)
            date_format = "%Y-W%U"  # Year-Week format
            date_extract = extract("year", Job.created_at)
            period_extract = extract("week", Job.created_at)
        else:  # monthly
            start_date = end_date - timedelta(days=365)
            date_format = "%Y-%m"  # Year-Month format
            date_extract = extract("year", Job.created_at)
            period_extract = extract("month", Job.created_at)

        # Query jobs over time
        jobs_over_time = (
            db.query(
                date_extract.label("year"),
                period_extract.label("period"),
                func.count(Job.id).label("count"),
            )
            .filter(
                Job.user_id == current_user.id,
                Job.created_at >= start_date,
                Job.created_at <= end_date,
            )
            .group_by(date_extract, period_extract)
            .order_by(date_extract, period_extract)
            .all()
        )

        # Format results
        results = []
        for year, period_num, count in jobs_over_time:
            year_int = int(year)
            period_int = int(period_num)  # ensure integer

            if period == "weekly":
                period_label = f"{year_int}-W{period_int:02d}"
            else:
                period_label = f"{year_int}-{period_int:02d}"

            results.append({"period": period_label, "count": count})

        return {"period": period, "jobs_over_time": results}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting jobs over time: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving jobs over time",
        )


@router.get("/analytics/match-score-summary")
def get_match_score_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get average match score across jobs.
    """
    try:
        # Query match score statistics
        match_score_stats = (
            db.query(
                func.avg(MatchScore.similarity_score).label("average_score"),
                func.min(MatchScore.similarity_score).label("min_score"),
                func.max(MatchScore.similarity_score).label("max_score"),
                func.count(MatchScore.id).label("total_scores"),
            )
            .join(Job, MatchScore.job_id == Job.id)
            .filter(Job.user_id == current_user.id)
            .first()
        )

        # Get score distribution
        score_distribution = (
            db.query(
                case(
                    (MatchScore.similarity_score >= 0.8, "excellent"),
                    (MatchScore.similarity_score >= 0.6, "good"),
                    (MatchScore.similarity_score >= 0.4, "fair"),
                    else_="poor",
                ).label("category"),
                func.count(MatchScore.id).label("count"),
            )
            .join(Job, MatchScore.job_id == Job.id)
            .filter(Job.user_id == current_user.id)
            .group_by("category")
            .all()
        )

        # Format distribution
        distribution = {
            "excellent": 0,  # 0.8-1.0
            "good": 0,  # 0.6-0.79
            "fair": 0,  # 0.4-0.59
            "poor": 0,  # 0.0-0.39
        }

        for category, count in score_distribution:
            distribution[category] = count

        # Format response
        summary = {
            "average_score": (
                float(match_score_stats.average_score)
                if match_score_stats.average_score
                else 0.0
            ),
            "min_score": (
                float(match_score_stats.min_score)
                if match_score_stats.min_score
                else 0.0
            ),
            "max_score": (
                float(match_score_stats.max_score)
                if match_score_stats.max_score
                else 0.0
            ),
            "total_scores": match_score_stats.total_scores,
            "score_distribution": distribution,
        }

        return summary

    except Exception as e:
        logger.error(f"Error getting match score summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving match score summary",
        )
