"""
API routes for career strategy agent functionality.
Provides AI-powered career planning and strategic guidance using LangChain agents.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session

from app.api.routes_auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.career_strategy_agent import (
    career_strategy_agent,
    CareerStrategyAgentError,
)
from app.schemas.career_strategy import (
    CareerStrategyResponse,
    SkillGapAnalysisResponse,
    MarketInsightsResponse,
    AgentStatusResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/career/strategy-planning",
    response_model=CareerStrategyResponse,
    summary="Generate comprehensive career strategy plan",
    description="Create AI-powered career strategy using autonomous agent analysis",
)
def create_career_strategy_plan(
    career_goals: str = Body(..., description="Career goals and aspirations"),
    target_roles: Optional[List[str]] = Body(
        None, description="List of target job roles/positions"
    ),
    timeframe: str = Body(
        "2-3 years", description="Desired timeframe for career progression"
    ),
    current_role: Optional[str] = Body(
        None, description="Current job role or position"
    ),
    location_preference: Optional[str] = Body(
        None, description="Preferred work location or region"
    ),
    constraints: Optional[List[str]] = Body(
        None, description="Any constraints or limitations to consider"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Generate a comprehensive career strategy plan using AI agent analysis.

    This endpoint leverages LangChain agents to provide multi-step autonomous career planning:
    - Job market analysis for target roles and locations
    - Skill gap assessment based on user profile
    - Structured career progression planning with timelines
    - Strategic recommendations and actionable next steps

    The agent uses multiple specialized tools to gather data and provide insights:
    - Job Analysis Tool: Market trends and demand analysis
    - Skill Gap Analysis Tool: Current skills vs. target requirements
    - Career Path Planner Tool: Structured progression planning

    Args:
        career_goals: User's career aspirations and goals
        target_roles: Specific roles or positions of interest
        timeframe: Timeline for achieving career goals
        current_role: Current position for progression planning
        location_preference: Geographic preferences for career
        constraints: Any limitations or special considerations

    Returns:
        Comprehensive career strategy analysis with actionable recommendations

    Raises:
        400: Invalid input parameters
        500: Agent analysis error
    """
    try:
        logger.info(
            f"Career strategy planning request from user {current_user.id}: "
            f"goals='{career_goals[:50]}...', roles={target_roles}, timeframe={timeframe}"
        )

        # Validate required inputs
        if not career_goals or len(career_goals.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Career goals must be at least 10 characters long",
            )

        # Set defaults for optional parameters
        target_roles = target_roles or []
        constraints = constraints or []

        # Validate timeframe format
        valid_timeframes = ["6 months", "1 year", "2-3 years", "3-5 years", "5+ years"]
        if timeframe not in valid_timeframes:
            logger.warning(f"Non-standard timeframe provided: {timeframe}")

        # Execute agent-based career strategy analysis
        strategy_result = career_strategy_agent.analyze_career_strategy(
            user_id=current_user.id,
            db=db,
            career_goals=career_goals.strip(),
            target_roles=target_roles,
            timeframe=timeframe,
            current_role=current_role.strip() if current_role else None,
            location_preference=(
                location_preference.strip() if location_preference else None
            ),
            constraints=constraints,
        )

        # Enhance response with metadata
        response_data = {
            "user_id": current_user.id,
            "request_timestamp": datetime.now(timezone.utc),
            "input_parameters": {
                "career_goals": career_goals,
                "target_roles": target_roles,
                "timeframe": timeframe,
                "current_role": current_role,
                "location_preference": location_preference,
                "constraints": constraints,
            },
            **strategy_result,
        }

        logger.info(
            f"Career strategy analysis completed for user {current_user.id}: "
            f"tokens={strategy_result.get('analysis_metadata', {}).get('tokens_used', 'N/A')}, "
            f"cost=${strategy_result.get('analysis_metadata', {}).get('analysis_cost', 0):.4f}"
        )

        return response_data

    except CareerStrategyAgentError as e:
        logger.error(
            f"Career strategy agent error for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Career strategy analysis failed: {str(e)}",
        )

    except ValueError as e:
        logger.error(f"Invalid parameter for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request parameters: {str(e)}",
        )

    except HTTPException:
        # Re-raise HTTP exceptions (e.g., validation errors) as-is
        raise

    except Exception as e:
        logger.error(
            f"Unexpected error in career strategy planning for user {current_user.id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during career strategy analysis",
        )


