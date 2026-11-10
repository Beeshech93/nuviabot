from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class MediaAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    client_id: Optional[int] = None
    filename: str
    original_name: str
    file_path: str
    file_url: str
    file_size: int
    mime_type: str
    media_type: str  # image, video, logo, thumbnail
    folder: str
    tags: Optional[str] = ""
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime


class MediaFolderResponse(BaseModel):
    name: str
    asset_count: int
    total_size_bytes: int


class MediaUpdateRequest(BaseModel):
    folder: Optional[str] = None
    tags: Optional[str] = None
