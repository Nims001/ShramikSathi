"""Pydantic schemas for auth (register / login / me)."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    """Public user profile — includes identity demographics used by the form."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    role: str = "worker"
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    ethnicity: Optional[str] = None
    education_level: Optional[str] = None
    language: str = "en"
    created_at: datetime


class RegisterRequest(BaseModel):
    """Signup: credentials + identity & demographics (age is calculated, not asked)."""

    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="worker", pattern="^(worker|employer)$")
    gender: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[date] = None
    ethnicity: Optional[str] = Field(default=None, max_length=80)
    education_level: Optional[str] = Field(default=None, max_length=60)
    language: str = "en"


class LoginRequest(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    """Profile edits. Age is recalculated server-side from the date of birth."""

    gender: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[date] = None
    ethnicity: Optional[str] = Field(default=None, max_length=80)
    education_level: Optional[str] = Field(default=None, max_length=60)
    language: Optional[str] = Field(default=None, max_length=10)


class AuthResponse(BaseModel):
    token: str
    user: UserOut
