"""add guestbook messages

Revision ID: 20260913_01
Revises: 20260909_01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260913_01"
down_revision = "20260909_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "guestbook_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nickname", sa.String(length=40), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("visitor_hash", sa.String(length=64), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("risk_score", sa.Integer(), server_default="0", nullable=False),
        # MySQL does not allow defaults on TEXT columns; the service supplies
        # an empty reply when a message is created.
        sa.Column("admin_reply", sa.Text(), nullable=False),
        sa.Column("admin_note", sa.String(length=500), server_default="", nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("status in ('pending', 'approved', 'rejected', 'spam', 'deleted')", name="ck_guestbook_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_guestbook_messages_status", "guestbook_messages", ["status"])
    op.create_index("ix_guestbook_messages_visitor_hash", "guestbook_messages", ["visitor_hash"])
    op.create_index("ix_guestbook_messages_content_hash", "guestbook_messages", ["content_hash"])
    op.create_index("ix_guestbook_messages_created_at", "guestbook_messages", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_guestbook_messages_created_at", table_name="guestbook_messages")
    op.drop_index("ix_guestbook_messages_content_hash", table_name="guestbook_messages")
    op.drop_index("ix_guestbook_messages_visitor_hash", table_name="guestbook_messages")
    op.drop_index("ix_guestbook_messages_status", table_name="guestbook_messages")
    op.drop_table("guestbook_messages")
