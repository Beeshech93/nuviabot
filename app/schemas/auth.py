from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    type: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    organization_name: str
    full_name: str
    email: str
    password: str
    industry: Optional[str] = "Digital Marketing"
    language: Optional[str] = "es"
    timezone: Optional[str] = "America/New_York"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    language: str
    timezone: str
    avatar_url: Optional[str] = ""
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    avatar_url: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
