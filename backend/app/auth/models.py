from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=120)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class User(BaseModel):
    id: str
    email: str
    full_name: str = Field(..., min_length=1, max_length=120)
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=1)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool = False


class TokenPayload(BaseModel):
    sub: str
    exp: int | None = None