"""
Pydantic schemas for career strategy agent responses.
Defines data structures for LangChain agent-based career planning results.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


class CareerPhase(BaseModel):
    """
    Represents a phase in career progression planning.
    Structured timeline-based career development stage.
    """

    phase: str = Field(
        ..., description="Phase identifier and timeframe (e.g., 'Phase 1 (Months 1-6)')"
    )
    objectives: List[str] = Field(
        default_factory=list, description="Key objectives to achieve during this phase"
    )
    key_actions: List[str] = Field(
        default_factory=list, description="Specific actions and activities to complete"
    )
    success_metrics: List[str] = Field(
        default_factory=list, description="Measurable success indicators for the phase"
    )


class SkillAnalysisData(BaseModel):
    """
    Comprehensive skill analysis results from agent assessment.
    Includes current skills, gaps, and learning recommendations.
    """

    current_skills: List[str] = Field(
        default_factory=list,
        description="Currently demonstrated skills and competencies",
    )
    skill_gaps: List[str] = Field(
        default_factory=list,
        description="Identified gaps between current and target skills",
    )
    learning_recommendations: List[str] = Field(
        default_factory=list, description="Specific learning actions and resources"
    )
    priority_skills: List[str] = Field(
        default_factory=list, description="High-priority skills to develop first"
    )


class MarketInsightsData(BaseModel):
    """
    Job market intelligence from agent analysis.
    Market trends, demand, and competitive landscape insights.
    """

    market_analysis: str = Field(..., description="Overall market condition assessment")
    demand_trends: List[str] = Field(
        default_factory=list, description="Market demand trends and patterns"
    )
    salary_insights: str = Field(
        ..., description="Salary range and progression insights"
    )
    skill_requirements: List[str] = Field(
        default_factory=list, description="In-demand skills and qualifications"
    )


class CareerPlanData(BaseModel):
    """
    Structured career progression plan from agent planning.
    Multi-phase career development with timelines and milestones.
    """

    career_phases: List[CareerPhase] = Field(
        default_factory=list, description="Structured phases of career progression"
    )
    key_milestones: List[str] = Field(
        default_factory=list, description="Major milestones and achievements to target"
    )
    potential_challenges: List[str] = Field(
        default_factory=list, description="Anticipated challenges and obstacles"
    )
    success_strategies: List[str] = Field(
        default_factory=list, description="Strategic approaches for achieving success"
    )


class AgentAnalysisMetadata(BaseModel):
    """
    Metadata about the agent analysis execution.
    Cost tracking, performance metrics, and execution details.
    """

    user_id: str = Field(..., description="User ID for the analysis")
    analysis_timestamp: str = Field(
        ..., description="ISO timestamp when analysis was performed"
    )
    tokens_used: Optional[int] = Field(
        None, description="Number of tokens consumed by the analysis", ge=0
    )
    analysis_cost: Optional[float] = Field(
        None, description="Cost in USD for the analysis", ge=0.0
    )
    agent_iterations: Optional[int] = Field(
        None, description="Number of agent reasoning iterations", ge=0
    )


class CareerStrategyResponse(BaseModel):
    """
    Comprehensive career strategy analysis response.
    Main response model for career strategy planning endpoint.
    """

    user_id: UUID = Field(..., description="User ID for the career strategy analysis")
    request_timestamp: datetime = Field(
        ..., description="Timestamp when the request was processed"
    )

    # Input parameters for reference
    input_parameters: Dict[str, Any] = Field(
        ..., description="Input parameters used for the analysis"
    )

    # Core analysis results from agent
    analysis_summary: str = Field(
        ..., description="Comprehensive narrative summary from the agent"
    )
    market_analysis: Optional[MarketInsightsData] = Field(
        None, description="Job market insights and trends analysis"
    )
    skill_analysis: Optional[SkillAnalysisData] = Field(
        None, description="Skill gap analysis and learning recommendations"
    )
    career_plan: Optional[CareerPlanData] = Field(
        None, description="Structured career progression plan"
    )

    # Strategic outputs
    strategic_recommendations: List[str] = Field(
        default_factory=list,
        description="Key strategic recommendations from agent analysis",
    )
    next_steps: List[str] = Field(
        default_factory=list, description="Immediate actionable next steps"
    )

    # Analysis metadata
    analysis_metadata: Optional[AgentAnalysisMetadata] = Field(
        None, description="Metadata about the agent analysis execution"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}
        schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "request_timestamp": "2024-01-15T10:30:00Z",
                "input_parameters": {
                    "career_goals": "Transition to senior data scientist role",
                    "target_roles": ["Senior Data Scientist", "ML Engineer"],
                    "timeframe": "2-3 years",
                    "current_role": "Data Analyst",
                    "location_preference": "San Francisco Bay Area",
                },
                "analysis_summary": "Based on comprehensive analysis, transitioning to a senior data scientist role is highly achievable within the 2-3 year timeframe...",
                "market_analysis": {
                    "market_analysis": "Strong demand for data science professionals in SF Bay Area",
                    "demand_trends": [
                        "Machine learning roles growing 25% annually",
                        "Strong demand for Python and deep learning skills",
                        "Remote-friendly positions increasing",
                    ],
                    "salary_insights": "Senior Data Scientists: $150K-$220K in SF Bay Area",
                    "skill_requirements": [
                        "Python",
                        "Machine Learning",
                        "Deep Learning",
                        "SQL",
                    ],
                },
                "skill_analysis": {
                    "current_skills": ["Python", "SQL", "Data Analysis", "Statistics"],
                    "skill_gaps": ["Deep Learning", "MLOps", "Distributed Computing"],
                    "learning_recommendations": [
                        "Complete deep learning specialization",
                        "Gain hands-on experience with Kubernetes",
                        "Build portfolio of ML projects",
                    ],
                    "priority_skills": ["Deep Learning", "MLOps"],
                },
                "career_plan": {
                    "career_phases": [
                        {
                            "phase": "Phase 1 (Months 1-8)",
                            "objectives": ["Skill development", "Portfolio building"],
                            "key_actions": ["Complete ML courses", "Build 3 projects"],
                            "success_metrics": [
                                "Certifications obtained",
                                "Portfolio published",
                            ],
                        }
                    ],
                    "key_milestones": ["Complete ML certification", "Land senior role"],
                    "potential_challenges": [
                        "Competition for senior roles",
                        "Skill acquisition time",
                    ],
                    "success_strategies": [
                        "Consistent learning",
                        "Networking",
                        "Project experience",
                    ],
                },
                "strategic_recommendations": [
                    "Focus on deep learning skills as top priority",
                    "Build a strong portfolio showcasing ML projects",
                    "Network with data science professionals in target companies",
                ],
                "next_steps": [
                    "Enroll in deep learning course within 2 weeks",
                    "Identify 3 target companies for networking",
                    "Begin first ML portfolio project",
                ],
                "analysis_metadata": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "analysis_timestamp": "2024-01-15T10:30:00Z",
                    "tokens_used": 1250,
                    "analysis_cost": 0.0025,
                    "agent_iterations": 3,
                },
            }
        }


class SkillGapAnalysisResponse(BaseModel):
    """
    Response for skill gap analysis endpoint.
    Focused response for skills assessment without full career planning.
    """

    user_id: UUID = Field(..., description="User ID for the analysis")
    analysis_timestamp: datetime = Field(
        ..., description="Timestamp when analysis was performed"
    )
    target_roles: List[str] = Field(..., description="Target roles analyzed")
    career_goals: str = Field(..., description="Career goals context for analysis")
    focus_areas: Optional[List[str]] = Field(
        None, description="Specific focus areas for analysis"
    )

    skill_analysis: SkillAnalysisData = Field(
        ..., description="Detailed skill gap analysis results"
    )
    analysis_summary: str = Field(
        ..., description="Summary of the skill analysis performed"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class MarketInsightsResponse(BaseModel):
    """
    Response for market insights analysis endpoint.
    Market intelligence focused response without full career planning.
    """

    user_id: UUID = Field(..., description="User ID for the analysis")
    analysis_timestamp: datetime = Field(
        ..., description="Timestamp when analysis was performed"
    )
    query_parameters: Dict[str, Any] = Field(
        ..., description="Parameters used for the market analysis"
    )

    market_insights: MarketInsightsData = Field(
        ..., description="Comprehensive market analysis results"
    )
    insights_summary: str = Field(
        ..., description="Summary of the market insights analysis"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class AgentStatusResponse(BaseModel):
    """
    Response for career strategy agent status endpoint.
    Service health and capability information.
    """

    service: str = Field(..., description="Service name identifier")
    status: str = Field(
        ...,
        description="Current service status",
        pattern="^(operational|degraded|unavailable)$",
    )
    timestamp: datetime = Field(..., description="Status check timestamp")

    agent_capabilities: Dict[str, bool] = Field(
        ..., description="Available agent capabilities and their status"
    )
    tool_status: Dict[str, str] = Field(
        ..., description="Status of individual agent tools"
    )
    llm_status: str = Field(
        ..., description="LLM connectivity and configuration status"
    )
    model_info: Dict[str, Any] = Field(
        ..., description="LLM model configuration information"
    )
    features: Dict[str, bool] = Field(..., description="Available service features")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


# Error response schemas
class CareerStrategyError(BaseModel):
    """
    Error response for career strategy operations.
    Standardized error information for troubleshooting.
    """

    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for programmatic handling")
    user_id: Optional[UUID] = Field(
        None, description="User ID that encountered the error, if applicable"
    )
    timestamp: datetime = Field(..., description="Error timestamp")
    request_details: Optional[Dict[str, Any]] = Field(
        None, description="Request details that caused the error"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}
