from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from app.config import settings
from app.db.models import AuditLog, SocialAccount
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/social/webhook", tags=["Social Webhooks"])


@router.get("/meta")
async def verify_meta_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
):
    """Meta (Instagram & Facebook) Webhook subscription verification challenge."""
    if hub_mode == "subscribe" and hub_verify_token == settings.META_WEBHOOK_VERIFY_TOKEN:
        logger.info("Meta webhook successfully verified with challenge.")
        return Response(content=str(hub_challenge), media_type="text/plain", status_code=200)

    logger.warning("Meta webhook verification failed: invalid verify token or mode.")
    raise HTTPException(status_code=403, detail="Verification token mismatch.")


@router.post("/meta")
async def handle_meta_webhook(request: Request):
    """Handles incoming real-time notifications from Meta (Instagram & Facebook Graph API)."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    logger.info("Meta Webhook Received: %s", json.dumps(payload)[:300])

    obj_type = payload.get("object")
    entries = payload.get("entry", [])

    db = SessionLocal()
    try:
        for entry in entries:
            platform_id = str(entry.get("id"))
            # Find associated social account in database
            account = (
                db.query(SocialAccount)
                .filter(SocialAccount.platform_account_id == platform_id)
                .first()
            )
            if account:
                account.last_synced_at = datetime.now(timezone.utc)
                # Audit the event
                audit = AuditLog(
                    organization_id=account.organization_id,
                    user_id=1,
                    action="meta_webhook_event",
                    entity_type="social_account",
                    entity_id=account.id,
                    details=json.dumps({"object": obj_type, "time": entry.get("time")}),
                )
                db.add(audit)
        db.commit()
    except Exception as e:
        logger.error("Error processing Meta webhook event: %s", e)
    finally:
        db.close()

    return {"status": "success", "received": True}


@router.post("/tiktok")
async def handle_tiktok_webhook(request: Request):
    """Handles incoming TikTok developer notifications (publish status, creator stats updates)."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    logger.info("TikTok Webhook Received: %s", json.dumps(payload)[:300])
    return {"status": "success", "received": True}


@router.get("/youtube")
async def verify_youtube_pubsubhubbub(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """Handles Google PubSubHubbub subscription verification for YouTube channels."""
    if hub_challenge:
        return Response(content=str(hub_challenge), media_type="text/plain", status_code=200)
    return {"status": "active"}


@router.post("/youtube")
async def handle_youtube_notification(request: Request):
    """Handles real-time YouTube XML/Atom push notifications."""
    body = await request.body()
    logger.info("YouTube Webhook Received: %d bytes", len(body))
    return {"status": "success", "received": True}
