import os
import shutil
import uuid
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.config import settings
from app.core.exceptions import NuvioException, ResourceNotFoundException
from app.db.models import MediaAsset, Organization


class MediaService:
    @staticmethod
    def ensure_upload_dir():
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    @staticmethod
    async def upload_asset(
        db: Session,
        organization_id: int,
        file: UploadFile,
        folder: str = "General",
        tags: str = "",
        client_id: Optional[int] = None,
    ) -> MediaAsset:
        MediaService.ensure_upload_dir()

        # Check content type
        content_type = file.content_type or "application/octet-stream"
        is_image = content_type in settings.ALLOWED_IMAGE_TYPES
        is_video = content_type in settings.ALLOWED_VIDEO_TYPES

        if not (is_image or is_video):
            raise NuvioException(
                detail=f"Unsupported file type '{content_type}'. Allowed types: JPG, PNG, WEBP, GIF, MP4, MOV, WEBM."
            )

        # Generate unique safe filename
        ext = os.path.splitext(file.filename or "")[1].lower()
        if not ext:
            ext = ".jpg" if is_image else ".mp4"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        destination_path = os.path.join(settings.UPLOAD_DIR, unique_name)

        # Save file to disk
        file_size = 0
        with open(destination_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                file_size += len(chunk)
                if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
                    # Remove partial file
                    buffer.close()
                    if os.path.exists(destination_path):
                        os.remove(destination_path)
                    raise NuvioException(
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024):.0f}MB."
                    )
                buffer.write(chunk)

        # Build public URL path
        file_url = f"/static/uploads/{unique_name}"
        media_type = "image" if is_image else "video"
        if "logo" in (file.filename or "").lower() or folder.lower() == "logos":
            media_type = "logo"

        asset = MediaAsset(
            organization_id=organization_id,
            client_id=client_id,
            filename=unique_name,
            original_name=file.filename or unique_name,
            file_path=destination_path,
            file_url=file_url,
            file_size=file_size,
            mime_type=content_type,
            media_type=media_type,
            folder=folder,
            tags=tags,
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset

    @staticmethod
    def delete_asset(db: Session, asset_id: int, organization_id: int) -> bool:
        asset = (
            db.query(MediaAsset)
            .filter(
                MediaAsset.id == asset_id, MediaAsset.organization_id == organization_id
            )
            .first()
        )
        if not asset:
            raise ResourceNotFoundException("MediaAsset")

        # Remove from disk if exists
        if os.path.exists(asset.file_path):
            try:
                os.remove(asset.file_path)
            except OSError:
                pass

        db.delete(asset)
        db.commit()
        return True

