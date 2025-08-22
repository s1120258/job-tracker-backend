# app/crud/user.py

from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import GoogleUserCreate, UserCreate


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email address."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_google_id(db: Session, google_id: str) -> Optional[User]:
    """Get user by Google ID."""
    return db.query(User).filter(User.google_id == google_id).first()


def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user with email/password authentication."""
    db_user = User(
        email=user.email,
        firstname=user.firstname,
        lastname=user.lastname,
        hashed_password=get_password_hash(user.password),
        provider="email",
        is_oauth=False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_google_user(db: Session, user_data: GoogleUserCreate) -> User:
    """Create a new user with Google OAuth authentication."""
    db_user = User(
        email=user_data.email,
        firstname=user_data.firstname,
        lastname=user_data.lastname,
        google_id=user_data.google_id,
        provider="google",
        is_oauth=True,
        hashed_password=None,  # No password for OAuth users
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_or_create_google_user(db: Session, google_user_data: dict) -> User:
    """
    Get existing Google user or create a new one.

    First checks by Google ID, then by email for account linking.
    """
    # First, try to find user by Google ID
    user = get_user_by_google_id(db, google_user_data["google_id"])
    if user:
        return user

    # Check if user exists with same email (for account linking)
    user = get_user_by_email(db, google_user_data["email"])
    if user:
        # Link existing account with Google
        user.google_id = google_user_data["google_id"]
        user.provider = "google"
        user.is_oauth = True
        db.commit()
        db.refresh(user)
        return user

    # Create new Google user
    google_user = GoogleUserCreate(**google_user_data)
    return create_google_user(db, google_user)
