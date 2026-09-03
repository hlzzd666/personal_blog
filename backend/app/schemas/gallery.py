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


class GalleryCharacterPayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    epithet: str = Field(..., min_length=1, max_length=120)
    faction: str = Field(..., min_length=1, max_length=120)
    bounty: str = Field(..., min_length=1, max_length=120)
    ability: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1, max_length=5000)
    quote: str = Field(..., min_length=1, max_length=500)
    poster_url: str | None = Field(default=None, max_length=2048)
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
