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
    series_id: int | None = Field(default=None, ge=1)
    series_order: int | None = Field(default=None, ge=0, le=100000)

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


class ArticleCountItem(BaseModel):
    name: str
    count: int


class ArticleMonthCount(BaseModel):
    key: str
    count: int


class ArticleListStats(BaseModel):
    categories: list[ArticleCountItem] = Field(default_factory=list)
    tags: list[ArticleCountItem] = Field(default_factory=list)
    months: list[ArticleMonthCount] = Field(default_factory=list)


class ArticleListResponse(BaseModel):
    items: list[ArticleResponse]
    total: int
    page: int
    page_size: int
    stats: ArticleListStats = Field(default_factory=ArticleListStats)


class ArticleLikeResponse(BaseModel):
    likes: int
    liked_by_current_visitor: bool


class ArticleSummary(BaseModel):
    id: int
    slug: str
    title: str
    summary: str
    cover_image_url: str | None
    published_at: datetime | None
    created_at: datetime
    category: str
    tags: list[str]

    model_config = {"from_attributes": True}


class ArticleSeriesSummary(BaseModel):
    id: int
    slug: str
    title: str


class ArticleContextResponse(BaseModel):
    previous: ArticleSummary | None = None
    next: ArticleSummary | None = None
    related: list[ArticleSummary] = Field(default_factory=list)
    series: ArticleSeriesSummary | None = None
