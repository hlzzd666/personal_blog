from datetime import datetime

from pydantic import BaseModel, Field


class MediaReference(BaseModel):
    source: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)


class MediaFileItem(BaseModel):
    filename: str
    relative_path: str
    url: str
    content_type: str
    media_type: str
    size: int
    modified_at: datetime
    referenced: bool
    references: list[MediaReference] = Field(default_factory=list)


class MediaListResponse(BaseModel):
    items: list[MediaFileItem] = Field(default_factory=list)
    total: int
    used_count: int
    unused_count: int
    total_size: int
    unused_size: int


class MediaCleanupResponse(BaseModel):
    deleted_count: int
    deleted_size: int
    deleted_files: list[str] = Field(default_factory=list)
