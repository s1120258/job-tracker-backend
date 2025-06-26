# app/schemas/resume.py

from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Union
import json


class ResumeBase(BaseModel):
    file_name: str
    extracted_text: Optional[str] = None
    embedding: Optional[List[float]] = None

    @field_validator("embedding", mode="before")
    @classmethod
    def validate_embedding(cls, v):
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


class ResumeCreate(ResumeBase):
    pass


class ResumeUpdate(ResumeBase):
    pass


class ResumeRead(ResumeBase):
    id: UUID
    user_id: UUID
    upload_date: datetime

    class Config:
        from_attributes = True  # For Pydantic v2
