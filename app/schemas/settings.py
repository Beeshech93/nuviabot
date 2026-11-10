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


class LivePlatformStatus(BaseModel):
    platform: str
    name: str
    is_live: bool
    status_label: str  # "LIVE (API Oficial)" or "SANDBOX (Simulador)"
    configured: bool
    app_id_or_client_key_masked: str
    callback_url: str
    webhook_url: Optional[str] = None
    required_scopes: list[str]


class LiveIntegrationsResponse(BaseModel):
    app_base_url: str
    openai: LivePlatformStatus
    meta: LivePlatformStatus
    tiktok: LivePlatformStatus
    youtube: LivePlatformStatus
    stripe: LivePlatformStatus


class UpdateIntegrationsRequest(BaseModel):
    openai_api_key: Optional[str] = None
    meta_app_id: Optional[str] = None
    meta_app_secret: Optional[str] = None
    meta_webhook_verify_token: Optional[str] = None
    tiktok_client_key: Optional[str] = None
    tiktok_client_secret: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None


class LiveTestResult(BaseModel):
    platform: str
    is_live: bool
    success: bool
    message: str
    latency_ms: Optional[int] = 0


class AuditLogItemResponse(BaseModel):
    id: int
    user_name: Optional[str] = "Sistema"
    action: str
    resource_type: str
    resource_id: Optional[str] = ""
    ip_address: Optional[str] = ""
    details: dict = {}
    created_at: str


class AuditLogListResponse(BaseModel):
    total: int
    items: list[AuditLogItemResponse]

