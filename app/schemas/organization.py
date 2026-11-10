from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    industry: str
    logo_url: Optional[str] = ""
    timezone: str
    default_language: str
    subscription_status: str
    ai_credits_used_this_month: int
    posts_published_this_month: int
    auto_publish_enabled: bool
    plan_name: Optional[str] = "Free"
    created_at: datetime


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    logo_url: Optional[str] = None
    timezone: Optional[str] = None
    default_language: Optional[str] = None
    auto_publish_enabled: Optional[bool] = None


class ClientWorkspaceCreate(BaseModel):
    name: str
    industry: Optional[str] = "Marketing"
    logo_url: Optional[str] = ""
    notes: Optional[str] = ""


class ClientWorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    name: str
    industry: str
    logo_url: Optional[str] = ""
    notes: Optional[str] = ""
    is_active: bool
    created_at: datetime
