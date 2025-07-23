# app/schemas/job.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
import enum
import json

# Import skill analysis schemas
from app.schemas.skill_analysis import (
    SkillGapAnalysisResponse,
    SkillGapAnalysisRequest,
    ResumeSkillsResponse,
    JobSkillsResponse,
    SkillMatchSummary,
)


class JobStatus(str, enum.Enum):
    new = "new"
    saved = "saved"
    matched = "matched"
    applied = "applied"
    rejected = "rejected"


class JobBase(BaseModel):
    title: str
    description: str
    company: str
    location: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None  # e.g., "RemoteOK", "Indeed"
    date_posted: Optional[date] = None
    status: JobStatus = JobStatus.new
    match_score: Optional[float] = Field(None, ge=0.0, le=1.0)  # 0-1 similarity score
    job_embedding: Optional[List[float]] = None  # Vector embedding

    @field_validator("job_embedding", mode="before")
    @classmethod
    def validate_job_embedding(cls, v):
        """Convert Vector type from database to List[float] for API response."""
        if v is None:
            return None
        # If it's already a list, return as is
        if isinstance(v, list):
            return v
        # If it's a string (JSON), parse it
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        # If it's a Vector object from pgvector, convert to list
        if hasattr(v, "tolist"):
            return v.tolist()
        return v


class JobCreate(JobBase):
    # Required fields for creating a job
    title: str
    description: str
    company: str


class JobUpdate(BaseModel):
    # All fields optional for updates
    title: Optional[str] = None
    description: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    date_posted: Optional[date] = None
    status: Optional[JobStatus] = None
    match_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    job_embedding: Optional[List[float]] = None

    @field_validator("job_embedding", mode="before")
    @classmethod
    def validate_job_embedding(cls, v):
        """Convert Vector type from database to List[float] for API response."""
        if v is None:
            return None
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        if hasattr(v, "tolist"):
            return v.tolist()
        return v


class JobRead(JobBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # For Pydantic v2


class JobSearch(BaseModel):
    """Schema for job search parameters"""

    keyword: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None  # Filter by job board source
    status: Optional[JobStatus] = None  # Filter by user's job status


class JobSearchResult(BaseModel):
    """Schema for external job search results (from crawlers)"""

    title: str
    description: str
    company: str
    location: Optional[str] = None
    url: Optional[str] = None
    source: str
    date_posted: Optional[date] = None


class JobMatchRequest(BaseModel):
    """Schema for job matching request"""

    resume_id: UUID


class JobMatchResponse(BaseModel):
    """Schema for job matching response"""

    job_id: UUID
    resume_id: UUID
    similarity_score: float
    status: JobStatus


class JobApplyRequest(BaseModel):
    """Schema for job application request"""

    resume_id: UUID
    cover_letter_template: Optional[str] = "default"


class JobApplyResponse(BaseModel):
    """Schema for job application response"""

    job_id: UUID
    resume_id: UUID
    status: JobStatus
    applied_at: datetime


# Skill Gap Analysis related schemas
class JobSkillExtractionResponse(BaseModel):
    """Schema for job skill extraction response"""

    job_id: UUID
    skills_data: JobSkillsResponse
    extraction_timestamp: datetime


class ResumeSkillExtractionResponse(BaseModel):
    """Schema for resume skill extraction response"""

    resume_id: UUID
    skills_data: ResumeSkillsResponse
    extraction_timestamp: datetime
