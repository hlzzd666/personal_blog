"""remove about location description

Revision ID: 20260821_05
Revises: 20260821_04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260821_05"
down_revision = "20260821_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("about_profiles", "location_description")


def downgrade() -> None:
    op.add_column(
        "about_profiles",
        sa.Column("location_description", sa.String(length=240), nullable=False, server_default=""),
    )
    op.alter_column("about_profiles", "location_description", server_default=None)
