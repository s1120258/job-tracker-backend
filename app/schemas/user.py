# app/schemas/user.py

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
