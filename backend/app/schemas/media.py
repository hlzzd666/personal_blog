from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MediaReference(BaseModel):
    source: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)


class MediaFileItem(BaseModel):
    storage: Literal["local", "oss"] = "local"
    cleanup_eligible: bool = True
    filename: str
    relative_path: str
    url: str
    content_type: str
    media_type: str
    size: int | None
    modified_at: datetime | None
    referenced: bool
    references: list[MediaReference] = Field(default_factory=list)


class MediaListResponse(BaseModel):
    warnings: list[str] = Field(default_factory=list)
    oss_complete: bool = True
    upload_storage: Literal["local", "oss"] = "local"
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
