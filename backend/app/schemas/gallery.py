from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class GallerySettingsPayload(BaseModel):
    hall_name: str = Field(..., min_length=1, max_length=120)
    entry_title: str = Field(..., min_length=1, max_length=200)
    show_entry: bool = True
    show_logo: bool = False
    logo_url: str | None = Field(default=None, max_length=2048)

    @field_validator("hall_name", "entry_title")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("不能为空")
        return normalized

    @field_validator("logo_url")
    @classmethod
    def normalize_logo_url(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class GallerySettingsResponse(GallerySettingsPayload):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GalleryChapterPayload(BaseModel):
    title: str = Field(..., min_length=1, max_length=80)
    subtitle: str = Field(default="", max_length=200)
    heading: str = Field(default="", max_length=200)
    description: str = Field(default="", max_length=500)
    note: str = Field(default="", max_length=300)
    label: str = Field(default="", max_length=120)
    story: str = Field(default="", max_length=5000)
    artwork_index: int = Field(default=0, ge=0, le=3)
    is_visible: bool = True

    @field_validator("title")
    @classmethod
    def normalize_chapter_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("不能为空")
        return normalized

    @field_validator("subtitle", "heading", "description", "note", "label", "story")
    @classmethod
    def trim_chapter_text(cls, value: str) -> str:
        return value.strip()


class GalleryChapterResponse(GalleryChapterPayload):
    id: int
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GalleryChapterOrderPayload(BaseModel):
    chapter_ids: list[int] = Field(..., max_length=20)

    @field_validator("chapter_ids")
    @classmethod
    def validate_chapter_ids(cls, value: list[int]) -> list[int]:
        if any(item < 1 for item in value) or len(value) != len(set(value)):
            raise ValueError("分类排序必须使用有效且不重复的分类编号")
        return value


class GalleryCharacterPayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    epithet: str = Field(..., min_length=1, max_length=120)
    faction: str = Field(..., min_length=1, max_length=120)
    bounty: str = Field(..., min_length=1, max_length=120)
    ability: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1, max_length=5000)
    quote: str = Field(..., min_length=1, max_length=500)
    poster_url: str | None = Field(default=None, max_length=2048)
    chapter_id: int | None = Field(default=None, ge=1)
    is_visible: bool = False

    @field_validator(
        "name", "epithet", "faction", "bounty", "ability", "description", "quote"
    )
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("不能为空")
        return normalized

    @field_validator("poster_url")
    @classmethod
    def normalize_poster_url(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class GalleryCharacterResponse(GalleryCharacterPayload):
    id: int
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GalleryResponse(BaseModel):
    settings: GallerySettingsResponse
    chapters: list[GalleryChapterResponse]
    characters: list[GalleryCharacterResponse]


class GalleryCharacterOrderPayload(BaseModel):
    character_ids: list[int] = Field(..., max_length=40)

    @field_validator("character_ids")
    @classmethod
    def validate_unique_ids(cls, value: list[int]) -> list[int]:
        if len(value) != len(set(value)):
            raise ValueError("人物排序不能包含重复项")
        return value


class GalleryImageUploadResult(BaseModel):
    url: str
