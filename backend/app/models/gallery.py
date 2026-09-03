from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class GallerySettings(Base):
    __tablename__ = "gallery_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    hall_name: Mapped[str] = mapped_column(String(120))
    entry_title: Mapped[str] = mapped_column(String(200))
    show_entry: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    show_logo: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    logo_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )


class GalleryCharacter(Base):
    __tablename__ = "gallery_characters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80))
    epithet: Mapped[str] = mapped_column(String(120))
    faction: Mapped[str] = mapped_column(String(120))
    bounty: Mapped[str] = mapped_column(String(120))
    ability: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    quote: Mapped[str] = mapped_column(String(500))
    poster_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )
