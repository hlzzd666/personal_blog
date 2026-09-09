"""create visitor records

Revision ID: 20260909_01
Revises: 20260903_01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260909_01"
down_revision = "20260903_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "visitor_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ip", sa.String(length=64), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("page_path", sa.String(length=2048), nullable=False),
        sa.Column("referer", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("device_type", sa.String(length=32), server_default="desktop", nullable=False),
        sa.Column("visited_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_visitor_records_ip", "visitor_records", ["ip"])
    op.create_index("ix_visitor_records_city", "visitor_records", ["city"])
    op.create_index("ix_visitor_records_visited_at", "visitor_records", ["visited_at"])


def downgrade() -> None:
    op.drop_index("ix_visitor_records_visited_at", table_name="visitor_records")
    op.drop_index("ix_visitor_records_city", table_name="visitor_records")
    op.drop_index("ix_visitor_records_ip", table_name="visitor_records")
    op.drop_table("visitor_records")
