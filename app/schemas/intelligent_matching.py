"""
Pydantic schemas for intelligent job matching responses.
Defines data structures for RAG-powered job analysis results.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

class MarketIntelligenceData(BaseModel):
    """
    Market intelligence extracted from similar job positions.
    Provides market context and positioning insights.
    """
    similar_jobs_analyzed: int = Field(
        ..., 
        description="Number of similar jobs analyzed for market context",
        ge=0
    )
    average_similarity_score: float = Field(
        ..., 
        description="Average similarity score to analyzed market positions",
        ge=0.0,
        le=1.0
    )
    market_positioning: str = Field(
        ..., 
        description="Market positioning assessment (e.g., premium/standard/entry-level)"
    )
    salary_range_insight: Optional[str] = Field(
        None, 
        description="Estimated salary range insight based on similar positions"
    )
    skill_trend_analysis: List[str] = Field(
        default_factory=list, 
        description="Key skill trends identified in this market segment"
    )
    demand_assessment: str = Field(
        ..., 
        description="Market demand evaluation (e.g., high/medium/low demand)"
    )

class StrategicRecommendation(BaseModel):
    """
    Strategic recommendation for job application approach.
    Provides actionable advice for candidates.
    """
    category: str = Field(
        ..., 
        description="Recommendation category (e.g., Strategic, Technical, General)"
    )
    recommendation: str = Field(
        ..., 
        description="Specific actionable recommendation"
    )
    priority: str = Field(
        ..., 
        description="Priority level for this recommendation",
        regex="^(High|Medium|Low)$"
    )

class IntelligentJobAnalysisResponse(BaseModel):
    """
    Comprehensive response for intelligent job analysis.
    Combines traditional matching with RAG-powered market intelligence.
    """
    job_id: UUID = Field(
        ..., 
        description="UUID of the analyzed job"
    )
    analysis_timestamp: datetime = Field(
        ..., 
        description="Timestamp when the analysis was performed"
    )
    include_market_context: bool = Field(
        ..., 
        description="Whether market context analysis was included"
    )
    context_depth: int = Field(
        ..., 
        description="Number of similar jobs analyzed for context",
        ge=0,
        le=10
    )
    
    # Core analysis results
    basic_match_score: Optional[float] = Field(
        None, 
        description="Traditional resume-job similarity score (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    
    # Market intelligence (RAG-powered)
    market_intelligence: MarketIntelligenceData = Field(
        ..., 
        description="Market analysis based on similar job positions"
    )
    
    # Strategic insights
    strategic_recommendations: List[StrategicRecommendation] = Field(
        default_factory=list, 
        description="Strategic recommendations for job application"
    )
    competitive_advantages: List[str] = Field(
        default_factory=list, 
        description="Candidate's competitive advantages for this position"
    )
    improvement_suggestions: List[str] = Field(
        default_factory=list, 
        description="Areas for improvement before applying"
    )
    
    # Metadata
    job_title: Optional[str] = Field(
        None, 
        description="Title of the analyzed job"
    )
    company_name: Optional[str] = Field(
        None, 
        description="Company name for the analyzed job"
    )
    analysis_summary: Optional[str] = Field(
        None, 
        description="Brief summary of the analysis performed"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "analysis_timestamp": "2024-01-15T10:30:00Z",
                "include_market_context": True,
                "context_depth": 5,
                "basic_match_score": 0.78,
                "market_intelligence": {
                    "similar_jobs_analyzed": 5,
                    "average_similarity_score": 0.72,
                    "market_positioning": "Standard market position",
                    "salary_range_insight": "Competitive salary range: $80K-$120K",
                    "skill_trend_analysis": [
                        "Python and FastAPI in high demand",
                        "Cloud experience increasingly valued",
                        "AI/ML skills becoming standard"
                    ],
                    "demand_assessment": "High market demand"
                },
                "strategic_recommendations": [
                    {
                        "category": "Strategic",
                        "recommendation": "Emphasize your FastAPI experience early in application",
                        "priority": "High"
                    },
                    {
                        "category": "Technical",
                        "recommendation": "Highlight cloud deployment experience",
                        "priority": "Medium"
                    }
                ],
                "competitive_advantages": [
                    "5+ years Python experience exceeds market average",
                    "Full-stack capabilities provide versatility"
                ],
                "improvement_suggestions": [
                    "Consider AWS certification to strengthen cloud credentials",
                    "Build portfolio demonstrating AI/ML applications"
                ],
                "job_title": "Senior Python Developer",
                "company_name": "Tech Innovations Inc",
                "analysis_summary": "Analyzed 5 similar positions for market context"
            }
        }

class MarketIntelligenceOnlyResponse(BaseModel):
    """
    Response for market intelligence only requests.
    Lighter response focusing on market analysis.
    """
    job_id: UUID = Field(
        ..., 
        description="UUID of the analyzed job"
    )
    analysis_timestamp: datetime = Field(
        ..., 
        description="Timestamp when the analysis was performed"
    )
    context_depth: int = Field(
        ..., 
        description="Number of similar jobs analyzed",
        ge=0,
        le=10
    )
    market_intelligence: MarketIntelligenceData = Field(
        ..., 
        description="Market analysis based on similar job positions"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class IntelligentMatchingHealthResponse(BaseModel):
    """
    Health check response for intelligent matching service.
    """
    service: str = Field(
        ..., 
        description="Service name"
    )
    status: str = Field(
        ..., 
        description="Service status",
        regex="^(healthy|degraded|unhealthy)$"
    )
    timestamp: datetime = Field(
        ..., 
        description="Health check timestamp"
    )
    features: dict = Field(
        ..., 
        description="Available features and their status"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Error response schemas
class IntelligentMatchingError(BaseModel):
    """
    Error response for intelligent matching operations.
    """
    error: str = Field(
        ..., 
        description="Error message"
    )
    error_code: str = Field(
        ..., 
        description="Error code for programmatic handling"
    )
    job_id: Optional[UUID] = Field(
        None, 
        description="Job ID that caused the error, if applicable"
    )
    timestamp: datetime = Field(
        ..., 
        description="Error timestamp"
    )
    details: Optional[dict] = Field(
        None, 
        description="Additional error details"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