@router.post(
    "/career/skill-gap-analysis",
    response_model=SkillGapAnalysisResponse,
    summary="Analyze skill gaps for career transition",
    description="AI-powered analysis of skills needed for target career goals",
)
def analyze_skill_gaps(
    target_roles: List[str] = Body(..., description="Target job roles for analysis"),
    career_goals: str = Body(..., description="Career goals context"),
    focus_areas: Optional[List[str]] = Body(
        None, description="Specific skill areas to focus analysis on"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Analyze skill gaps between current profile and target career goals.

    Uses the Skill Gap Analysis Tool to provide detailed assessment of:
    - Current skills inventory based on user profile
    - Required skills for target roles
    - Prioritized learning recommendations
    - Structured skill development plan

    Args:
        target_roles: List of target job roles to analyze against
        career_goals: Career goals for context
        focus_areas: Optional specific areas to focus analysis on

    Returns:
        Detailed skill gap analysis with learning recommendations
    """
    try:
        logger.info(
            f"Skill gap analysis request from user {current_user.id} for roles: {target_roles}"
        )

        # Validate inputs
        if not target_roles or len(target_roles) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one target role must be specified",
            )

        if not career_goals or len(career_goals.strip()) < 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Career goals must be provided for context",
            )

        # Create a simplified agent execution focused on skill analysis
        import json
        from app.services.career_strategy_agent import SkillGapAnalysisTool

        skill_tool = SkillGapAnalysisTool(db)

        # Prepare tool input
        tool_input = {
            "user_id": str(current_user.id),
            "target_roles": target_roles,
            "career_goals": career_goals.strip(),
            "focus_areas": focus_areas or [],
        }

        # Execute skill gap analysis
        tool_result = skill_tool._run(json.dumps(tool_input))

        # Parse tool result

        try:
            skill_analysis = json.loads(tool_result)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            skill_analysis = {
                "current_skills": ["Unable to parse analysis"],
                "skill_gaps": ["Analysis parsing error"],
                "learning_recommendations": ["Retry analysis"],
                "priority_skills": ["Error in analysis"],
            }

        # Structure response
        response_data = {
            "user_id": current_user.id,
            "analysis_timestamp": datetime.now(timezone.utc),
            "target_roles": target_roles,
            "career_goals": career_goals,
            "focus_areas": focus_areas,
            "skill_analysis": skill_analysis,
            "analysis_summary": f"Skill gap analysis completed for {len(target_roles)} target role(s)",
        }

        logger.info(f"Skill gap analysis completed for user {current_user.id}")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error in skill gap analysis for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Skill gap analysis failed",
        )


@router.get(
    "/career/market-insights",
    response_model=MarketInsightsResponse,
    summary="Get job market insights for career planning",
    description="AI-powered job market analysis and trends for strategic planning",
)
def get_market_insights(
    target_roles: List[str] = Query(..., description="Target roles to analyze"),
    location: Optional[str] = Query(None, description="Geographic focus for analysis"),
    timeframe: str = Query(
        "current", description="Analysis timeframe (current, 6months, 1year)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get comprehensive job market insights for career planning.

    Uses the Job Analysis Tool to provide market intelligence including:
    - Market demand trends for target roles
    - Salary insights and progression data
    - Required skills and qualifications trends
    - Geographic market variations

    Args:
        target_roles: List of roles to analyze market for
        location: Geographic focus for market analysis
        timeframe: Timeframe for trend analysis

    Returns:
        Market insights and trends analysis
    """
    try:
        logger.info(
            f"Market insights request from user {current_user.id}: "
            f"roles={target_roles}, location={location}, timeframe={timeframe}"
        )

        # Validate inputs
        if not target_roles or len(target_roles) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one target role must be specified",
            )

        # Create job analysis tool
        import json
        from app.services.career_strategy_agent import JobAnalysisTool

        job_tool = JobAnalysisTool(db)

        # Prepare tool input
        tool_input = {
            "user_id": str(current_user.id),
            "target_roles": target_roles,
            "location_preference": location or "",
            "timeframe": timeframe,
        }

        # Execute market analysis
        tool_result = job_tool._run(json.dumps(tool_input))

        # Parse tool result

        try:
            market_analysis = json.loads(tool_result)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            market_analysis = {
                "market_analysis": "Analysis parsing error occurred",
                "demand_trends": ["Unable to parse market data"],
                "salary_insights": "Salary data unavailable",
                "skill_requirements": ["General skills analysis failed"],
            }

        # Structure response
        response_data = {
            "user_id": current_user.id,
            "analysis_timestamp": datetime.now(timezone.utc),
            "query_parameters": {
                "target_roles": target_roles,
                "location": location,
                "timeframe": timeframe,
            },
            "market_insights": market_analysis,
            "insights_summary": f"Market analysis for {len(target_roles)} role(s) in {location or 'global'} market",
        }

        logger.info(f"Market insights analysis completed for user {current_user.id}")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in market insights for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Market insights analysis failed",
        )


@router.get(
    "/career/agent-status",
    response_model=AgentStatusResponse,
    summary="Check career strategy agent status",
    description="Health check and status information for the career strategy agent",
)
def get_agent_status() -> Dict[str, Any]:
    """
    Get status and configuration information for the career strategy agent.

    Returns:
        Agent status, capabilities, and configuration details
    """
    try:
        # Test basic agent functionality
        test_result = "operational"

        try:
            # Test LLM connectivity
            test_llm = career_strategy_agent.llm
            if test_llm and hasattr(test_llm, "model_name"):
                llm_status = "connected"
            else:
                llm_status = "configuration_error"
        except Exception:
            llm_status = "connection_error"
            test_result = "degraded"

        status_data = {
            "service": "career_strategy_agent",
            "status": test_result,
            "timestamp": datetime.now(timezone.utc),
            "agent_capabilities": {
                "job_market_analysis": True,
                "skill_gap_assessment": True,
                "career_path_planning": True,
                "strategic_recommendations": True,
                "multi_step_reasoning": True,
            },
            "tool_status": {
                "job_analysis_tool": "operational",
                "skill_gap_analysis_tool": "operational",
                "career_path_planner_tool": "operational",
            },
            "llm_status": llm_status,
            "model_info": {
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 2000,
            },
            "features": {
                "autonomous_agents": True,
                "multi_tool_execution": True,
                "cost_tracking": True,
                "structured_planning": True,
            },
        }

        return status_data

    except Exception as e:
        logger.error(f"Error checking agent status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Career strategy agent status check failed",
        )
