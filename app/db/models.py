from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.db.session import Base


def utc_now():
    return datetime.now(timezone.utc)


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    code = Column(String(20), unique=True, nullable=False)  # free, starter, pro, agency
    price_monthly = Column(Float, default=0.0)
    price_annual = Column(Float, default=0.0)
    max_social_accounts = Column(Integer, default=1)
    max_posts_per_month = Column(Integer, default=20)
    max_ai_credits = Column(Integer, default=50)
    max_clients = Column(Integer, default=1)
    max_team_members = Column(Integer, default=1)
    features = Column(JSON, default=list)

    organizations = relationship("Organization", back_populates="plan")


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    industry = Column(String(100), default="General")
    logo_url = Column(String(500), default="")
    timezone = Column(String(50), default="America/New_York")
    default_language = Column(String(10), default="es")

    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True)
    stripe_customer_id = Column(String(100), nullable=True)
    stripe_subscription_id = Column(String(100), nullable=True)
    subscription_status = Column(String(50), default="trialing")
    trial_ends_at = Column(DateTime, nullable=True)

    ai_credits_used_this_month = Column(Integer, default=0)
    posts_published_this_month = Column(Integer, default=0)

    # Publishing preference: allows bypassing approval if organization explicitly configures it
    auto_publish_enabled = Column(Boolean, default=False)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    plan = relationship("Plan", back_populates="organizations")
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    social_accounts = relationship(
        "SocialAccount", back_populates="organization", cascade="all, delete-orphan"
    )
    posts = relationship("Post", back_populates="organization", cascade="all, delete-orphan")
    media_assets = relationship(
        "MediaAsset", back_populates="organization", cascade="all, delete-orphan"
    )
    client_workspaces = relationship(
        "ClientWorkspace", back_populates="organization", cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "AuditLog", back_populates="organization", cascade="all, delete-orphan"
    )
    ad_campaigns = relationship(
        "AdCampaign", back_populates="organization", cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    # Roles: super_admin, agency_admin, client_admin, editor, viewer
    role = Column(String(50), default="editor", nullable=False)
    is_active = Column(Boolean, default=True)
    language = Column(String(10), default="es")
    timezone = Column(String(50), default="America/New_York")
    avatar_url = Column(String(500), default="")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    organization = relationship("Organization", back_populates="users")
    posts = relationship("Post", back_populates="author")
    approval_logs = relationship("ApprovalLog", back_populates="user")


class ClientWorkspace(Base):
    """Sub-clients or distinct brand workspaces managed under an Agency organization."""

    __tablename__ = "client_workspaces"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    industry = Column(String(100), default="Marketing")
    logo_url = Column(String(500), default="")
    notes = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="client_workspaces")
    social_accounts = relationship("SocialAccount", back_populates="client_workspace")
    posts = relationship("Post", back_populates="client_workspace")


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("client_workspaces.id"), nullable=True)

    # instagram, facebook, tiktok, youtube
    platform = Column(String(50), nullable=False, index=True)
    platform_account_id = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False)
    display_name = Column(String(100), default="")
    profile_picture_url = Column(String(500), default="")

    encrypted_access_token = Column(Text, nullable=False)
    encrypted_refresh_token = Column(Text, default="")
    token_expires_at = Column(DateTime, nullable=True)
    scopes = Column(Text, default="")

    # connected, expired, error, disconnected
    status = Column(String(30), default="connected", index=True)
    error_message = Column(Text, default="")

    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    metadata_json = Column(JSON, default=dict)
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="social_accounts")
    client_workspace = relationship("ClientWorkspace", back_populates="social_accounts")
    metrics = relationship(
        "AnalyticsMetric", back_populates="social_account", cascade="all, delete-orphan"
    )


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("client_workspaces.id"), nullable=True)

    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(100), nullable=False)
    # image, video, logo, thumbnail
    media_type = Column(String(50), default="image")
    folder = Column(String(100), default="General")
    tags = Column(String(255), default="")
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="media_assets")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("client_workspaces.id"), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(255), default="")
    content = Column(Text, nullable=False)
    # List of platforms: ["instagram", "facebook", "tiktok", "youtube"]
    target_platforms = Column(JSON, default=list)
    # List of MediaAsset IDs: [1, 2]
    media_ids = Column(JSON, default=list)

    scheduled_at = Column(DateTime, nullable=True, index=True)
    published_at = Column(DateTime, nullable=True)
    timezone = Column(String(50), default="America/New_York")

    # draft, pending_approval, approved, scheduled, publishing, published, failed, rejected
    status = Column(String(50), default="draft", index=True)
    rejection_reason = Column(Text, default="")
    auto_publish_without_approval = Column(Boolean, default=False)

    # {"instagram": "ig_12345", "facebook": "fb_67890"}
    platform_post_ids = Column(JSON, default=dict)
    # {"instagram": "Error code 190: Session expired"}
    publish_errors = Column(JSON, default=dict)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    organization = relationship("Organization", back_populates="posts")
    client_workspace = relationship("ClientWorkspace", back_populates="posts")
    author = relationship("User", back_populates="posts")
    approval_logs = relationship(
        "ApprovalLog", back_populates="post", cascade="all, delete-orphan"
    )


class ApprovalLog(Base):
    __tablename__ = "approval_logs"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # submitted, approved, rejected
    action = Column(String(50), nullable=False)
    comments = Column(Text, default="")
    created_at = Column(DateTime, default=utc_now)

    post = relationship("Post", back_populates="approval_logs")
    user = relationship("User", back_populates="approval_logs")


class AnalyticsMetric(Base):
    __tablename__ = "analytics_metrics"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    social_account_id = Column(
        Integer, ForeignKey("social_accounts.id"), nullable=False, index=True
    )
    platform = Column(String(50), nullable=False, index=True)
    metric_date = Column(Date, nullable=False, index=True)

    followers = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    raw_data = Column(JSON, default=dict)

    social_account = relationship("SocialAccount", back_populates="metrics")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), default="")
    ip_address = Column(String(50), default="")
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="audit_logs")


class AdCampaign(Base):
    __tablename__ = "ad_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    campaign_uid = Column(String(100), unique=True, index=True)
    platform = Column(String(50), nullable=False)  # "facebook" or "tiktok"
    name = Column(String(255), nullable=False)
    objective = Column(String(100), default="followers")
    status = Column(String(50), default="active", index=True)  # "active", "paused", "in_review", "completed"

    budget_usd = Column(Float, default=10.0)
    daily_budget_usd = Column(Float, default=2.0)
    duration_days = Column(Integer, default=5)
    spend_usd = Column(Float, default=0.0)

    target_url = Column(String(500), default="")
    account_username = Column(String(100), default="")
    target_countries = Column(String(255), default="Global")
    target_interests = Column(String(255), default="Negocios, Finanzas, Inversión")

    ad_headline = Column(String(255), default="")
    ad_text = Column(Text, default="")
    call_to_action = Column(String(100), default="SEGUIR_PAGINA")

    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    video_views = Column(Integer, default=0)
    new_followers = Column(Integer, default=0)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    organization = relationship("Organization", back_populates="ad_campaigns")

