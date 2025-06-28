import uuid
from sqlalchemy import Column, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base_class import Base


class MatchScore(Base):
    __tablename__ = "match_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, unique=True
    )
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    similarity_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    application = relationship("Application", back_populates="match_score")
    resume = relationship("Resume", back_populates="match_scores")
