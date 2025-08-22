from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MatchScoreBase(BaseModel):
    application_id: UUID
    resume_id: UUID
    similarity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Similarity score between 0 and 1"
    )


class MatchScoreCreate(MatchScoreBase):
    pass


class MatchScoreUpdate(BaseModel):
    similarity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Similarity score between 0 and 1"
    )


class MatchScoreRead(MatchScoreBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MatchScoreResponse(BaseModel):
    application_id: UUID
    resume_id: UUID
    similarity_score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
