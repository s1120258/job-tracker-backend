# app/models/user.py

import uuid

from sqlalchemy import Boolean, Column, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)  # changed
    firstname = Column(String, nullable=False, server_default=text("'Unknown'"))
    lastname = Column(String, nullable=False, server_default=text("'User'"))
    hashed_password = Column(String, nullable=True)  # Now nullable for OAuth users

    # OAuth fields
    google_id = Column(String, unique=True, nullable=True, index=True)  # Google user ID
    provider = Column(
        String, nullable=False, server_default=text("'email'")
    )  # Auth provider: 'email', 'google'
    is_oauth = Column(
        Boolean, nullable=False, server_default=text("false")
    )  # OAuth authentication flag

    jobs = relationship("Job", back_populates="user")
    resumes = relationship("Resume", back_populates="user")
