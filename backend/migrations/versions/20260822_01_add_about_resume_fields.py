"""add about resume fields

Revision ID: 20260822_01
Revises: 20260821_05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260822_01"
down_revision = "20260821_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "about_profiles",
        sa.Column("resume_url", sa.String(length=2048), nullable=False, server_default=""),
    )
    op.add_column(
        "about_profiles",
        sa.Column("resume_filename", sa.String(length=255), nullable=False, server_default=""),
    )
    op.alter_column("about_profiles", "resume_url", server_default=None)
    op.alter_column("about_profiles", "resume_filename", server_default=None)


def downgrade() -> None:
    op.drop_column("about_profiles", "resume_filename")
    op.drop_column("about_profiles", "resume_url")
