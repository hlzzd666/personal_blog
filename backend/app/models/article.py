from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    content_markdown: Mapped[str] = mapped_column(Text)
    cover_image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    is_repost: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    author: Mapped[str] = mapped_column(String(100), default="站长", server_default="站长")
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )
    views: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    likes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    category: Mapped[str] = mapped_column(String(80), default="未分类", server_default="未分类")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
