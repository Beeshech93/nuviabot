from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.exceptions import NuvioException, PermissionDeniedException, ResourceNotFoundException
from app.core.security import decrypt_token
from app.db.models import ApprovalLog, MediaAsset, Organization, Post, SocialAccount, User
from app.services.social import get_social_adapter


class PublisherService:
    """Handles publication lifecycle, human approval verification, scheduling, and multi-network dispatch."""

    VALID_TRANSITIONS = {
        "draft": ["pending_approval", "approved", "scheduled"],
        "pending_approval": ["approved", "rejected", "draft"],
        "approved": ["scheduled", "publishing", "draft"],
        "scheduled": ["publishing", "draft", "pending_approval"],
        "publishing": ["published", "failed"],
        "failed": ["scheduled", "publishing", "draft"],
        "rejected": ["draft", "pending_approval"],
        "published": [],
    }

    @staticmethod
    def submit_for_approval(db: Session, post_id: int, user: User, comments: str = "") -> Post:
        post = (
            db.query(Post)
            .filter(Post.id == post_id, Post.organization_id == user.organization_id)
            .first()
        )
        if not post:
            raise ResourceNotFoundException("Post")

        if post.status not in ["draft", "rejected"]:
            raise NuvioException(detail=f"Cannot submit post in '{post.status}' status for approval")

        post.status = "pending_approval"
        post.rejection_reason = ""

        # Record in approval log
        log = ApprovalLog(
            post_id=post.id,
            user_id=user.id,
            action="submitted",
            comments=comments or "Submitted for human approval",
        )
        db.add(log)
        db.commit()
        db.refresh(post)
        return post

    @staticmethod
    def review_post(
        db: Session,
        post_id: int,
        reviewer: User,
        action: str,  # "approved" or "rejected"
        comments: str = "",
    ) -> Post:
        if reviewer.role not in ["super_admin", "agency_admin", "client_admin"]:
            raise PermissionDeniedException(
                "Only administrators can review and approve/reject publications"
            )

        post = (
            db.query(Post)
            .filter(Post.id == post_id, Post.organization_id == reviewer.organization_id)
            .first()
        )
        if not post:
            raise ResourceNotFoundException("Post")

        if post.status != "pending_approval":
            raise NuvioException(detail=f"Post is in '{post.status}' state, not pending approval")

        if action == "approved":
            # If scheduled_at is in the future, set to scheduled, otherwise approved
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if post.scheduled_at and post.scheduled_at > now:
                post.status = "scheduled"
            else:
                post.status = "approved"
            post.rejection_reason = ""
        elif action == "rejected":
            post.status = "rejected"
            post.rejection_reason = comments or "Rejected by reviewer"
        else:
            raise NuvioException(detail="Review action must be 'approved' or 'rejected'")

        log = ApprovalLog(
            post_id=post.id,
            user_id=reviewer.id,
            action=action,
            comments=comments,
        )
        db.add(log)
        db.commit()
        db.refresh(post)
        return post

    @staticmethod
    async def publish_post_now(
        db: Session,
        post_id: int,
        user: User,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Publishes post immediately after verifying human approval requirements."""
        post = (
            db.query(Post)
            .filter(Post.id == post_id, Post.organization_id == user.organization_id)
            .first()
        )
        if not post:
            raise ResourceNotFoundException("Post")

        org = (
            db.query(Organization).filter(Organization.id == user.organization_id).first()
        )

        # STRICT HUMAN APPROVAL CHECK
        # Must be approved, unless organization explicitly has auto_publish_enabled or user is admin forcing
        is_admin = user.role in ["super_admin", "agency_admin", "client_admin"]
        bypass_allowed = (
            org.auto_publish_enabled or post.auto_publish_without_approval or (force and is_admin)
        )

        if post.status not in ["approved", "scheduled", "failed"] and not bypass_allowed:
            raise PermissionDeniedException(
                "Human approval is mandatory before publishing. Post must be reviewed and approved."
            )

        post.status = "publishing"
        db.commit()

        # Collect media URLs if any
        media_urls = []
        if post.media_ids:
            media_items = (
                db.query(MediaAsset).filter(MediaAsset.id.in_(post.media_ids)).all()
            )
            media_urls = [m.file_url for m in media_items]

        target_platforms = post.target_platforms or []
        if not target_platforms:
            post.status = "failed"
            post.publish_errors = {"general": "No target platforms selected."}
            db.commit()
            return {"success": False, "detail": "No target platforms specified"}

        # Query connected social accounts for this organization
        accounts_query = db.query(SocialAccount).filter(
            SocialAccount.organization_id == user.organization_id,
            SocialAccount.platform.in_(target_platforms),
            SocialAccount.status == "connected",
        )
        if post.client_id:
            accounts_query = accounts_query.filter(
                SocialAccount.client_id == post.client_id
            )

        accounts = accounts_query.all()
        account_map = {acc.platform: acc for acc in accounts}

        platform_post_ids = dict(post.platform_post_ids or {})
        publish_errors = dict(post.publish_errors or {})
        success_count = 0

        for platform in target_platforms:
            account = account_map.get(platform)
            if not account:
                publish_errors[platform] = f"No active connected account found for {platform}."
                continue

            try:
                adapter = get_social_adapter(platform)
                decrypted_token = decrypt_token(account.encrypted_access_token)

                result = await adapter.publish_content(
                    access_token=decrypted_token,
                    account_id=account.platform_account_id,
                    content=post.content,
                    media_urls=media_urls,
                    title=post.title,
                )

                if result.get("success"):
                    platform_post_ids[platform] = result.get("post_id", "pub_ok")
                    publish_errors.pop(platform, None)
                    success_count += 1
                else:
                    publish_errors[platform] = result.get("error", "Unknown publishing error")
            except Exception as e:
                publish_errors[platform] = str(e)

        post.platform_post_ids = platform_post_ids
        post.publish_errors = publish_errors

        if success_count > 0:
            post.status = "published"
            post.published_at = datetime.now(timezone.utc)
            if org:
                org.posts_published_this_month = (org.posts_published_this_month or 0) + 1
        else:
            post.status = "failed"
            post.retry_count = (post.retry_count or 0) + 1

        db.commit()
        db.refresh(post)

        return {
            "success": success_count > 0,
            "status": post.status,
            "platform_post_ids": post.platform_post_ids,
            "publish_errors": post.publish_errors,
        }

    @staticmethod
    async def process_scheduled_queue(db: Session) -> int:
        """Background scheduler processor: Dispatches posts whose scheduled_at time has arrived."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        due_posts = (
            db.query(Post)
            .filter(
                Post.status == "scheduled",
                Post.scheduled_at <= now,
            )
            .all()
        )

        processed = 0
        for post in due_posts:
            # Fetch author or org admin to run publication
            user = (
                db.query(User)
                .filter(User.id == post.author_id)
                .first()
            )
            if not user:
                continue

            try:
                await PublisherService.publish_post_now(db, post.id, user, force=True)
                processed += 1
            except Exception as e:
                post.status = "failed"
                post.publish_errors = {"scheduler_error": str(e)}
                db.commit()

        return processed
