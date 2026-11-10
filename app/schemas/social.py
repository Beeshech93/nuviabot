from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class SocialAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    client_id: Optional[int] = None
    platform: str
    platform_account_id: str
    username: str
    display_name: Optional[str] = ""
    profile_picture_url: Optional[str] = ""
    status: str
    error_message: Optional[str] = ""
    followers_count: int
    following_count: int
    posts_count: int
    last_synced_at: Optional[datetime] = None
    created_at: datetime


class OAuthUrlResponse(BaseModel):
    platform: str
    auth_url: str
    state: str


class ConnectManualAccountRequest(BaseModel):
    """Allows securely registering verified official credentials or developer test accounts."""

    platform: str
    platform_account_id: str
    username: str
    display_name: Optional[str] = ""
    access_token: str
    refresh_token: Optional[str] = ""
    client_id: Optional[int] = None


class TestConnectionResponse(BaseModel):
    success: bool
    platform: str
    username: str
    status: str
    message: str
    account_info: Optional[Dict[str, Any]] = None
