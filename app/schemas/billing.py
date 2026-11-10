from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    price_monthly: float
    price_annual: float
    max_social_accounts: int
    max_posts_per_month: int
    max_ai_credits: int
    max_clients: int
    max_team_members: int
    features: List[str]


class SubscriptionStatusResponse(BaseModel):
    plan_name: str
    plan_code: str
    status: str
    is_active: bool
    current_period_end: Optional[str] = None
    social_accounts_used: int
    social_accounts_limit: int
    posts_published_this_month: int
    posts_limit: int
    ai_credits_used: int
    ai_credits_limit: int
    team_members_count: int
    team_members_limit: int
    clients_count: int
    clients_limit: int
    stripe_configured: bool


class CreateCheckoutSessionRequest(BaseModel):
    plan_code: str  # starter, pro, agency
    billing_cycle: str = "monthly"  # monthly, annual
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str
    is_mock: bool = False
