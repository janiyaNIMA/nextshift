from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PublicRegisterRole(str, Enum):
    STUDENT = "student"
    EMPLOYER = "employer"


class UserRegisterRequest(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=255, description="Full name")]
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128, description="Password (min 8 chars)")]
    role: PublicRegisterRole = Field(
        default=PublicRegisterRole.STUDENT,
        description="Public registration role: 'student' or 'employer' only",
    )


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    is_approved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
