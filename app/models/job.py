# app/models/job.py

from sqlalchemy import Column, String, Date, Enum, Text, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
import enum
import uuid
from datetime import datetime, timezone
from app.db.base_class import Base


class JobStatus(enum.Enum):
    new = "new"
    saved = "saved"
    matched = "matched"
    applied = "applied"
    rejected = "rejected"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=True)
    url = Column(String, nullable=True)
    source = Column(String, nullable=True)  # e.g., "RemoteOK", "Indeed"
    date_posted = Column(Date, nullable=True)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.new)
    match_score = Column(Float, nullable=True)  # 0-1 similarity score
    job_embedding = Column(Vector(1536), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", back_populates="jobs")
    match_scores = relationship("MatchScore", back_populates="job")