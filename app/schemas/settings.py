from typing import Optional
from pydantic import BaseModel, ConfigDict


class SystemSettingsResponse(BaseModel):
    user_name: str
    user_email: str
    user_role: str
    organization_name: str
    organization_slug: str
    industry: str
    logo_url: Optional[str] = ""
    language: str  # es, en, ht
    timezone: str
    auto_publish_enabled: bool
    openai_configured: bool
    meta_configured: bool
    tiktok_configured: bool
    youtube_configured: bool
    stripe_configured: bool


class UpdateSystemSettingsRequest(BaseModel):
    user_name: Optional[str] = None
    organization_name: Optional[str] = None
    industry: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    auto_publish_enabled: Optional[bool] = None
    logo_url: Optional[str] = None


class TeamMemberInviteRequest(BaseModel):
    email: str
    full_name: str
    role: str  # agency_admin, client_admin, editor, viewer


class TeamMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: str
