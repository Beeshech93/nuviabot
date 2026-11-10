from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_organization, get_current_user
from app.db.models import Organization, User
from app.db.session import get_db
from app.schemas.ai import (
    AICalendarIdeaRequest,
    AICalendarIdeaResponse,
    AIGenerateRequest,
    AIGenerateResponse,
    AIHashtagRequest,
    AIHashtagResponse,
    AIImproveRequest,
    AIImproveResponse,
    AITranslateRequest,
    AITranslateResponse,
)
from app.services.ai_service import ai_service
from app.services.billing_service import BillingService

router = APIRouter(prefix="/ai", tags=["AI Content Studio"])


@router.post("/generate", response_model=AIGenerateResponse)
async def generate_content(
    req: AIGenerateRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    # Enforce AI usage limits
    BillingService.check_can_use_ai_credits(db, org, credits=1)

    result = await ai_service.generate_content(req)

    # Increment usage
    org.ai_credits_used_this_month = (org.ai_credits_used_this_month or 0) + 1
    db.commit()

    plan = org.plan
    max_credits = plan.max_ai_credits if plan else 50
    result.credits_remaining = max(0, max_credits - org.ai_credits_used_this_month)
    return result


@router.post("/improve", response_model=AIImproveResponse)
async def improve_caption(
    req: AIImproveRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    BillingService.check_can_use_ai_credits(db, org, credits=1)
    result = await ai_service.improve_caption(
        original=req.original_caption,
        instruction=req.instruction,
        language=req.language or "es",
    )
    org.ai_credits_used_this_month = (org.ai_credits_used_this_month or 0) + 1
    db.commit()
    return result


@router.post("/hashtags", response_model=AIHashtagResponse)
async def generate_hashtags(
    req: AIHashtagRequest,
    current_user: User = Depends(get_current_user),
):
    return await ai_service.generate_hashtags(
        content=req.content,
        social_network=req.social_network,
        industry=req.industry or "General",
    )


@router.post("/translate", response_model=AITranslateResponse)
async def translate_content(
    req: AITranslateRequest,
    current_user: User = Depends(get_current_user),
):
    return await ai_service.translate_content(
        content=req.content,
        target_language=req.target_language,
    )


@router.post("/calendar-ideas", response_model=AICalendarIdeaResponse)
async def generate_calendar_ideas(
    req: AICalendarIdeaRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    BillingService.check_can_use_ai_credits(db, org, credits=2)
    result = await ai_service.generate_calendar_ideas(
        business_name=req.business_name,
        industry=req.industry,
        days=req.days,
        language=req.language,
    )
    org.ai_credits_used_this_month = (org.ai_credits_used_this_month or 0) + 2
    db.commit()
    return result

