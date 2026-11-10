import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project Info
    PROJECT_NAME: str = "NUVIO GROWTH BOT"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Security & Auth
    SECRET_KEY: str = "nuvio-growth-bot-super-secure-production-secret-key-32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # 32-byte Fernet key for encrypting OAuth tokens in database
    ENCRYPTION_KEY: str = "dGVzdF9mZXJuZXRfa2V5XzMyX2J5dGVzX2FkZGFkZGFkZGFkZGE="

    # Database
    DATABASE_URL: str = (
        "sqlite:////tmp/nuviabot.db"
        if os.getenv("VERCEL")
        else "sqlite:///./nuviabot.db"
    )

    # OpenAI / AI Assistant
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Social APIs OAuth Credentials
    # Meta (Instagram Graph API & Facebook Graph API)
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_REDIRECT_URI: str = "http://localhost:8000/api/v1/social/callback/meta"

    # TikTok Content Posting API
    TIKTOK_CLIENT_KEY: str = ""
    TIKTOK_CLIENT_SECRET: str = ""
    TIKTOK_REDIRECT_URI: str = "http://localhost:8000/api/v1/social/callback/tiktok"

    # Google / YouTube Data API v3
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/social/callback/youtube"

    # Stripe Billing
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Media Storage
    STORAGE_TYPE: str = "local"  # 'local' or 's3'
    UPLOAD_DIR: str = (
        "/tmp/uploads"
        if os.getenv("VERCEL")
        else os.path.join(os.getcwd(), "app", "static", "uploads")
    )
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    ALLOWED_VIDEO_TYPES: List[str] = ["video/mp4", "video/quicktime", "video/webm"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 120

    # Localization & Default Settings
    DEFAULT_LANGUAGE: str = "es"  # es, en, ht
    DEFAULT_TIMEZONE: str = "America/New_York"


settings = Settings()

