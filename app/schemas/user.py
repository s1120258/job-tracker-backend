# app/schemas/user.py

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    firstname: str
    lastname: str
    password: str


class GoogleUserCreate(BaseModel):
    email: EmailStr
    firstname: str
    lastname: str
    google_id: str


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    firstname: str
    lastname: str
    provider: str
    is_oauth: bool
    google_id: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str | None = None


class RefreshToken(BaseModel):
    refresh_token: str
    token_type: str = "bearer"


# Google OAuth specific schemas
class GoogleTokenRequest(BaseModel):
    id_token: str


class GoogleAuthResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserRead
