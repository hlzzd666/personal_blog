from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DailyLearningSettingsUpdate(BaseModel):
    enabled: bool = False
    publish_time: time = time(9, 0)
    ai_base_url: str = Field(default="", max_length=2048)
    ai_model: str = Field(default="", max_length=200)
    api_key: str | None = Field(default=None, max_length=4096)
    generation_instructions: str = Field(default="", max_length=5000)
    tags: list[str] = Field(default_factory=lambda: ["前端面试", "每日问答"], min_length=1, max_length=20)

    @field_validator("ai_base_url", "ai_model", "generation_instructions")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        tags = list(dict.fromkeys(tag.strip() for tag in value if tag.strip()))
        if not tags:
            raise ValueError("请至少配置一个文章标签")
        if any(len(tag) > 30 for tag in tags):
            raise ValueError("单个文章标签不能超过 30 个字符")
        return tags


class DailyLearningSettingsResponse(BaseModel):
    enabled: bool
    publish_time: time
    ai_base_url: str
    ai_model: str
    api_key_configured: bool
    generation_instructions: str
    tags: list[str]
    timezone: str = "Asia/Shanghai"
    updated_at: datetime


class DailyLearningRunResponse(BaseModel):
    id: int
    run_date: date
    scheduled_for: datetime
    status: Literal["pending", "running", "succeeded", "failed"]
    attempt_count: int
    last_error: str | None
    next_retry_at: datetime | None
    article_id: int | None
    article_slug: str | None = None
    article_title: str | None = None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DailyLearningRunListResponse(BaseModel):
    items: list[DailyLearningRunResponse]
    total: int


class DailyLearningTestResponse(BaseModel):
    ok: bool
    model: str
    question_count: int
    first_question: str
    latency_ms: int


class GeneratedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=3, max_length=500)
    answer: str = Field(..., min_length=10, max_length=8000)

    @field_validator("question", "answer")
    @classmethod
    def strip_content(cls, value: str) -> str:
        return value.strip()


class GeneratedQuestionSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questions: list[GeneratedQuestion] = Field(..., min_length=10, max_length=10)
