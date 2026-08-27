"""add daily learning settings and runs

Revision ID: 20260827_01
Revises: 20260825_01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260827_01"
down_revision = "20260825_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "daily_learning_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("publish_time", sa.Time(), nullable=False, server_default="09:00:00"),
        sa.Column("ai_base_url", sa.String(length=2048), nullable=False, server_default=""),
        sa.Column("ai_model", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("encrypted_api_key", sa.Text(), nullable=True),
        sa.Column("generation_instructions", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "daily_learning_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_date", sa.Date(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(), nullable=True),
        sa.Column("article_id", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["article_id"], ["articles.id"], name="fk_daily_learning_runs_article_id_articles", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_date"),
    )
    op.create_index(
        op.f("ix_daily_learning_runs_article_id"),
        "daily_learning_runs",
        ["article_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_daily_learning_runs_run_date"),
        "daily_learning_runs",
        ["run_date"],
        unique=True,
    )
    op.execute(
        sa.text(
            "INSERT INTO daily_learning_settings "
            "(id, enabled, publish_time, ai_base_url, ai_model, generation_instructions) "
            "VALUES (1, 0, '09:00:00', '', '', '')"
        )
    )


def downgrade() -> None:
    op.drop_table("daily_learning_runs")
    op.drop_table("daily_learning_settings")
