from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class QuoteItem(BaseModel):
    author: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1, max_length=120)


class SiteVisualAsset(BaseModel):
    key: str = Field(..., min_length=1, max_length=60, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(..., min_length=1, max_length=80)
    usage: Literal["background"] = "background"
    image_url: str = Field(default="", max_length=2048)
    enabled: bool = True
    opacity: float = Field(default=0.32, ge=0, le=1)
    note: str = Field(default="", max_length=160)

    @field_validator("usage", mode="before")
    @classmethod
    def normalize_usage(cls, value: object) -> str:
        return "background"


class SiteSettings(BaseModel):
    site_subtitle: str = Field(..., min_length=1, max_length=120)
    hero_image_url: HttpUrl
    nav_brand: str = Field(..., min_length=1, max_length=60)
    site_launched_on: date = Field(default=date(2026, 1, 1))
    owner_avatar_url: str = Field(default="/owner-avatar.jpg", min_length=1, max_length=2048)
    quotes: list[QuoteItem] = Field(default_factory=list, min_length=1)
    visual_assets: list[SiteVisualAsset] = Field(default_factory=list)
    owner_location_name: str = Field(default="未设置站长地址", min_length=1, max_length=80)
    owner_latitude: float | None = Field(default=None, ge=-90, le=90)
    owner_longitude: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("site_launched_on")
    @classmethod
    def validate_site_launched_on(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("建站日期不能晚于今天")
        return value

    @model_validator(mode="after")
    def validate_owner_coordinates(self) -> "SiteSettings":
        if (self.owner_latitude is None) != (self.owner_longitude is None):
            raise ValueError("站长经纬度必须同时填写")
        return self


class SiteSettingsUpdate(SiteSettings):
    pass
