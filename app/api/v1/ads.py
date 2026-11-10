from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_organization, get_current_user
from app.db.models import Organization, User
from app.db.session import get_db
from app.schemas.ads import AdAccountInfo, AdCampaignCreateRequest, AdCampaignResponse
from app.services.ads_service import ads_service

router = APIRouter(prefix="/ads", tags=["Facebook & TikTok Ads Manager"])


@router.get("/accounts", response_model=List[AdAccountInfo])
def get_ad_accounts(
    current_user: User = Depends(get_current_user),
):
    """Retrieve connected Meta Ads and TikTok for Business ad accounts."""
    return ads_service.get_ad_accounts()


@router.get("/campaigns", response_model=List[AdCampaignResponse])
def list_campaigns(
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """List all active and scheduled advertising campaigns across Meta and TikTok."""
    return ads_service.list_campaigns(db, org.id)


@router.post("/campaigns", response_model=AdCampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    req: AdCampaignCreateRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Create and launch a new Facebook Ads or TikTok Ads campaign."""
    return await ads_service.create_campaign(db, org.id, req)


@router.post("/campaigns/{campaign_id}/toggle", response_model=AdCampaignResponse)
def toggle_campaign_status(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Pause or resume an active ad campaign."""
    updated = ads_service.toggle_status(db, org.id, campaign_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    return updated

