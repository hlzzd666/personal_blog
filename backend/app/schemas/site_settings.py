from pydantic import BaseModel, Field, HttpUrl, model_validator


class QuoteItem(BaseModel):
    author: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1, max_length=120)


class SiteSettings(BaseModel):
    site_subtitle: str = Field(..., min_length=1, max_length=120)
    hero_image_url: HttpUrl
    nav_brand: str = Field(..., min_length=1, max_length=60)
    owner_avatar_url: str = Field(default="/owner-avatar.jpg", min_length=1, max_length=2048)
    quotes: list[QuoteItem] = Field(default_factory=list, min_length=1)
    owner_location_name: str = Field(default="未设置站长地址", min_length=1, max_length=80)
    owner_latitude: float | None = Field(default=None, ge=-90, le=90)
    owner_longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def validate_owner_coordinates(self) -> "SiteSettings":
        if (self.owner_latitude is None) != (self.owner_longitude is None):
            raise ValueError("站长经纬度必须同时填写")
        return self


class SiteSettingsUpdate(SiteSettings):
    pass
