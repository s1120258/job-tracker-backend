# app/schemas/application.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
import enum
import json


class ApplicationStatus(str, enum.Enum):
    applied = "applied"
    interviewing = "interviewing"
    rejected = "rejected"
    offer = "offer"
    accepted = "accepted"


class ApplicationBase(BaseModel):
    company_name: str
    position_title: str
    job_description_text: str
    job_embedding: Optional[List[float]] = None  # Vector embedding
    application_status: ApplicationStatus = ApplicationStatus.applied
    applied_date: date
    interview_date: Optional[date] = None
    offer_date: Optional[date] = None
    notes: Optional[str] = None

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


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(ApplicationBase):
    pass


class ApplicationRead(ApplicationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # For Pydantic v2
