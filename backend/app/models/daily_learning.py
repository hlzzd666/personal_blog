from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class DailyLearningSettings(Base):
    __tablename__ = "daily_learning_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    publish_time: Mapped[time] = mapped_column(Time, default=time(9, 0))
    schedule_type: Mapped[str] = mapped_column(String(20), default="daily", server_default="daily")
    schedule_weekday: Mapped[int | None] = mapped_column(Integer, nullable=True)
    schedule_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_base_url: Mapped[str] = mapped_column(String(2048), default="", server_default="")
    ai_model: Mapped[str] = mapped_column(String(200), default="", server_default="")
    encrypted_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    generation_topic: Mapped[str] = mapped_column(String(200), default="前端面试题", server_default="前端面试题")
    system_prompt: Mapped[str] = mapped_column(Text, default="", server_default="")
    generation_instructions: Mapped[str] = mapped_column(Text, default="")
    generation_count: Mapped[int] = mapped_column(Integer, default=10, server_default="10")
    question_label: Mapped[str] = mapped_column(String(50), default="题目", server_default="题目")
    answer_label: Mapped[str] = mapped_column(String(50), default="参考答案", server_default="参考答案")
    article_title_template: Mapped[str] = mapped_column(
        String(200), default="{date}-学习问答", server_default="{date}-学习问答"
    )
    article_slug_template: Mapped[str] = mapped_column(
        String(160), default="{date}-学习记录", server_default="{date}-学习记录"
    )
    article_summary_template: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(String(100), default="AI自动生成", server_default="AI自动生成")
    series_id: Mapped[int | None] = mapped_column(
        ForeignKey("series.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("article_categories.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    tag_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    retry_delays_minutes: Mapped[list[int]] = mapped_column(JSON, default=lambda: [10, 30])
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )


class DailyLearningRun(Base):
    __tablename__ = "daily_learning_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    article_id: Mapped[int | None] = mapped_column(
        ForeignKey("articles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )
