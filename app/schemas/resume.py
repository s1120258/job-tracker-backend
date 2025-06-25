# app/schemas/resume.py

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class ResumeCreate(BaseModel):
    file_name: str
    extracted_text: Optional[str] = None


class ResumeRead(BaseModel):
    id: UUID
    file_name: str
    upload_date: datetime
    extracted_text: Optional[str] = None

    class Config:
        from_attributes = True  # For Pydantic v2
