from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TaxonomyPayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    sort_order: int = Field(default=0, ge=0, le=100000)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("名称不能为空")
        return value


class TaxonomyItem(TaxonomyPayload):
    id: int
    article_count: int = 0
    created_at: datetime
    updated_at: datetime


class TaxonomyListResponse(BaseModel):
    items: list[TaxonomyItem] = Field(default_factory=list)
    total: int = 0


class ArticleTaxonomyResponse(BaseModel):
    categories: list[TaxonomyItem] = Field(default_factory=list)
    tags: list[TaxonomyItem] = Field(default_factory=list)
