from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_organization, get_current_user, require_editor
from app.db.models import MediaAsset, Organization, User
from app.db.session import get_db
from app.schemas.media import MediaAssetResponse, MediaFolderResponse
from app.services.media_service import MediaService

router = APIRouter(prefix="/media", tags=["Media Library"])


@router.get("", response_model=List[MediaAssetResponse])
def list_media(
    folder: Optional[str] = Query(None),
    media_type: Optional[str] = Query(None),
    client_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    query = db.query(MediaAsset).filter(MediaAsset.organization_id == org.id)
    if folder:
        query = query.filter(MediaAsset.folder == folder)
    if media_type:
        query = query.filter(MediaAsset.media_type == media_type)
    if client_id is not None:
        query = query.filter(MediaAsset.client_id == client_id)

    return query.order_by(MediaAsset.created_at.desc()).all()


@router.post("/upload", response_model=MediaAssetResponse)
async def upload_media_file(
    file: UploadFile = File(...),
    folder: str = Form("General"),
    tags: str = Form(""),
    client_id: Optional[int] = Form(None),
    current_user: User = Depends(require_editor),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    asset = await MediaService.upload_asset(
        db=db,
        organization_id=org.id,
        file=file,
        folder=folder,
        tags=tags,
        client_id=client_id,
    )
    return asset


@router.delete("/{asset_id}")
def delete_media_file(
    asset_id: int,
    current_user: User = Depends(require_editor),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    MediaService.delete_asset(db, asset_id, org.id)
    return {"message": "Media asset deleted successfully."}


@router.get("/folders", response_model=List[MediaFolderResponse])
def list_folders(
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    assets = db.query(MediaAsset).filter(MediaAsset.organization_id == org.id).all()
    folder_map = {}
    for a in assets:
        f_name = a.folder or "General"
        if f_name not in folder_map:
            folder_map[f_name] = {"count": 0, "size": 0}
        folder_map[f_name]["count"] += 1
        folder_map[f_name]["size"] += a.file_size or 0

    return [
        MediaFolderResponse(
            name=name,
            asset_count=stats["count"],
            total_size_bytes=stats["size"],
        )
        for name, stats in folder_map.items()
    ]

