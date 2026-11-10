from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_organization, get_current_user, require_editor
from app.core.exceptions import NuvioException, ResourceNotFoundException
from app.db.models import ApprovalLog, MediaAsset, Organization, Post, User
from app.db.session import get_db
from app.schemas.post import (
    ApprovalLogResponse,
    PostCreate,
    PostResponse,
    PostUpdate,
    PublishNowRequest,
)
from app.services.billing_service import BillingService
from app.services.publisher_service import PublisherService

router = APIRouter(prefix="/posts", tags=["Publications"])


def _format_post_response(post: Post, db: Session) -> PostResponse:
    # Gather media URLs
    media_urls = []
    if post.media_ids:
        media_assets = (
            db.query(MediaAsset).filter(MediaAsset.id.in_(post.media_ids)).all()
        )
        media_urls = [m.file_url for m in media_assets]

    # Gather approval logs
    logs = (
        db.query(ApprovalLog)
        .filter(ApprovalLog.post_id == post.id)
        .order_by(ApprovalLog.created_at.desc())
        .all()
    )

    resp = PostResponse.model_validate(post)
    resp.author_name = post.author.full_name if post.author else "Team Member"
    resp.media_urls = media_urls
    resp.approval_logs = [
        ApprovalLogResponse(
            id=l.id,
            post_id=l.post_id,
            user_id=l.user_id,
            action=l.action,
            comments=l.comments or "",
            reviewer_name=l.user.full_name if l.user else "Reviewer",
            created_at=l.created_at,
        )
        for l in logs
    ]
    return resp


@router.get("", response_model=List[PostResponse])
def list_posts(
    status_filter: Optional[str] = Query(None, alias="status"),
    client_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    query = db.query(Post).filter(Post.organization_id == org.id)
    if status_filter:
        query = query.filter(Post.status == status_filter)
    if client_id is not None:
        query = query.filter(Post.client_id == client_id)

    posts = query.order_by(Post.created_at.desc()).all()
    return [_format_post_response(p, db) for p in posts]


@router.post("", response_model=PostResponse)
def create_post(
    req: PostCreate,
    current_user: User = Depends(require_editor),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    # Check plan limit
    BillingService.check_can_publish_post(db, org)

    # Initial status logic
    initial_status = "draft"
    if req.submit_for_approval:
        initial_status = "pending_approval"
    elif org.auto_publish_enabled and req.scheduled_at:
        initial_status = "scheduled"

    post = Post(
        organization_id=org.id,
        client_id=req.client_id,
        author_id=current_user.id,
        title=req.title or "",
        content=req.content,
        target_platforms=req.target_platforms or ["instagram"],
        media_ids=req.media_ids or [],
        scheduled_at=req.scheduled_at,
        timezone=req.timezone or org.timezone,
        status=initial_status,
        auto_publish_without_approval=req.auto_publish_without_approval or False,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    if req.submit_for_approval:
        log = ApprovalLog(
            post_id=post.id,
            user_id=current_user.id,
            action="submitted",
            comments="Submitted directly upon creation",
        )
        db.add(log)
        db.commit()

    return _format_post_response(post, db)


@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    post = (
        db.query(Post)
        .filter(Post.id == post_id, Post.organization_id == org.id)
        .first()
    )
    if not post:
        raise ResourceNotFoundException("Post")
    return _format_post_response(post, db)


@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    req: PostUpdate,
    current_user: User = Depends(require_editor),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    post = (
        db.query(Post)
        .filter(Post.id == post_id, Post.organization_id == org.id)
        .first()
    )
    if not post:
        raise ResourceNotFoundException("Post")

    if post.status == "published":
        raise NuvioException(detail="Cannot edit already published posts.")

    if req.title is not None:
        post.title = req.title
    if req.content is not None:
        post.content = req.content
    if req.target_platforms is not None:
        post.target_platforms = req.target_platforms
    if req.media_ids is not None:
        post.media_ids = req.media_ids
    if req.scheduled_at is not None:
        post.scheduled_at = req.scheduled_at
    if req.timezone is not None:
        post.timezone = req.timezone
    if req.client_id is not None:
        post.client_id = req.client_id
    if req.auto_publish_without_approval is not None:
        post.auto_publish_without_approval = req.auto_publish_without_approval

    db.commit()
    db.refresh(post)
    return _format_post_response(post, db)


@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    current_user: User = Depends(require_editor),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    post = (
        db.query(Post)
        .filter(Post.id == post_id, Post.organization_id == org.id)
        .first()
    )
    if not post:
        raise ResourceNotFoundException("Post")

    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully."}


@router.post("/{post_id}/submit-approval", response_model=PostResponse)
def submit_post_approval(
    post_id: int,
    comments: Optional[str] = Query(""),
    current_user: User = Depends(require_editor),
    db: Session = Depends(get_db),
):
    post = PublisherService.submit_for_approval(db, post_id, current_user, comments)
    return _format_post_response(post, db)


@router.post("/{post_id}/publish-now")
async def publish_post_now(
    post_id: int,
    req: Optional[PublishNowRequest] = None,
    current_user: User = Depends(require_editor),
    db: Session = Depends(get_db),
):
    force = req.force if req else False
    result = await PublisherService.publish_post_now(
        db, post_id, current_user, force=force
    )
    return result


@router.post("/{post_id}/retry")
async def retry_failed_post(
    post_id: int,
    current_user: User = Depends(require_editor),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    post = (
        db.query(Post)
        .filter(Post.id == post_id, Post.organization_id == org.id)
        .first()
    )
    if not post:
        raise ResourceNotFoundException("Post")

    if post.status != "failed":
        raise NuvioException(detail="Only posts in 'failed' status can be retried.")

    result = await PublisherService.publish_post_now(db, post_id, current_user, force=True)
    return result
