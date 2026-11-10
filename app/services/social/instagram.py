import urllib.parse
from typing import Any, Dict, List, Optional
import httpx
from app.config import settings
from app.services.social.base import SocialAdapter


class InstagramAdapter(SocialAdapter):
    """Instagram Graph API official adapter for Professional / Creator / Business accounts."""

    BASE_GRAPH_URL = "https://graph.facebook.com/v20.0"
    OAUTH_DIALOG_URL = "https://www.facebook.com/v20.0/dialog/oauth"

    SCOPES = [
        "instagram_basic",
        "instagram_content_publish",
        "instagram_manage_insights",
        "pages_show_list",
        "pages_read_engagement",
    ]

    def get_authorization_url(self, state: str) -> str:
        # If META_APP_ID is not configured in .env, seamlessly use developer sandbox OAuth simulation
        if not settings.META_APP_ID:
            return f"/api/v1/social/callback/instagram?code=sandbox_ig_auth_{state[:8]}&state={state}"

        redirect_uri = settings.META_REDIRECT_URI.replace("/meta", "/instagram")
        params = {
            "client_id": settings.META_APP_ID,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": ",".join(self.SCOPES),
            "response_type": "code",
        }
        return f"{self.OAUTH_DIALOG_URL}?{urllib.parse.urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        if not settings.META_APP_SECRET or not settings.META_APP_ID:
            # Return structured mock for local developer sandbox when credentials not yet set
            return {
                "access_token": f"mock_ig_access_token_{code[:10]}",
                "refresh_token": f"mock_ig_refresh_token_{code[:10]}",
                "expires_in": 5184000,  # 60 days
                "token_type": "bearer",
            }

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_GRAPH_URL}/oauth/access_token",
                params={
                    "client_id": settings.META_APP_ID,
                    "client_secret": settings.META_APP_SECRET,
                    "redirect_uri": settings.META_REDIRECT_URI,
                    "code": code,
                },
                timeout=15.0,
            )
            data = resp.json()
            if "error" in data:
                raise Exception(
                    f"Instagram OAuth error: {data['error'].get('message', 'Unknown error')}"
                )
            return data

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        if not settings.META_APP_SECRET or not settings.META_APP_ID:
            return {
                "access_token": f"refreshed_ig_token_{refresh_token[:8]}",
                "expires_in": 5184000,
            }

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_GRAPH_URL}/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": settings.META_APP_ID,
                    "client_secret": settings.META_APP_SECRET,
                    "fb_exchange_token": refresh_token,
                },
                timeout=15.0,
            )
            return resp.json()

    async def get_account_profile(self, access_token: str) -> Dict[str, Any]:
        if access_token.startswith("mock_"):
            return {
                "id": "17841400000000001",
                "username": "nuvio_instagram_biz",
                "display_name": "Nuvio Business IG",
                "profile_picture_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150",
                "followers_count": 8420,
                "following_count": 342,
                "posts_count": 94,
            }

        async with httpx.AsyncClient() as client:
            # Query the user's accounts to get the connected Instagram Business account
            resp = await client.get(
                f"{self.BASE_GRAPH_URL}/me/accounts",
                params={
                    "fields": "instagram_business_account{id,username,name,profile_picture_url,followers_count,media_count}",
                    "access_token": access_token,
                },
                timeout=15.0,
            )
            data = resp.json()
            accounts = data.get("data", [])
            for page in accounts:
                ig_biz = page.get("instagram_business_account")
                if ig_biz:
                    return {
                        "id": ig_biz.get("id"),
                        "username": ig_biz.get("username", "instagram_user"),
                        "display_name": ig_biz.get("name", ig_biz.get("username")),
                        "profile_picture_url": ig_biz.get("profile_picture_url", ""),
                        "followers_count": ig_biz.get("followers_count", 0),
                        "following_count": 0,
                        "posts_count": ig_biz.get("media_count", 0),
                    }

            return {
                "id": "ig_pending_id",
                "username": "ig_creator",
                "display_name": "Instagram Creator",
                "profile_picture_url": "",
                "followers_count": 0,
                "following_count": 0,
                "posts_count": 0,
            }

    async def publish_content(
        self,
        access_token: str,
        account_id: str,
        content: str,
        media_urls: Optional[list] = None,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Instagram Graph API requires a 2-step container creation and publish flow."""
        if access_token.startswith("mock_"):
            import time

            return {
                "success": True,
                "platform": "instagram",
                "post_id": f"ig_post_{int(time.time())}",
                "status": "published",
            }

        image_url = media_urls[0] if media_urls else None
        if not image_url:
            raise Exception("Instagram requires at least one image or video URL to publish.")

        async with httpx.AsyncClient() as client:
            # Step 1: Create media container
            container_resp = await client.post(
                f"{self.BASE_GRAPH_URL}/{account_id}/media",
                data={
                    "image_url": image_url,
                    "caption": content,
                    "access_token": access_token,
                },
                timeout=30.0,
            )
            container_data = container_resp.json()
            container_id = container_data.get("id")
            if not container_id:
                raise Exception(
                    f"Instagram container creation error: {container_data.get('error', {}).get('message', 'Failed container')}"
                )

            # Step 2: Publish container
            publish_resp = await client.post(
                f"{self.BASE_GRAPH_URL}/{account_id}/media_publish",
                data={
                    "creation_id": container_id,
                    "access_token": access_token,
                },
                timeout=30.0,
            )
            publish_data = publish_resp.json()
            post_id = publish_data.get("id")
            if not post_id:
                raise Exception(
                    f"Instagram publish error: {publish_data.get('error', {}).get('message', 'Failed publication')}"
                )

            return {
                "success": True,
                "platform": "instagram",
                "post_id": post_id,
                "status": "published",
            }

    async def fetch_insights(
        self, access_token: str, account_id: str, since_days: int = 30
    ) -> Dict[str, Any]:
        if access_token.startswith("mock_"):
            return {
                "impressions": 14250,
                "reach": 9800,
                "views": 18200,
                "likes": 1280,
                "comments": 310,
                "shares": 194,
                "engagement_rate": 3.8,
            }

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_GRAPH_URL}/{account_id}/insights",
                params={
                    "metric": "impressions,reach,profile_views",
                    "period": "day",
                    "access_token": access_token,
                },
                timeout=15.0,
            )
            return resp.json()

