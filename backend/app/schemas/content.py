from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator

from .article import ArticleResponse


class SeriesPayload(BaseModel):
    slug: str = Field(..., min_length=1, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    cover_image_url: str | None = Field(default=None, max_length=2048)
    sort_order: int = Field(default=0, ge=0, le=100000)


class SeriesResponse(SeriesPayload):
    id: int
    article_count: int = 0
    created_at: datetime
    updated_at: datetime


class SeriesDetailResponse(SeriesResponse):
    articles: list[ArticleResponse] = Field(default_factory=list)


class SeriesListResponse(BaseModel):
    items: list[SeriesResponse]
    total: int


class NotePayload(BaseModel):
    slug: str = Field(..., min_length=1, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    content_markdown: str = Field(..., min_length=1, max_length=50000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    external_url: HttpUrl | None = None
    published_at: datetime | None = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(tag.strip() for tag in value if tag.strip()))


class NoteResponse(NotePayload):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    items: list[NoteResponse]
    total: int
    page: int
    page_size: int


class DashboardStatsResponse(BaseModel):
    article_count: int
    series_count: int
    note_count: int
    total_views: int
    total_likes: int
    top_articles: list[ArticleResponse]
    recent_articles: list[ArticleResponse]
