"""add series and notes

Revision ID: 20260825_01
Revises: 20260822_01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260825_01"
down_revision = "20260822_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "series",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("cover_image_url", sa.String(length=2048), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_series_slug"), "series", ["slug"], unique=True)
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("external_url", sa.String(length=2048), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_notes_slug"), "notes", ["slug"], unique=True)
    op.add_column("articles", sa.Column("series_id", sa.Integer(), nullable=True))
    op.add_column("articles", sa.Column("series_order", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_articles_series_id"), "articles", ["series_id"], unique=False)
    op.create_foreign_key(
        "fk_articles_series_id_series",
        "articles",
        "series",
        ["series_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_articles_series_id_series", "articles", type_="foreignkey")
    op.drop_index(op.f("ix_articles_series_id"), table_name="articles")
    op.drop_column("articles", "series_order")
    op.drop_column("articles", "series_id")
    op.drop_index(op.f("ix_notes_slug"), table_name="notes")
    op.drop_table("notes")
    op.drop_index(op.f("ix_series_slug"), table_name="series")
    op.drop_table("series")
