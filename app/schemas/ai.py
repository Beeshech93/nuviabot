from typing import List, Optional
from pydantic import BaseModel, Field


class AIProposal(BaseModel):
    title: str = ""
    caption: str
    hashtags: List[str] = []
    call_to_action: str = ""
    tone: str = ""
    target_platform: str = ""


class AIGenerateRequest(BaseModel):
    business_name: str
    industry: str
    product_service: str
    target_audience: str
    social_network: str  # instagram, facebook, tiktok, youtube, all
    language: str = "es"  # es, en, ht
    tone: str = "professional"  # professional, conversational, energetic, inspirational, humorous, urgent
    objective: str = "brand_awareness"  # sales, brand_awareness, lead_generation, engagement, community
    additional_notes: Optional[str] = ""
    variations_count: int = Field(default=3, ge=1, le=5)


class AIGenerateResponse(BaseModel):
    proposals: List[AIProposal]
    language: str
    model_used: str
    credits_remaining: Optional[int] = None


class AIImproveRequest(BaseModel):
    original_caption: str
    instruction: str  # "make it more engaging", "add emojis", "shorter for twitter/tiktok", "stronger call to action"
    social_network: Optional[str] = "instagram"
    language: Optional[str] = "es"


class AIImproveResponse(BaseModel):
    improved_caption: str
    hashtags: List[str] = []
    explanation: str = ""


class AIHashtagRequest(BaseModel):
    content: str
    social_network: str = "instagram"
    industry: Optional[str] = "General"
    count: int = Field(default=15, ge=5, le=30)


class AIHashtagResponse(BaseModel):
    hashtags: List[str]
    categories: dict = {}


class AITranslateRequest(BaseModel):
    content: str
    source_language: str = "auto"
    target_language: str  # es, en, ht


class AITranslateResponse(BaseModel):
    translated_content: str
    target_language: str


class AICalendarIdeaRequest(BaseModel):
    business_name: str
    industry: str
    days: int = Field(default=7, ge=3, le=30)
    language: str = "es"
    tone: str = "engaging"


class AICalendarDayPlan(BaseModel):
    day_number: int
    day_name: str
    content_pillar: str
    post_idea: str
    recommended_platform: str
    caption_starter: str


class AICalendarIdeaResponse(BaseModel):
    days_plan: List[AICalendarDayPlan]
    strategy_summary: str


class AIChatRequest(BaseModel):
    message: str
    language: Optional[str] = "es"  # es, en, ht
    context: Optional[dict] = None


class AIChatResponse(BaseModel):
    reply: str
    suggested_actions: List[dict] = []
    language: str


# Growth Booster & Viral Engine Schemas
class AIBoostPostRequest(BaseModel):
    caption: str
    social_network: str = "instagram"  # instagram, facebook, tiktok, youtube
    goal: str = "followers"  # followers, views, engagement
    target_audience: Optional[str] = "Público general interesado en finanzas y negocios"
    language: Optional[str] = "es"


class AIBoostPostResponse(BaseModel):
    boosted_caption: str
    viral_hook: str
    follower_cta: str
    recommended_hashtags: List[str]
    best_time_to_post: str
    estimated_reach_multiplier: str
    tips: List[str]


class AIBoostCampaignCalcRequest(BaseModel):
    platform: str = "facebook"
    budget_usd: float = 10.0
    duration_days: int = 5
    goal: str = "followers"  # followers, views, engagement
    country: Optional[str] = "Global"


class AIBoostCampaignCalcResponse(BaseModel):
    estimated_impressions_min: int
    estimated_impressions_max: int
    estimated_reach_min: int
    estimated_reach_max: int
    estimated_profile_visits_min: int
    estimated_profile_visits_max: int
    estimated_followers_gain_min: int
    estimated_followers_gain_max: int
    cost_per_follower_est: str
    recommended_strategy: str


class AIBoostLaunchRequest(BaseModel):
    platform: str = "facebook"
    account_username: str = "lajanrapid"
    post_id: Optional[int] = None
    goal: str = "followers"
    budget_usd: float = 10.0
    duration_days: int = 5
    target_interests: Optional[str] = "Negocios, Finanzas, Inversión"
    target_countries: Optional[str] = "Global"


class AIBoostLaunchResponse(BaseModel):
    success: bool
    campaign_id: str
    status: str
    message: str
    projected_results: dict


class AIBoostUrlRequest(BaseModel):
    url: str
    goal: str = "followers"  # followers, views, engagement
    budget_usd: float = 10.0
    duration_days: int = 5
    language: Optional[str] = "es"


class AIBoostUrlResponse(BaseModel):
    detected_platform: str  # facebook, instagram, tiktok, youtube
    target_type: str  # page, post, reel
    extracted_handle_or_id: str
    cleaned_url: str
    headline: str
    viral_hook_recommendation: str
    pinned_comment_template: str
    follower_cta: str
    recommended_hashtags: List[str]
    estimated_impressions: str
    estimated_reach: str
    estimated_followers_gain: str
    suggested_boost_actions: List[str]

