from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class PostBase(BaseModel):
    title: Optional[str] = ""
    content: str
    target_platforms: List[str]  # ["instagram", "facebook", "tiktok", "youtube"]
    media_ids: Optional[List[int]] = []
    scheduled_at: Optional[datetime] = None
    timezone: Optional[str] = "America/New_York"
    client_id: Optional[int] = None
    auto_publish_without_approval: Optional[bool] = False


class PostCreate(PostBase):
    submit_for_approval: Optional[bool] = False


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    target_platforms: Optional[List[str]] = None
    media_ids: Optional[List[int]] = None
    scheduled_at: Optional[datetime] = None
    timezone: Optional[str] = None
    client_id: Optional[int] = None
    auto_publish_without_approval: Optional[bool] = None


class ApprovalLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    user_id: int
    action: str  # submitted, approved, rejected
    comments: Optional[str] = ""
    reviewer_name: Optional[str] = ""
    created_at: datetime


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    client_id: Optional[int] = None
    author_id: int
    author_name: Optional[str] = ""
    title: Optional[str] = ""
    content: str
    target_platforms: List[str]
    media_ids: List[int]
    media_urls: Optional[List[str]] = []
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    timezone: str
    status: str
    rejection_reason: Optional[str] = ""
    auto_publish_without_approval: bool
    platform_post_ids: Optional[Dict[str, Any]] = {}
    publish_errors: Optional[Dict[str, Any]] = {}
    retry_count: int
    approval_logs: Optional[List[ApprovalLogResponse]] = []
    created_at: datetime
    updated_at: datetime


class ReviewPostRequest(BaseModel):
    action: str  # "approved" or "rejected"
    comments: Optional[str] = ""


class PublishNowRequest(BaseModel):
    force: Optional[bool] = False
