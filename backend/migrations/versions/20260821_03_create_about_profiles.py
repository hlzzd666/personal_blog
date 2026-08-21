"""create about profiles

Revision ID: 20260821_03
Revises: 20260821_02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260821_03"
down_revision = "20260821_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "about_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("role", sa.String(length=120), nullable=False),
        sa.Column("headline", sa.String(length=160), nullable=False),
        sa.Column("bio", sa.Text(), nullable=False),
        sa.Column("avatar_url", sa.String(length=2048), nullable=False),
        sa.Column("status_text", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=True),
        sa.Column("location_name", sa.String(length=100), nullable=False),
        sa.Column("location_longitude", sa.Float(), nullable=True),
        sa.Column("location_latitude", sa.Float(), nullable=True),
        sa.Column("location_description", sa.String(length=240), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("work_experiences", sa.JSON(), nullable=False),
        sa.Column("project_experiences", sa.JSON(), nullable=False),
        sa.Column("skill_groups", sa.JSON(), nullable=False),
        sa.Column("social_links", sa.JSON(), nullable=False),
        sa.Column("interests", sa.JSON(), nullable=False),
        sa.Column("site_title", sa.String(length=120), nullable=False),
        sa.Column("site_description", sa.Text(), nullable=False),
        sa.Column("site_launched_at", sa.String(length=40), nullable=False),
        sa.Column("site_stack", sa.JSON(), nullable=False),
        sa.Column("site_repository_url", sa.String(length=2048), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("about_profiles")
