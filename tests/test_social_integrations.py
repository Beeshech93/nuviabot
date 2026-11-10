import pytest
from app.core.security import decrypt_token, encrypt_token
from app.services.social import get_social_adapter
from app.services.social.facebook import FacebookAdapter
from app.services.social.instagram import InstagramAdapter
from app.services.social.tiktok import TikTokAdapter
from app.services.social.youtube import YouTubeAdapter


def test_token_encryption_and_decryption():
    raw_token = "EAABwzLIX450BO1z9382109asdasd91283019283"
    encrypted = encrypt_token(raw_token)
    assert encrypted != raw_token
    decrypted = decrypt_token(encrypted)
    assert decrypted == raw_token


def test_adapter_registry():
    assert isinstance(get_social_adapter("instagram"), InstagramAdapter)
    assert isinstance(get_social_adapter("facebook"), FacebookAdapter)
    assert isinstance(get_social_adapter("tiktok"), TikTokAdapter)
    assert isinstance(get_social_adapter("youtube"), YouTubeAdapter)

    with pytest.raises(ValueError):
        get_social_adapter("unsupported_network")


def test_oauth_url_generation(monkeypatch):
    from app.config import settings

    ig_adapter = get_social_adapter("instagram")

    # In sandbox mode (no app id configured), returns internal callback simulation
    ig_sandbox_url = ig_adapter.get_authorization_url(state="test_state_123")
    assert "/api/v1/social/callback/instagram" in ig_sandbox_url

    # When Meta App ID is configured, returns official Facebook dialog
    monkeypatch.setattr(settings, "META_APP_ID", "123456789012345")
    ig_live_url = ig_adapter.get_authorization_url(state="test_state_123")
    assert "dialog/oauth" in ig_live_url
    assert "instagram_basic" in ig_live_url
    assert "state=test_state_123" in ig_live_url

    # TikTok live URL
    monkeypatch.setattr(settings, "TIKTOK_CLIENT_KEY", "test_tiktok_key")
    tt_adapter = get_social_adapter("tiktok")
    tt_url = tt_adapter.get_authorization_url(state="test_state_456")
    assert "tiktok.com" in tt_url
    assert "video.publish" in tt_url

    # YouTube live URL
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test_google_client_id")
    yt_adapter = get_social_adapter("youtube")
    yt_url = yt_adapter.get_authorization_url(state="test_state_789")
    assert "accounts.google.com" in yt_url
    assert "youtube.upload" in yt_url


@pytest.mark.asyncio
async def test_mock_adapter_publishing_flows():
    for platform in ["instagram", "facebook", "tiktok", "youtube"]:
        adapter = get_social_adapter(platform)
        result = await adapter.publish_content(
            access_token="mock_token_123",
            account_id="mock_acc_123",
            content="Testing publication workflow",
            media_urls=["https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe"],
            title="Test Post",
        )
        assert result["success"] is True
        assert result["platform"] == platform
        assert result["status"] == "published"

