from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user
from app.core.exceptions import NuvioException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.db.models import Organization, Plan, User
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    PasswordChangeRequest,
    RegisterRequest,
    Token,
    UserResponse,
    UserUpdate,
)
from app.services.billing_service import BillingService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise NuvioException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Ensure plans exist
    BillingService.seed_plans(db)
    free_plan = db.query(Plan).filter(Plan.code == "free").first()

    # Generate organization slug
    clean_slug = req.organization_name.lower().replace(" ", "-")[:40]
    org = Organization(
        name=req.organization_name,
        slug=f"{clean_slug}-{int(datetime.now(timezone.utc).timestamp())}",
        industry=req.industry or "General",
        timezone=req.timezone or "America/New_York",
        default_language=req.language or "es",
        plan_id=free_plan.id if free_plan else None,
        subscription_status="active",
        auto_publish_enabled=False,
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    # Create primary admin user
    user = User(
        organization_id=org.id,
        email=req.email.lower(),
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role="agency_admin",  # Primary owner has agency_admin role
        is_active=True,
        language=req.language or "es",
        timezone=req.timezone or "America/New_York",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(
        subject=user.id,
        claims={"org_id": org.id, "role": user.role, "email": user.email},
    )
    refresh_token = create_refresh_token(subject=user.id)

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=Token)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password.")

    if not user.is_active:
        raise UnauthorizedException("Account is disabled. Please contact your administrator.")

    access_token = create_access_token(
        subject=user.id,
        claims={"org_id": user.organization_id, "role": user.role, "email": user.email},
    )
    refresh_token = create_refresh_token(subject=user.id)

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_profile(
    req: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.full_name is not None:
        current_user.full_name = req.full_name
    if req.language is not None:
        current_user.language = req.language
    if req.timezone is not None:
        current_user.timezone = req.timezone
    if req.avatar_url is not None:
        current_user.avatar_url = req.avatar_url

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/change-password")
def change_password(
    req: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(req.current_password, current_user.hashed_password):
        raise NuvioException(detail="Current password does not match.")

    if len(req.new_password) < 8:
        raise NuvioException(detail="New password must be at least 8 characters.")

    current_user.hashed_password = hash_password(req.new_password)
    db.commit()
    return {"message": "Password updated successfully."}

