"""add configurable daily learning tags

Revision ID: 20260827_02
Revises: 20260827_01
"""

import json

from alembic import op
import sqlalchemy as sa


revision = "20260827_02"
down_revision = "20260827_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("daily_learning_settings", sa.Column("tags", sa.JSON(), nullable=True))
    op.execute(
        sa.text("UPDATE daily_learning_settings SET tags = :tags WHERE tags IS NULL").bindparams(
            tags=json.dumps(["前端面试", "每日问答"], ensure_ascii=False)
        )
    )
    op.alter_column(
        "daily_learning_settings",
        "tags",
        existing_type=sa.JSON(),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("daily_learning_settings", "tags")
