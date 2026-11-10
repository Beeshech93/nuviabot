from typing import Dict
from app.services.social.base import SocialAdapter
from app.services.social.facebook import FacebookAdapter
from app.services.social.instagram import InstagramAdapter
from app.services.social.tiktok import TikTokAdapter
from app.services.social.youtube import YouTubeAdapter

ADAPTERS: Dict[str, SocialAdapter] = {
    "instagram": InstagramAdapter(),
    "facebook": FacebookAdapter(),
    "tiktok": TikTokAdapter(),
    "youtube": YouTubeAdapter(),
}


def get_social_adapter(platform: str) -> SocialAdapter:
    """Retrieve the dedicated official adapter for the given social network."""
    adapter = ADAPTERS.get(platform.lower())
    if not adapter:
        raise ValueError(f"Platform '{platform}' is not supported.")
    return adapter

