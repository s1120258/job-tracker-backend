from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from uuid import UUID
from enum import Enum


class SkillLevel(str, Enum):
    """Enumeration for skill proficiency levels."""

    entry = "Entry"
    intermediate = "Intermediate"
    advanced = "Advanced"
    senior = "Senior"
    any = "Any"
    none = "None"
    beginner = "Beginner"


class SkillCategory(str, Enum):
    """Enumeration for skill categories."""

    programming_language = "programming_language"
    framework = "framework"
    tool = "tool"
    cloud_platform = "cloud_platform"
    database = "database"
    soft_skill = "soft_skill"
    domain = "domain"
    certification = "certification"
    other = "other"


class Priority(str, Enum):
    """Enumeration for priority levels."""

    high = "High"
    medium = "Medium"
    low = "Low"


class Importance(str, Enum):
    """Enumeration for skill importance levels."""

    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class GapSeverity(str, Enum):
    """Enumeration for skill gap severity."""

    major = "Major"
    minor = "Minor"
    none = "None"


class TechnicalSkill(BaseModel):
    """Schema for technical skills with detailed information."""

    name: str = Field(..., description="Name of the technical skill")
    level: SkillLevel = Field(..., description="Proficiency level of the skill")
    years_experience: int = Field(
        0, ge=0, description="Years of experience with this skill"
    )
    evidence: Optional[str] = Field(
        None, description="Evidence from resume text supporting this skill"
    )


class SkillRequirement(BaseModel):
    """Schema for job skill requirements."""

    name: str = Field(..., description="Name of the required skill")
    level: SkillLevel = Field(..., description="Required proficiency level")
    category: SkillCategory = Field(..., description="Category of the skill")
    importance: Importance = Field(
        ..., description="Importance level of this skill for the job"
    )


class SkillStrength(BaseModel):
    """Schema for candidate's skill strengths."""

    skill: str = Field(..., description="Name of the skill")
    reason: str = Field(..., description="Reason why this is considered a strength")


class SkillGap(BaseModel):
    """Schema for identified skill gaps."""

    skill: str = Field(..., description="Name of the skill with a gap")
    required_level: SkillLevel = Field(..., description="Required proficiency level")
    current_level: SkillLevel = Field(
        ..., description="Current proficiency level of candidate"
    )
    priority: Priority = Field(
        ..., description="Priority level for addressing this gap"
    )
    impact: str = Field(..., description="Impact description of this skill gap")
    gap_severity: GapSeverity = Field(..., description="Severity of the skill gap")


class LearningRecommendation(BaseModel):
    """Schema for learning recommendations."""

    skill: str = Field(..., description="Name of the skill to learn")
    priority: Priority = Field(..., description="Learning priority")
    estimated_learning_time: str = Field(
        ..., description="Estimated time to acquire the skill"
    )
    suggested_approach: str = Field(..., description="Recommended learning approach")
    resources: List[str] = Field(
        default_factory=list, description="Recommended learning resources"
    )
    immediate_actions: List[str] = Field(
        default_factory=list, description="Immediate steps to take"
    )


class ExperienceGap(BaseModel):
    """Schema for experience gap analysis."""

    required_years: int = Field(..., ge=0, description="Required years of experience")
    candidate_years: int = Field(
        ..., ge=0, description="Candidate's years of experience"
    )
    gap: int = Field(..., description="Experience gap in years")
    assessment: str = Field(..., description="Assessment of experience gap")


class EducationMatch(BaseModel):
    """Schema for education requirement matching."""

    required: str = Field(..., description="Required education")
    candidate: str = Field(..., description="Candidate's education")
    matches: bool = Field(..., description="Whether education requirement is met")
    assessment: str = Field(..., description="Assessment of education match")


class ResumeSkillsResponse(BaseModel):
    """Schema for resume skill extraction response."""

    technical_skills: List[TechnicalSkill] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    total_experience_years: int = Field(0, ge=0)


class JobSkillsResponse(BaseModel):
    """Schema for job skill extraction response."""

    required_skills: List[SkillRequirement] = Field(default_factory=list)
    preferred_skills: List[SkillRequirement] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    cloud_platforms: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    experience_required: str = Field("", description="Required experience description")
    education_required: str = Field("", description="Required education description")
    seniority_level: str = Field("", description="Required seniority level")


class SkillGapAnalysisResponse(BaseModel):
    """Schema for comprehensive skill gap analysis response."""

    job_id: UUID = Field(..., description="ID of the job being analyzed")
    resume_id: UUID = Field(..., description="ID of the resume being analyzed")
    overall_match_percentage: float = Field(
        ..., ge=0, le=100, description="Overall match percentage"
    )
    match_summary: str = Field(..., description="Summary of the skill match")
    strengths: List[SkillStrength] = Field(
        default_factory=list, description="Candidate's skill strengths"
    )
    skill_gaps: List[SkillGap] = Field(
        default_factory=list, description="Identified skill gaps"
    )
    learning_recommendations: List[LearningRecommendation] = Field(
        default_factory=list, description="Recommended learning paths"
    )
    experience_gap: Optional[ExperienceGap] = Field(
        None, description="Experience gap analysis"
    )
    education_match: Optional[EducationMatch] = Field(
        None, description="Education requirement match"
    )
    recommended_next_steps: List[str] = Field(
        default_factory=list, description="Recommended next steps"
    )
    application_advice: str = Field("", description="Advice for job application")
    analysis_timestamp: Optional[str] = Field(None, description="Timestamp of analysis")


class SkillGapAnalysisRequest(BaseModel):
    """Schema for skill gap analysis request."""

    resume_id: Optional[UUID] = Field(
        None, description="Specific resume ID to use (optional)"
    )
    include_learning_recommendations: bool = Field(
        True, description="Whether to include learning recommendations"
    )
    include_experience_analysis: bool = Field(
        True, description="Whether to include experience gap analysis"
    )
    include_education_analysis: bool = Field(
        True, description="Whether to include education matching"
    )


class SkillExtractionRequest(BaseModel):
    """Schema for skill extraction request."""

    text: str = Field(..., min_length=1, description="Text to extract skills from")
    context: str = Field(
        "resume", description="Context of the text (resume, job_description)"
    )

    @field_validator("context")
    @classmethod
    def validate_context(cls, v):
        """Validate context is either resume or job_description."""
        if v not in ["resume", "job_description"]:
            raise ValueError("Context must be either 'resume' or 'job_description'")
        return v


# Error response schemas
class SkillAnalysisError(BaseModel):
    """Schema for skill analysis error responses."""

    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )


# Summary schemas for quick overview
class SkillMatchSummary(BaseModel):
    """Schema for quick skill match summary."""

    job_id: UUID
    resume_id: UUID
    match_percentage: float = Field(..., ge=0, le=100)
    critical_gaps_count: int = Field(..., ge=0)
    strengths_count: int = Field(..., ge=0)
    total_required_skills: int = Field(..., ge=0)
    last_analyzed: Optional[str] = Field(None)
