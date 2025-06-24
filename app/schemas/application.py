from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date, datetime
import enum


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
    application_status: ApplicationStatus = ApplicationStatus.applied
    applied_date: date
    interview_date: Optional[date] = None
    offer_date: Optional[date] = None
    notes: Optional[str] = None


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
        orm_mode = True
