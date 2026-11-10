from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_organization, require_admin
from app.core.exceptions import NuvioException, ResourceNotFoundException
from app.core.security import hash_password
from app.db.models import Organization, User
from app.db.session import get_db
from app.schemas.settings import TeamMemberInviteRequest, TeamMemberResponse
from app.services.billing_service import BillingService

router = APIRouter(prefix="/team", tags=["Team Members"])


@router.get("", response_model=List[TeamMemberResponse])
def list_team_members(
    current_user: User = Depends(require_admin),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    users = db.query(User).filter(User.organization_id == org.id).all()
    return [
        TeamMemberResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at.strftime("%Y-%m-%d"),
        )
        for u in users
    ]


@router.post("/invite", response_model=TeamMemberResponse)
def invite_team_member(
    req: TeamMemberInviteRequest,
    current_user: User = Depends(require_admin),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    BillingService.check_can_add_team_member(db, org)

    # Check if email taken
    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise NuvioException(detail="A user with this email address already exists.")

    valid_roles = ["agency_admin", "client_admin", "editor", "viewer"]
    if req.role not in valid_roles:
        raise NuvioException(detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}")

    # Default temporary password: Password123!
    user = User(
        organization_id=org.id,
        email=req.email.lower(),
        full_name=req.full_name,
        role=req.role,
        hashed_password=hash_password("NuvioGrowth2026!"),
        is_active=True,
        language=org.default_language,
        timezone=org.timezone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TeamMemberResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.strftime("%Y-%m-%d"),
    )


@router.delete("/{user_id}")
def remove_team_member(
    user_id: int,
    current_user: User = Depends(require_admin),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise NuvioException(detail="You cannot remove yourself from the organization.")

    user = (
        db.query(User)
        .filter(User.id == user_id, User.organization_id == org.id)
        .first()
    )
    if not user:
        raise ResourceNotFoundException("Team Member")

    db.delete(user)
    db.commit()
    return {"message": "Team member removed successfully."}

