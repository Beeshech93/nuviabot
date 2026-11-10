from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class SocialAdapter(ABC):
    """Abstract base adapter for official Social Media APIs.

    Follows official platform terms and legitimate growth practices:
    - Official OAuth workflows
    - Legitimate publishing
    - Real statistics
    - Respect for platform rate limits
    """

    @abstractmethod
    def get_authorization_url(self, state: str) -> str:
        """Returns the official OAuth authorization URL for user login."""
        pass

    @abstractmethod
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchanges temporary OAuth authorization code for access and refresh tokens."""
        pass

    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refreshes expired access token when supported by platform."""
        pass

    @abstractmethod
    async def get_account_profile(self, access_token: str) -> Dict[str, Any]:
        """Fetches authentic account profile information (ID, username, avatar, follower counts)."""
        pass

    @abstractmethod
    async def publish_content(
        self,
        access_token: str,
        account_id: str,
        content: str,
        media_urls: Optional[list] = None,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Publishes content legitimately through the official platform API."""
        pass

    @abstractmethod
    async def fetch_insights(
        self, access_token: str, account_id: str, since_days: int = 30
    ) -> Dict[str, Any]:
        """Fetches authentic performance analytics and insights from official endpoints."""
        pass

