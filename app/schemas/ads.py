from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AdCampaignCreateRequest(BaseModel):
    platform: str = "facebook"  # "facebook" or "tiktok"
    name: str = "Campaña de Crecimiento Oficial"
    objective: str = "followers"  # "followers", "views", "leads"
    target_url: str = "https://www.facebook.com/lajanrapid"
    account_username: str = "lajanrapid"
    budget_usd: float = Field(default=10.0, ge=1.0, le=5000.0)
    duration_days: int = Field(default=5, ge=1, le=30)
    target_countries: str = "Global"
    target_interests: str = "Negocios, Finanzas, Comercio, Inversión"
    ad_headline: Optional[str] = "Página Oficial Lajan Rapid"
    ad_text: Optional[str] = "Descubre consejos exclusivos, finanzas inteligentes y oportunidades de negocio todos los días."
    call_to_action: Optional[str] = "SEGUIR_PAGINA"


class AdCampaignResponse(BaseModel):
    id: int
    campaign_uid: str
    platform: str
    name: str
    objective: str
    status: str
    budget_usd: float
    daily_budget_usd: float
    duration_days: int
    spend_usd: float
    target_url: str
    account_username: str
    target_countries: str
    target_interests: str
    ad_headline: str
    ad_text: str
    call_to_action: str
    impressions: int
    clicks: int
    video_views: int
    new_followers: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class AdAccountInfo(BaseModel):
    platform: str
    ad_account_id: str
    name: str
    currency: str
    status: str
    balance_usd: float
    is_live: bool
