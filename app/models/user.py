# app/models/user.py

from sqlalchemy import Column, Integer, String
from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)  # changed
    hashed_password = Column(String, nullable=False)
