from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DailyLearningSettingsUpdate(BaseModel):
    enabled: bool = False
    publish_time: time = time(9, 0)
    schedule_type: Literal["daily", "weekly", "monthly"] | None = None
    schedule_weekday: int | None = Field(default=None, ge=1, le=7)
    schedule_day: int | None = Field(default=None, ge=1, le=31)
    ai_base_url: str = Field(default="", max_length=2048)
    ai_model: str = Field(default="", max_length=200)
    api_key: str | None = Field(default=None, max_length=4096)
    generation_topic: str | None = Field(default=None, max_length=200)
    system_prompt: str | None = Field(default=None, max_length=5000)
    generation_instructions: str | None = Field(default=None, max_length=5000)
    generation_count: int | None = Field(default=None, ge=1, le=20)
    question_label: str | None = Field(default=None, max_length=50)
    answer_label: str | None = Field(default=None, max_length=50)
    article_title_template: str | None = Field(default=None, max_length=200)
    article_slug_template: str | None = Field(default=None, max_length=160)
    article_summary_template: str | None = Field(default=None, max_length=5000)
    author: str | None = Field(default=None, max_length=100)
    series_id: int | None = Field(default=None, ge=1)
    category_id: int | None = Field(default=None, ge=1)
    tag_ids: list[int] | None = Field(default=None, max_length=20)
    tags: list[str] | None = Field(default=None, max_length=20)
    max_attempts: int | None = Field(default=None, ge=1, le=10)
    retry_delays_minutes: list[int] | None = Field(default=None, max_length=9)

    @field_validator(
        "ai_base_url",
        "ai_model",
        "generation_topic",
        "system_prompt",
        "generation_instructions",
        "question_label",
        "answer_label",
        "article_title_template",
        "article_slug_template",
        "article_summary_template",
        "author",
    )
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        tags = list(dict.fromkeys(tag.strip() for tag in value if tag.strip()))
        if any(len(tag) > 30 for tag in tags):
            raise ValueError("单个文章标签不能超过 30 个字符")
        return tags

    @field_validator("tag_ids")
    @classmethod
    def normalize_tag_ids(cls, value: list[int] | None) -> list[int] | None:
        return list(dict.fromkeys(value)) if value is not None else None

    @field_validator("retry_delays_minutes")
    @classmethod
    def validate_retry_delays(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        if any(delay < 1 or delay > 1440 for delay in value):
            raise ValueError("重试间隔必须在 1 至 1440 分钟之间")
        return value


class DailyLearningSettingsResponse(BaseModel):
    enabled: bool
    publish_time: time
    schedule_type: Literal["daily", "weekly", "monthly"]
    schedule_weekday: int | None
    schedule_day: int | None
    ai_base_url: str
    ai_model: str
    api_key_configured: bool
    generation_topic: str
    system_prompt: str
    generation_instructions: str
    generation_count: int
    question_label: str
    answer_label: str
    article_title_template: str
    article_slug_template: str
    article_summary_template: str
    author: str
    series_id: int | None
    series_title: str | None
    category_id: int | None
    category: str | None
    tag_ids: list[int]
    tags: list[str]
    max_attempts: int
    retry_delays_minutes: list[int]
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

    questions: list[GeneratedQuestion] = Field(..., min_length=1, max_length=20)
