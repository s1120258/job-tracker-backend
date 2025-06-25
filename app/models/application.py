# app/models/application.py

from sqlalchemy import Column, String, Date, Enum, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
import uuid
from datetime import datetime, timezone
from app.db.base_class import Base


class ApplicationStatus(enum.Enum):
    applied = "applied"
    interviewing = "interviewing"
    rejected = "rejected"
    offer = "offer"
    accepted = "accepted"


class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    company_name = Column(String, nullable=False)
    position_title = Column(String, nullable=False)
    job_description_text = Column(Text, nullable=False)
    job_embedding = Column(String, nullable=True)  # Placeholder for vector
    application_status = Column(
        Enum(ApplicationStatus), nullable=False, default=ApplicationStatus.applied
    )
    applied_date = Column(Date, nullable=False)
    interview_date = Column(Date, nullable=True)
    offer_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="applications")
