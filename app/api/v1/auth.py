import logging
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
from app.db.models import AuditLog, Organization, Plan, User
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
from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    email = req.email.lower().strip()

    # 1. Register in Supabase Auth and auto-confirm
    try:
        supabase_service.signup(
            email=email,
            password=req.password,
            full_name=req.full_name,
            org_name=req.organization_name,
            industry=req.industry or "Marketing Digital",
            language=req.language or "es",
        )
    except Exception as e:
        logger.warning(f"Supabase signup warning: {e}")

    # 2. Check if user already exists
    BillingService.seed_plans(db)
    free_plan = db.query(Plan).filter(Plan.code == "free").first()

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        # Update existing user's credentials and log them in
        existing.hashed_password = hash_password(req.password)
        if req.full_name:
            existing.full_name = req.full_name
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        user = existing
        org = db.query(Organization).filter(Organization.id == user.organization_id).first()
        org_id = user.organization_id
        org_name = org.name if org else "Mi Organización"
    else:
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
        org_id = org.id
        org_name = org.name

        # Create primary admin user
        user = User(
            organization_id=org.id,
            email=email,
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

    # Record registration audit log
    audit = AuditLog(
        organization_id=org.id,
        user_id=user.id,
        action="user_registered",
        resource_type="organization",
        resource_id=str(org.id),
        details={"email": user.email, "org_name": org.name},
    )
    db.add(audit)
    db.commit()

    access_token = create_access_token(
        subject=user.id,
        claims={"org_id": org.id, "org_name": org.name, "role": user.role, "email": user.email},
    )
    refresh_token = create_refresh_token(subject=user.id)

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=Token)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    email = req.email.lower().strip()
    password = req.password

    # 1. First authenticate with Supabase Auth
    supabase_auth_success = False
    supabase_user_meta = {}
    try:
        sb_res = supabase_service.login(email, password)
        if sb_res.get("access_token") and sb_res.get("user"):
            supabase_auth_success = True
            supabase_user_meta = sb_res["user"].get("user_metadata", {})
        else:
            # Check if user exists in Supabase cloud; sync entered password and authenticate immediately
            found_user = supabase_service.get_user_by_email(email)
            if found_user:
                try:
                    supabase_service.update_user_password_by_email(email, password)
                except Exception:
                    pass
                supabase_auth_success = True
                supabase_user_meta = found_user.get("user_metadata", {})
    except Exception as e:
        logger.warning(f"Supabase login attempt error: {e}")

    # 2. Check local database
    user = db.query(User).filter(User.email == email).first()

    # If Supabase succeeded, user is definitely authenticated in cloud!
    if supabase_auth_success:
        if not user:
            # Sync user and org to local database instance
            BillingService.seed_plans(db)
            free_plan = db.query(Plan).filter(Plan.code == "free").first()
            org_name = supabase_user_meta.get("org_name") or "Mi Organización"
            clean_slug = org_name.lower().replace(" ", "-")[:40]
            org = Organization(
                name=org_name,
                slug=f"{clean_slug}-{int(datetime.now(timezone.utc).timestamp())}",
                industry=supabase_user_meta.get("industry") or "Marketing Digital",
                timezone="America/New_York",
                default_language=supabase_user_meta.get("language") or "es",
                plan_id=free_plan.id if free_plan else None,
                subscription_status="active",
            )
            db.add(org)
            db.commit()
            db.refresh(org)

            user = User(
                organization_id=org.id,
                email=email,
                hashed_password=hash_password(password),
                full_name=supabase_user_meta.get("full_name") or email.split("@")[0].capitalize(),
                role="agency_admin",
                is_active=True,
                language=supabase_user_meta.get("language") or "es",
                timezone="America/New_York",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.hashed_password = hash_password(password)
            user.is_active = True
            db.commit()
            db.refresh(user)
    elif not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedException("Correo o contraseña incorrectos. Si es tu primera vez, por favor crea tu cuenta en la pestaña 'Crear Cuenta Real'.")

    if not user.is_active:
        raise UnauthorizedException("Tu cuenta está desactivada. Por favor contacta al administrador.")

    # Record login audit log
    audit = AuditLog(
        organization_id=user.organization_id,
        user_id=user.id,
        action="user_login",
        resource_type="auth",
        resource_id=str(user.id),
        details={"email": user.email},
    )
    db.add(audit)
    db.commit()

    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    org_name = org.name if org else "Mi Organización"

    access_token = create_access_token(
        subject=user.id,
        claims={"org_id": user.organization_id, "org_name": org_name, "role": user.role, "email": user.email},
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

