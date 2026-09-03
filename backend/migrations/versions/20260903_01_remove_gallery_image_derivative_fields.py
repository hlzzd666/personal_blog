"""remove duplicate gallery image fields

Revision ID: 20260903_01
Revises: 20260901_02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260903_01"
down_revision = "20260901_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 展示字段优先级高于旧主字段，确保历史上传继续使用已经处理好的图片。
    op.execute(
        sa.text(
            "UPDATE gallery_settings "
            "SET logo_url = COALESCE(logo_display_url, logo_url) "
            "WHERE logo_display_url IS NOT NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE gallery_characters "
            "SET poster_url = COALESCE(poster_display_url, poster_frame_url, poster_url) "
            "WHERE poster_display_url IS NOT NULL OR poster_frame_url IS NOT NULL"
        )
    )
    op.drop_column("gallery_characters", "poster_display_url")
    op.drop_column("gallery_characters", "poster_frame_url")
    op.drop_column("gallery_settings", "logo_display_url")


def downgrade() -> None:
    op.add_column("gallery_settings", sa.Column("logo_display_url", sa.String(length=2048), nullable=True))
    op.add_column("gallery_characters", sa.Column("poster_frame_url", sa.String(length=2048), nullable=True))
    op.add_column("gallery_characters", sa.Column("poster_display_url", sa.String(length=2048), nullable=True))
    op.execute(sa.text("UPDATE gallery_settings SET logo_display_url = logo_url WHERE logo_url IS NOT NULL"))
    op.execute(sa.text("UPDATE gallery_characters SET poster_frame_url = poster_url, poster_display_url = poster_url WHERE poster_url IS NOT NULL"))
