from typing import List
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.core.exceptions import PermissionDeniedException, UnauthorizedException
from app.core.security import decode_token
from app.db.models import Organization, User
from app.db.session import get_db

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT bearer token and return the authenticated User."""
    if not auth or not auth.credentials:
        raise UnauthorizedException("Authentication token required")

    payload = decode_token(auth.credentials)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedException("Invalid or expired access token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Token payload missing subject")

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise UnauthorizedException("Malformed token identifier")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        email = payload.get("email")
        if email:
            from datetime import datetime, timezone
            from app.db.models import Plan
            from app.services.billing_service import BillingService

            BillingService.seed_plans(db)
            free_plan = db.query(Plan).filter(Plan.code == "free").first()

            org_id = payload.get("org_id", 1)
            org = db.query(Organization).filter(Organization.id == org_id).first()
            if not org:
                org = Organization(
                    id=org_id,
                    name=payload.get("org_name", "Mi Organización"),
                    slug=f"org-{int(datetime.now(timezone.utc).timestamp())}",
                    industry="Marketing Digital",
                    timezone="America/New_York",
                    default_language="es",
                    plan_id=free_plan.id if free_plan else None,
                    subscription_status="active",
                )
                db.add(org)
                db.commit()
                db.refresh(org)

            user = User(
                id=user_id,
                organization_id=org.id,
                email=email.lower(),
                hashed_password="SUPABASE_MANAGED_SESSION",
                full_name=email.split("@")[0].capitalize(),
                role=payload.get("role", "agency_admin"),
                is_active=True,
                language="es",
                timezone="America/New_York",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            raise UnauthorizedException("User no longer exists")

    if not user.is_active:
        raise UnauthorizedException("Account is disabled")

    return user


def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Organization:
    """Strict multi-tenant boundary: Returns the current user's organization."""
    org = (
        db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    )
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found for active user",
        )
    return org


class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role == "super_admin":
            return user

        if user.role not in self.allowed_roles:
            raise PermissionDeniedException(
                f"Action requires one of the following roles: {', '.join(self.allowed_roles)}"
            )
        return user


# Common role dependencies
require_admin = RoleChecker(["agency_admin", "client_admin", "super_admin"])
require_editor = RoleChecker(["agency_admin", "client_admin", "editor", "super_admin"])

