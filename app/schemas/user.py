# app/schemas/user.py

from pydantic import BaseModel, EmailStr
from uuid import UUID


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: UUID
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str | None = None


class RefreshToken(BaseModel):
    refresh_token: str
    token_type: str = "bearer"
