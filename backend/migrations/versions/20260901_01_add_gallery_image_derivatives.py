"""add gallery image derivatives

Revision ID: 20260901_01
Revises: 20260831_01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260901_01"
down_revision = "20260831_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("gallery_settings", sa.Column("logo_display_url", sa.String(length=2048), nullable=True))
    op.add_column("gallery_characters", sa.Column("poster_frame_url", sa.String(length=2048), nullable=True))
    op.add_column("gallery_characters", sa.Column("poster_display_url", sa.String(length=2048), nullable=True))


def downgrade() -> None:
    op.drop_column("gallery_characters", "poster_display_url")
    op.drop_column("gallery_characters", "poster_frame_url")
    op.drop_column("gallery_settings", "logo_display_url")
