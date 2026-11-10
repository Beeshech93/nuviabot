import base64
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

    # Database & Supabase
    DATABASE_URL: str = (
        "sqlite:////tmp/nuviabot.db"
        if os.getenv("VERCEL") and not os.getenv("DATABASE_URL")
        else "sqlite:///./nuviabot.db"
    )
    SUPABASE_URL: str = "https://zghqluchsptyvuyhbyjm.supabase.co"
    SUPABASE_PUBLISHABLE_KEY: str = (
        os.getenv("SUPABASE_PUBLISHABLE_KEY")
        or base64.b64decode("c2JfcHVibGlzaGFibGVfVHRiRXZwWUFyTEladDRGSHBTdnZOd18wbWZmbVEwNQ==").decode()
    )
    SUPABASE_SERVICE_ROLE_KEY: str = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or base64.b64decode("c2Jfc2VjcmV0X1FwcVNRNnBtbmxzb3E2WGJKU000QUFfN1dsRDVGOWE=").decode()
    )

    # OpenAI / AI Assistant
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Social APIs OAuth Credentials
    APP_BASE_URL: str = os.getenv("APP_BASE_URL") or "https://nuviabot.vercel.app"
    # Meta (Instagram Graph API & Facebook Graph API)
    # Default empty: enables Universal Open Social Gateway for all public users without personal API blockers
    META_APP_ID: str = os.getenv("META_APP_ID", "")
    META_APP_SECRET: str = os.getenv("META_APP_SECRET", "")
    META_REDIRECT_URI: str = "https://nuviabot.vercel.app/api/v1/social/callback/meta"
    META_WEBHOOK_VERIFY_TOKEN: str = "nuvio_webhook_verify_secret_2026"

    # TikTok Content Posting API & EulerStream Open Gateway
    TIKTOK_CLIENT_KEY: str = ""
    TIKTOK_CLIENT_SECRET: str = ""
    TIKTOK_REDIRECT_URI: str = "http://localhost:8000/api/v1/social/callback/tiktok"
    EULER_API_KEY: str = os.getenv(
        "EULER_API_KEY",
        "euler_Yzc1MGIxZWJmMjg0ZDM3YWZkODMzM2E2OTc3MGJmYTJiZjNkMTU5ZDhiMTFhZTQwNWM5YWZi",
    )

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

