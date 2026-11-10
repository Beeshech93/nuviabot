from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.v1.posts import _format_post_response
from app.core.dependencies import get_current_organization, require_admin
from app.db.models import Organization, Post, User
from app.db.session import get_db
from app.schemas.post import PostResponse, ReviewPostRequest
from app.services.publisher_service import PublisherService

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get("/pending", response_model=List[PostResponse])
def list_pending_approvals(
    current_user: User = Depends(require_admin),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Retrieve all posts awaiting human approval within this organization."""
    posts = (
        db.query(Post)
        .filter(
            Post.organization_id == org.id,
            Post.status == "pending_approval",
        )
        .order_by(Post.created_at.asc())
        .all()
    )
    return [_format_post_response(p, db) for p in posts]


@router.post("/{post_id}/review", response_model=PostResponse)
def review_post(
    post_id: int,
    req: ReviewPostRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Approve or reject a publication. Admin human approval required."""
    post = PublisherService.review_post(
        db,
        post_id=post_id,
        reviewer=current_user,
        action=req.action,
        comments=req.comments or "",
    )
    return _format_post_response(post, db)

