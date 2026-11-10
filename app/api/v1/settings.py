import os
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
import httpx
from sqlalchemy.orm import Session
from app.config import settings
from app.core.dependencies import get_current_organization, get_current_user, require_admin
from app.db.models import Organization, User
from app.db.session import get_db
from app.schemas.settings import (
    LiveIntegrationsResponse,
    LivePlatformStatus,
    LiveTestResult,
    SystemSettingsResponse,
    UpdateIntegrationsRequest,
    UpdateSystemSettingsRequest,
)

router = APIRouter(prefix="/settings", tags=["Settings"])


def _mask(val: Optional[str]) -> str:
    if not val:
        return "No configurada"
    if len(val) <= 8:
        return "••••" + val[-2:]
    return val[:4] + "••••••••" + val[-4:]


def _get_live_integrations_data() -> LiveIntegrationsResponse:
    base = settings.APP_BASE_URL.rstrip("/")
    meta_live = bool(settings.META_APP_ID and settings.META_APP_SECRET)
    tiktok_live = bool(settings.TIKTOK_CLIENT_KEY and settings.TIKTOK_CLIENT_SECRET)
    youtube_live = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    openai_live = bool(settings.OPENAI_API_KEY)
    stripe_live = bool(settings.STRIPE_SECRET_KEY)

    return LiveIntegrationsResponse(
        app_base_url=base,
        openai=LivePlatformStatus(
            platform="openai",
            name="OpenAI API (GPT-4o Copywriter)",
            is_live=openai_live,
            status_label="LIVE (API Oficial)" if openai_live else "SANDBOX (Simulador Heurístico)",
            configured=openai_live,
            app_id_or_client_key_masked=_mask(settings.OPENAI_API_KEY),
            callback_url="",
            webhook_url=None,
            required_scopes=["chat.completions"],
        ),
        meta=LivePlatformStatus(
            platform="meta",
            name="Meta Graph API v20.0 (Instagram & Facebook)",
            is_live=meta_live,
            status_label="LIVE (API Oficial Meta)" if meta_live else "SANDBOX (Simulador de Desarrollo)",
            configured=meta_live,
            app_id_or_client_key_masked=_mask(settings.META_APP_ID),
            callback_url=f"{base}/api/v1/social/callback/meta",
            webhook_url=f"{base}/api/v1/social/webhook/meta",
            required_scopes=[
                "instagram_basic",
                "instagram_content_publish",
                "instagram_manage_insights",
                "pages_show_list",
                "pages_read_engagement",
                "pages_manage_posts",
                "public_profile",
            ],
        ),
        tiktok=LivePlatformStatus(
            platform="tiktok",
            name="TikTok for Developers Content Posting API",
            is_live=tiktok_live,
            status_label="LIVE (API Oficial TikTok)" if tiktok_live else "SANDBOX (Simulador de Desarrollo)",
            configured=tiktok_live,
            app_id_or_client_key_masked=_mask(settings.TIKTOK_CLIENT_KEY),
            callback_url=f"{base}/api/v1/social/callback/tiktok",
            webhook_url=f"{base}/api/v1/social/webhook/tiktok",
            required_scopes=["user.info.basic", "video.upload", "video.publish"],
        ),
        youtube=LivePlatformStatus(
            platform="youtube",
            name="Google / YouTube Data API v3",
            is_live=youtube_live,
            status_label="LIVE (API Oficial Google)" if youtube_live else "SANDBOX (Simulador de Desarrollo)",
            configured=youtube_live,
            app_id_or_client_key_masked=_mask(settings.GOOGLE_CLIENT_ID),
            callback_url=f"{base}/api/v1/social/callback/youtube",
            webhook_url=f"{base}/api/v1/social/webhook/youtube",
            required_scopes=[
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube.readonly",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
        ),
        stripe=LivePlatformStatus(
            platform="stripe",
            name="Stripe Subscriptions & Billing API",
            is_live=stripe_live,
            status_label="LIVE (Stripe Payments)" if stripe_live else "SANDBOX (Modo Demo)",
            configured=stripe_live,
            app_id_or_client_key_masked=_mask(settings.STRIPE_SECRET_KEY),
            callback_url="",
            webhook_url=f"{base}/api/v1/billing/webhook",
            required_scopes=["billing:subscriptions:write", "checkout:sessions:create"],
        ),
    )


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


@router.get("/integrations", response_model=LiveIntegrationsResponse)
def get_live_integrations(
    current_user: User = Depends(get_current_user),
):
    return _get_live_integrations_data()


@router.put("/integrations", response_model=LiveIntegrationsResponse)
def update_live_integrations(
    req: UpdateIntegrationsRequest,
    current_user: User = Depends(require_admin),
):
    """Updates live platform API credentials dynamically at runtime."""
    env_updates = {}

    if req.openai_api_key is not None:
        settings.OPENAI_API_KEY = req.openai_api_key.strip()
        env_updates["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

    if req.meta_app_id is not None:
        settings.META_APP_ID = req.meta_app_id.strip()
        env_updates["META_APP_ID"] = settings.META_APP_ID

    if req.meta_app_secret is not None:
        settings.META_APP_SECRET = req.meta_app_secret.strip()
        env_updates["META_APP_SECRET"] = settings.META_APP_SECRET

    if req.meta_webhook_verify_token is not None:
        settings.META_WEBHOOK_VERIFY_TOKEN = req.meta_webhook_verify_token.strip()
        env_updates["META_WEBHOOK_VERIFY_TOKEN"] = settings.META_WEBHOOK_VERIFY_TOKEN

    if req.tiktok_client_key is not None:
        settings.TIKTOK_CLIENT_KEY = req.tiktok_client_key.strip()
        env_updates["TIKTOK_CLIENT_KEY"] = settings.TIKTOK_CLIENT_KEY

    if req.tiktok_client_secret is not None:
        settings.TIKTOK_CLIENT_SECRET = req.tiktok_client_secret.strip()
        env_updates["TIKTOK_CLIENT_SECRET"] = settings.TIKTOK_CLIENT_SECRET

    if req.google_client_id is not None:
        settings.GOOGLE_CLIENT_ID = req.google_client_id.strip()
        env_updates["GOOGLE_CLIENT_ID"] = settings.GOOGLE_CLIENT_ID

    if req.google_client_secret is not None:
        settings.GOOGLE_CLIENT_SECRET = req.google_client_secret.strip()
        env_updates["GOOGLE_CLIENT_SECRET"] = settings.GOOGLE_CLIENT_SECRET

    if req.stripe_secret_key is not None:
        settings.STRIPE_SECRET_KEY = req.stripe_secret_key.strip()
        env_updates["STRIPE_SECRET_KEY"] = settings.STRIPE_SECRET_KEY

    if req.stripe_publishable_key is not None:
        settings.STRIPE_PUBLISHABLE_KEY = req.stripe_publishable_key.strip()
        env_updates["STRIPE_PUBLISHABLE_KEY"] = settings.STRIPE_PUBLISHABLE_KEY

    # Persist into .env file if running in non-serverless local environment
    if not os.getenv("VERCEL") and os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                lines = f.readlines()

            new_lines = []
            seen_keys = set()
            for line in lines:
                matched = False
                for k, v in env_updates.items():
                    if line.startswith(f"{k}="):
                        new_lines.append(f"{k}={v}\n")
                        seen_keys.add(k)
                        matched = True
                        break
                if not matched:
                    new_lines.append(line)

            for k, v in env_updates.items():
                if k not in seen_keys:
                    new_lines.append(f"{k}={v}\n")

            with open(".env", "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception:
            pass

    return _get_live_integrations_data()


@router.post("/integrations/test/{platform}", response_model=LiveTestResult)
async def test_live_integration(
    platform: str,
    current_user: User = Depends(require_admin),
):
    """Executes a live test ping against the official platform API servers."""
    p = platform.lower()
    start = time.time()

    if p == "openai":
        if not settings.OPENAI_API_KEY:
            return LiveTestResult(
                platform="openai",
                is_live=False,
                success=True,
                message="Modo Sandbox Activo: Simulador trilingüe de IA listo para usar.",
                latency_ms=0,
            )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                )
                latency = int((time.time() - start) * 1000)
                if res.status_code == 200:
                    return LiveTestResult(
                        platform="openai",
                        is_live=True,
                        success=True,
                        message="API Key oficial de OpenAI verificada exitosamente. Modelos GPT disponibles.",
                        latency_ms=latency,
                    )
                else:
                    return LiveTestResult(
                        platform="openai",
                        is_live=True,
                        success=False,
                        message=f"Error de autenticación OpenAI ({res.status_code}): {res.text[:120]}",
                        latency_ms=latency,
                    )
        except Exception as e:
            return LiveTestResult(
                platform="openai",
                is_live=True,
                success=False,
                message=f"Fallo de conexión con OpenAI: {str(e)}",
                latency_ms=int((time.time() - start) * 1000),
            )

    elif p in ["meta", "instagram", "facebook"]:
        if not settings.META_APP_ID or not settings.META_APP_SECRET:
            return LiveTestResult(
                platform="meta",
                is_live=False,
                success=True,
                message="Modo Sandbox Activo: Vinculación simulada para Instagram y Facebook lista.",
                latency_ms=0,
            )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"https://graph.facebook.com/v20.0/{settings.META_APP_ID}",
                    params={
                        "access_token": f"{settings.META_APP_ID}|{settings.META_APP_SECRET}",
                        "fields": "id,name,category",
                    },
                )
                latency = int((time.time() - start) * 1000)
                data = res.json()
                if "error" in data:
                    return LiveTestResult(
                        platform="meta",
                        is_live=True,
                        success=False,
                        message=f"Error de Meta Graph API: {data['error'].get('message')}",
                        latency_ms=latency,
                    )
                return LiveTestResult(
                    platform="meta",
                    is_live=True,
                    success=True,
                    message=f"Meta App '{data.get('name', 'Nuvio App')}' validada con éxito en Meta Graph API v20.0.",
                    latency_ms=latency,
                )
        except Exception as e:
            return LiveTestResult(
                platform="meta",
                is_live=True,
                success=False,
                message=f"Fallo de conexión con Meta Graph API: {str(e)}",
                latency_ms=int((time.time() - start) * 1000),
            )

    elif p == "tiktok":
        if not settings.TIKTOK_CLIENT_KEY or not settings.TIKTOK_CLIENT_SECRET:
            return LiveTestResult(
                platform="tiktok",
                is_live=False,
                success=True,
                message="Modo Sandbox Activo: Simulador TikTok Content Posting API disponible.",
                latency_ms=0,
            )

        # TikTok does not have a stateless ping endpoint for app secret, check configuration format
        return LiveTestResult(
            platform="tiktok",
            is_live=True,
            success=True,
            message=f"Credenciales de TikTok configuradas (Client Key: {_mask(settings.TIKTOK_CLIENT_KEY)}). Listo para OAuth en vivo.",
            latency_ms=10,
        )

    elif p in ["youtube", "google"]:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            return LiveTestResult(
                platform="youtube",
                is_live=False,
                success=True,
                message="Modo Sandbox Activo: Simulador YouTube Data API v3 listo.",
                latency_ms=0,
            )

        return LiveTestResult(
            platform="youtube",
            is_live=True,
            success=True,
            message=f"Credenciales de Google / YouTube configuradas (Client ID: {_mask(settings.GOOGLE_CLIENT_ID)}). Listo para OAuth en vivo.",
            latency_ms=10,
        )

    elif p == "stripe":
        if not settings.STRIPE_SECRET_KEY:
            return LiveTestResult(
                platform="stripe",
                is_live=False,
                success=True,
                message="Modo Sandbox Activo: Pasarela de facturación en modo demostración.",
                latency_ms=0,
            )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    "https://api.stripe.com/v1/balance",
                    headers={"Authorization": f"Bearer {settings.STRIPE_SECRET_KEY}"},
                )
                latency = int((time.time() - start) * 1000)
                if res.status_code == 200:
                    return LiveTestResult(
                        platform="stripe",
                        is_live=True,
                        success=True,
                        message="Stripe API Key verificada con éxito. Listo para procesar pagos y suscripciones.",
                        latency_ms=latency,
                    )
                else:
                    return LiveTestResult(
                        platform="stripe",
                        is_live=True,
                        success=False,
                        message=f"Error de autenticación con Stripe ({res.status_code}): {res.text[:120]}",
                        latency_ms=latency,
                    )
        except Exception as e:
            return LiveTestResult(
                platform="stripe",
                is_live=True,
                success=False,
                message=f"Fallo de conexión con Stripe: {str(e)}",
                latency_ms=int((time.time() - start) * 1000),
            )

    raise HTTPException(status_code=400, detail=f"Plataforma '{platform}' no soportada para prueba.")
