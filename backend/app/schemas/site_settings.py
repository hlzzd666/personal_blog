from pydantic import BaseModel, Field, HttpUrl


class QuoteItem(BaseModel):
    author: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1, max_length=120)


class SiteSettings(BaseModel):
    site_subtitle: str = Field(..., min_length=1, max_length=120)
    hero_image_url: HttpUrl
    nav_brand: str = Field(..., min_length=1, max_length=60)
    quotes: list[QuoteItem] = Field(default_factory=list, min_length=1)


class SiteSettingsUpdate(SiteSettings):
    pass
