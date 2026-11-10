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

