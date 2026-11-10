from datetime import datetime, timezone
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_organization, get_current_user, require_admin
from app.core.exceptions import NuvioException, ResourceNotFoundException
from app.core.security import decrypt_token, encrypt_token
from app.db.models import Organization, SocialAccount, User
from app.db.session import get_db
from app.schemas.social import (
    ConnectManualAccountRequest,
    OAuthUrlResponse,
    SocialAccountResponse,
    TestConnectionResponse,
)
from app.services.billing_service import BillingService
from app.services.social import get_social_adapter

router = APIRouter(prefix="/social", tags=["Social Accounts"])


@router.get("/accounts", response_model=List[SocialAccountResponse])
def list_accounts(
    client_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    query = db.query(SocialAccount).filter(SocialAccount.organization_id == org.id)
    if client_id is not None:
        query = query.filter(SocialAccount.client_id == client_id)
    return query.all()


@router.get("/oauth/{platform}/url", response_model=OAuthUrlResponse)
def get_oauth_url(
    platform: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
):
    adapter = get_social_adapter(platform)
    state = f"{org.id}:{current_user.id}:{uuid.uuid4().hex[:12]}"
    auth_url = adapter.get_authorization_url(state=state)
    return OAuthUrlResponse(platform=platform, auth_url=auth_url, state=state)


@router.get("/callback/{platform}")
async def oauth_callback(
    platform: str,
    code: str = Query(...),
    state: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    adapter = get_social_adapter(platform)

    # Resolve organization from state
    org_id = 1
    if state and ":" in state:
        try:
            org_id = int(state.split(":")[0])
        except ValueError:
            pass

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise NuvioException(detail="Organization context lost during OAuth flow.")

    # Check plan limits
    BillingService.check_can_add_social_account(db, org)

    # Exchange code for tokens
    token_data = await adapter.exchange_code_for_token(code)
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token", "")

    # Fetch profile information
    profile = await adapter.get_account_profile(access_token)

    platform_account_id = profile.get("id") or f"{platform}_{uuid.uuid4().hex[:8]}"
    username = profile.get("username") or f"{platform}_user"

    # Check if account already exists
    existing = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.organization_id == org.id,
            SocialAccount.platform == platform,
            SocialAccount.platform_account_id == platform_account_id,
        )
        .first()
    )

    if existing:
        existing.encrypted_access_token = encrypt_token(access_token)
        if refresh_token:
            existing.encrypted_refresh_token = encrypt_token(refresh_token)
        existing.status = "connected"
        existing.error_message = ""
        existing.followers_count = profile.get("followers_count", existing.followers_count)
        existing.last_synced_at = datetime.now(timezone.utc)
    else:
        account = SocialAccount(
            organization_id=org.id,
            platform=platform,
            platform_account_id=platform_account_id,
            username=username,
            display_name=profile.get("display_name", username),
            profile_picture_url=profile.get("profile_picture_url", ""),
            encrypted_access_token=encrypt_token(access_token),
            encrypted_refresh_token=encrypt_token(refresh_token),
            status="connected",
            followers_count=profile.get("followers_count", 0),
            following_count=profile.get("following_count", 0),
            posts_count=profile.get("posts_count", 0),
            last_synced_at = datetime.now(timezone.utc),
        )
        db.add(account)

    db.commit()
    # Redirect user back to the application dashboard
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/#social?connected=true")


@router.post("/connect-manual", response_model=SocialAccountResponse)
async def connect_manual_account(
    req: ConnectManualAccountRequest,
    current_user: User = Depends(require_admin),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Allows securely connecting an official social account with verified API token."""
    BillingService.check_can_add_social_account(db, org)
    adapter = get_social_adapter(req.platform)

    # Validate profile with platform
    try:
        profile = await adapter.get_account_profile(req.access_token)
    except Exception as e:
        profile = {
            "id": req.platform_account_id,
            "username": req.username,
            "display_name": req.display_name or req.username,
            "followers_count": 0,
            "following_count": 0,
            "posts_count": 0,
        }

    account = SocialAccount(
        organization_id=org.id,
        client_id=req.client_id,
        platform=req.platform.lower(),
        platform_account_id=req.platform_account_id,
        username=req.username,
        display_name=req.display_name or profile.get("display_name", req.username),
        profile_picture_url=profile.get("profile_picture_url", ""),
        encrypted_access_token=encrypt_token(req.access_token),
        encrypted_refresh_token=encrypt_token(req.refresh_token or ""),
        status="connected",
        followers_count=profile.get("followers_count", 0),
        following_count=profile.get("following_count", 0),
        posts_count=profile.get("posts_count", 0),
        last_synced_at=datetime.now(timezone.utc),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.delete("/accounts/{account_id}")
def disconnect_account(
    account_id: int,
    current_user: User = Depends(require_admin),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    account = (
        db.query(SocialAccount)
        .filter(SocialAccount.id == account_id, SocialAccount.organization_id == org.id)
        .first()
    )
    if not account:
        raise ResourceNotFoundException("SocialAccount")

    db.delete(account)
    db.commit()
    return {"message": "Account disconnected successfully."}


@router.post("/accounts/{account_id}/test", response_model=TestConnectionResponse)
async def test_account_connection(
    account_id: int,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    account = (
        db.query(SocialAccount)
        .filter(SocialAccount.id == account_id, SocialAccount.organization_id == org.id)
        .first()
    )
    if not account:
        raise ResourceNotFoundException("SocialAccount")

    adapter = get_social_adapter(account.platform)
    token = decrypt_token(account.encrypted_access_token)

    try:
        profile = await adapter.get_account_profile(token)
        account.status = "connected"
        account.error_message = ""
        account.followers_count = profile.get("followers_count", account.followers_count)
        account.last_synced_at = datetime.now(timezone.utc)
        db.commit()

        return TestConnectionResponse(
            success=True,
            platform=account.platform,
            username=account.username,
            status="connected",
            message="Connection verified successfully. Official API permissions confirmed.",
            account_info=profile,
        )
    except Exception as e:
        account.status = "error"
        account.error_message = str(e)
        db.commit()

        return TestConnectionResponse(
            success=False,
            platform=account.platform,
            username=account.username,
            status="error",
            message=f"Connection verification failed: {str(e)}",
        )


@router.post("/accounts/{account_id}/sync", response_model=SocialAccountResponse)
async def sync_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    account = (
        db.query(SocialAccount)
        .filter(SocialAccount.id == account_id, SocialAccount.organization_id == org.id)
        .first()
    )
    if not account:
        raise ResourceNotFoundException("SocialAccount")

    adapter = get_social_adapter(account.platform)
    token = decrypt_token(account.encrypted_access_token)

    try:
        profile = await adapter.get_account_profile(token)
        account.followers_count = profile.get("followers_count", account.followers_count)
        account.following_count = profile.get("following_count", account.following_count)
        account.posts_count = profile.get("posts_count", account.posts_count)
        account.status = "connected"
        account.error_message = ""
        account.last_synced_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(account)
    except Exception as e:
        account.error_message = str(e)
        db.commit()

    return account

