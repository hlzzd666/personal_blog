from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AboutProfile(Base):
    __tablename__ = "about_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    display_name: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(120))
    headline: Mapped[str] = mapped_column(String(160))
    bio: Mapped[str] = mapped_column(Text)
    avatar_url: Mapped[str] = mapped_column(String(2048))
    status_text: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    location_name: Mapped[str] = mapped_column(String(100))
    location_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    metrics: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    work_experiences: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    project_experiences: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    skills: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    social_links: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    interests: Mapped[list[str]] = mapped_column(JSON, default=list)
    site_title: Mapped[str] = mapped_column(String(120))
    site_description: Mapped[str] = mapped_column(Text)
    site_launched_at: Mapped[str] = mapped_column(String(40))
    site_stack: Mapped[list[str]] = mapped_column(JSON, default=list)
    site_repository_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )
