from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, field_validator


class ArticlePayload(BaseModel):
    slug: str = Field(..., min_length=1, max_length=160)
    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(default="", max_length=500)
    content_markdown: str = Field(..., min_length=1)
    cover_image_url: str | None = Field(default=None, max_length=2048)
    is_repost: bool = False
    author: str = Field(default="站长", min_length=1, max_length=100)
    source_url: HttpUrl | None = None
    published_at: datetime | None = None
    updated_at: datetime | None = None
    views: int = Field(default=0, ge=0)
    likes: int = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list, max_length=20)
    category: str = Field(default="未分类", min_length=1, max_length=80)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(tag.strip() for tag in value if tag.strip()))


class ArticleCreate(ArticlePayload):
    pass


class ArticleUpdate(ArticlePayload):
    pass


class ArticleResponse(ArticlePayload):
    id: int
    created_at: datetime
    updated_at: datetime
    liked_by_current_visitor: bool = False

    model_config = {"from_attributes": True}


class ArticleListResponse(BaseModel):
    items: list[ArticleResponse]
    total: int
    page: int
    page_size: int


class ArticleLikeResponse(BaseModel):
    likes: int
    liked_by_current_visitor: bool
