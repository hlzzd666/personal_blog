"""create article like records

Revision ID: 20260821_02
Revises: 20260820_01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260821_02"
down_revision = "20260820_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "article_like_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("visitor_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("article_id", "visitor_hash", name="uq_article_like_records_article_visitor"),
    )
    op.create_index("ix_article_like_records_article_id", "article_like_records", ["article_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_article_like_records_article_id", table_name="article_like_records")
    op.drop_table("article_like_records")
