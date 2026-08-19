"""create articles table

Revision ID: 20260820_01
Revises:
"""

from alembic import op
import sqlalchemy as sa


revision = "20260820_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("cover_image_url", sa.String(length=2048), nullable=True),
        sa.Column("is_repost", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("author", sa.String(length=100), server_default="站长", nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("views", sa.Integer(), server_default="0", nullable=False),
        sa.Column("likes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("category", sa.String(length=80), server_default="未分类", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_articles_slug", "articles", ["slug"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_articles_slug", table_name="articles")
    op.drop_table("articles")
