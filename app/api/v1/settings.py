from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config import settings
from app.core.dependencies import get_current_organization, get_current_user, require_admin
from app.db.models import Organization, User
from app.db.session import get_db
from app.schemas.settings import SystemSettingsResponse, UpdateSystemSettingsRequest

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SystemSettingsResponse)
def get_system_settings(
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
):
    return SystemSettingsResponse(
        user_name=current_user.full_name,
        user_email=current_user.email,
        user_role=current_user.role,
        organization_name=org.name,
        organization_slug=org.slug,
        industry=org.industry,
        logo_url=org.logo_url or "",
        language=current_user.language or org.default_language or "es",
        timezone=current_user.timezone or org.timezone or "America/New_York",
        auto_publish_enabled=org.auto_publish_enabled or False,
        openai_configured=bool(settings.OPENAI_API_KEY),
        meta_configured=bool(settings.META_APP_ID and settings.META_APP_SECRET),
        tiktok_configured=bool(settings.TIKTOK_CLIENT_KEY and settings.TIKTOK_CLIENT_SECRET),
        youtube_configured=bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET),
        stripe_configured=bool(settings.STRIPE_SECRET_KEY),
    )


@router.put("", response_model=SystemSettingsResponse)
def update_system_settings(
    req: UpdateSystemSettingsRequest,
    current_user: User = Depends(require_admin),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    if req.user_name is not None:
        current_user.full_name = req.user_name

    if req.language is not None:
        current_user.language = req.language
        org.default_language = req.language

    if req.timezone is not None:
        current_user.timezone = req.timezone
        org.timezone = req.timezone

    if req.organization_name is not None:
        org.name = req.organization_name

    if req.industry is not None:
        org.industry = req.industry

    if req.logo_url is not None:
        org.logo_url = req.logo_url

    if req.auto_publish_enabled is not None:
        org.auto_publish_enabled = req.auto_publish_enabled

    db.commit()
    db.refresh(current_user)
    db.refresh(org)

    return get_system_settings(current_user=current_user, org=org)

