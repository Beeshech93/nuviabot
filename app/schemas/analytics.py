from datetime import date
from typing import Dict, List, Optional
from pydantic import BaseModel


class MetricPoint(BaseModel):
    date: date
    value: int


class PlatformSummary(BaseModel):
    platform: str
    connected_accounts: int
    followers: int
    impressions: int
    reach: int
    views: int
    likes: int
    comments: int
    shares: int
    engagement_rate: float


class AnalyticsSummaryResponse(BaseModel):
    is_demo_data: bool
    total_connected_accounts: int
    total_followers: int
    total_impressions: int
    total_reach: int
    total_views: int
    total_engagement_rate: float
    total_posts_published: int
    followers_growth_pct: float
    impressions_growth_pct: float
    by_platform: Dict[str, PlatformSummary]
    timeline_impressions: List[MetricPoint] = []
    timeline_followers: List[MetricPoint] = []
    timeline_engagement: List[MetricPoint] = []


class TopPostItem(BaseModel):
    id: int
    title: str
    content_snippet: str
    platform: str
    published_at: Optional[str] = None
    impressions: int
    likes: int
    comments: int
    shares: int
    engagement_rate: float

