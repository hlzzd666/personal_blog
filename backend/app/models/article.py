from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
        server_default=func.now(),
    )
    views: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    likes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    category: Mapped[str] = mapped_column(String(80), default="未分类", server_default="未分类")
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("article_categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    series_id: Mapped[int | None] = mapped_column(
        ForeignKey("series.id", ondelete="SET NULL"), nullable=True, index=True
    )
    series_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    tag_links: Mapped[list["ArticleTagLink"]] = relationship(
        back_populates="article", cascade="all, delete-orphan", lazy="selectin"
    )
    category_ref: Mapped["ArticleCategory | None"] = relationship(
        foreign_keys=[category_id], lazy="joined"
    )

    @property
    def tag_ids(self) -> list[int]:
        return [link.tag_id for link in self.tag_links]


class ArticleCategory(Base):
    __tablename__ = "article_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )


class ArticleTag(Base):
    __tablename__ = "article_tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )


class ArticleTagLink(Base):
    __tablename__ = "article_tag_links"

    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("article_tags.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    article: Mapped[Article] = relationship(back_populates="tag_links")
    tag: Mapped[ArticleTag] = relationship(lazy="joined")


class ArticleLikeRecord(Base):
    __tablename__ = "article_like_records"
    __table_args__ = (
        UniqueConstraint("article_id", "visitor_hash", name="uq_article_like_records_article_visitor"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    visitor_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
