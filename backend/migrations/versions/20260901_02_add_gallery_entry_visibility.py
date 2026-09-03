"""add gallery entry visibility setting

Revision ID: 20260901_02
Revises: 20260901_01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260901_02"
down_revision = "20260901_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "gallery_settings",
        sa.Column("show_entry", sa.Boolean(), server_default=sa.true(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("gallery_settings", "show_entry")
