from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_organization, get_current_user
from app.db.models import Organization, User
from app.db.session import get_db
from app.schemas.ai import (
    AIBoostCampaignCalcRequest,
    AIBoostCampaignCalcResponse,
    AIBoostLaunchRequest,
    AIBoostLaunchResponse,
    AIBoostPostRequest,
    AIBoostPostResponse,
    AIBoostUrlRequest,
    AIBoostUrlResponse,
    AICalendarIdeaRequest,
    AICalendarIdeaResponse,
    AIChatRequest,
    AIChatResponse,
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


@router.post("/chat", response_model=AIChatResponse)
async def chat_assistant(
    req: AIChatRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Conversational AI Growth Consultant for social media strategy and execution."""
    BillingService.check_can_use_ai_credits(db, org, credits=1)
    result = await ai_service.chat_assistant(
        message=req.message,
        language=req.language or current_user.language or org.default_language or "es",
        context=req.context,
    )
    org.ai_credits_used_this_month = (org.ai_credits_used_this_month or 0) + 1
    db.commit()
    return result


@router.post("/boost/optimize-post", response_model=AIBoostPostResponse)
async def boost_post_content(
    req: AIBoostPostRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Supercharge post captions with viral 3-second hooks, follower CTAs, and peak reach hashtags."""
    BillingService.check_can_use_ai_credits(db, org, credits=1)
    result = await ai_service.boost_post(req)
    org.ai_credits_used_this_month = (org.ai_credits_used_this_month or 0) + 1
    db.commit()
    return result


@router.post("/boost/campaign-calc", response_model=AIBoostCampaignCalcResponse)
def calculate_boost_campaign(
    req: AIBoostCampaignCalcRequest,
    current_user: User = Depends(get_current_user),
):
    """Calculate projected views, reach, profile visits, and new followers based on budget."""
    return ai_service.calculate_boost_campaign(req)


@router.post("/boost/launch", response_model=AIBoostLaunchResponse)
async def launch_boost_campaign(
    req: AIBoostLaunchRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Launch or schedule an official boost campaign targeting followers and views."""
    return await ai_service.launch_boost_campaign(req, org_id=org.id)


@router.post("/boost/by-url", response_model=AIBoostUrlResponse)
def boost_by_url(
    req: AIBoostUrlRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyze and generate viral growth and boost strategy directly from a Page or Post URL."""
    return ai_service.boost_by_url(req)

