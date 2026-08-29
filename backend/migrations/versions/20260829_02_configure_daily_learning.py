"""make daily learning publishing configurable

Revision ID: 20260829_02
Revises: 20260829_01
"""

import json

from alembic import op
import sqlalchemy as sa


revision = "20260829_02"
down_revision = "20260829_01"
branch_labels = None
depends_on = None


DEFAULT_SYSTEM_PROMPT = "你是严谨的资深前端面试官，只输出符合要求的 JSON。"
DEFAULT_INSTRUCTIONS = (
    "题目覆盖 JavaScript、TypeScript、Vue、React、浏览器、CSS、网络、性能和工程化，"
    "兼顾基础、中级和高级难度。答案准确、清晰，必要时给出简短代码示例。"
)


def _json_list(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return []
    return value if isinstance(value, list) else []


def _lookup_or_create(connection, table, name, values=None):
    existing_id = connection.execute(
        sa.select(table.c.id).where(table.c.name == name)
    ).scalar_one_or_none()
    if existing_id is not None:
        return existing_id

    connection.execute(sa.insert(table).values(name=name, **(values or {})))
    return connection.execute(
        sa.select(table.c.id).where(table.c.name == name)
    ).scalar_one()


def upgrade() -> None:
    columns = [
        sa.Column("schedule_type", sa.String(length=20), nullable=True, server_default="daily"),
        sa.Column("schedule_weekday", sa.Integer(), nullable=True),
        sa.Column("schedule_day", sa.Integer(), nullable=True),
        sa.Column("generation_topic", sa.String(length=200), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("generation_count", sa.Integer(), nullable=True),
        sa.Column("question_label", sa.String(length=50), nullable=True),
        sa.Column("answer_label", sa.String(length=50), nullable=True),
        sa.Column("article_title_template", sa.String(length=200), nullable=True),
        sa.Column("article_slug_template", sa.String(length=160), nullable=True),
        sa.Column("article_summary_template", sa.Text(), nullable=True),
        sa.Column("author", sa.String(length=100), nullable=True),
        sa.Column("series_id", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("tag_ids", sa.JSON(), nullable=True),
        sa.Column("max_attempts", sa.Integer(), nullable=True),
        sa.Column("retry_delays_minutes", sa.JSON(), nullable=True),
    ]
    for column in columns:
        op.add_column("daily_learning_settings", column)

    connection = op.get_bind()
    settings = sa.table(
        "daily_learning_settings",
        sa.column("id", sa.Integer),
        sa.column("generation_instructions", sa.Text),
        sa.column("tags", sa.JSON),
        sa.column("schedule_type", sa.String),
        sa.column("generation_topic", sa.String),
        sa.column("system_prompt", sa.Text),
        sa.column("generation_count", sa.Integer),
        sa.column("question_label", sa.String),
        sa.column("answer_label", sa.String),
        sa.column("article_title_template", sa.String),
        sa.column("article_slug_template", sa.String),
        sa.column("article_summary_template", sa.Text),
        sa.column("author", sa.String),
        sa.column("series_id", sa.Integer),
        sa.column("category_id", sa.Integer),
        sa.column("tag_ids", sa.JSON),
        sa.column("max_attempts", sa.Integer),
        sa.column("retry_delays_minutes", sa.JSON),
    )
    categories = sa.table(
        "article_categories", sa.column("id", sa.Integer), sa.column("name", sa.String)
    )
    tags = sa.table("article_tags", sa.column("id", sa.Integer), sa.column("name", sa.String))
    series = sa.table(
        "series",
        sa.column("id", sa.Integer),
        sa.column("slug", sa.String),
        sa.column("title", sa.String),
        sa.column("description", sa.Text),
        sa.column("sort_order", sa.Integer),
    )

    row = connection.execute(
        sa.select(settings.c.generation_instructions, settings.c.tags)
        .where(settings.c.id == 1)
    ).mappings().first()
    old_tags = _json_list(row["tags"] if row else None)
    tag_names = list(dict.fromkeys(str(tag).strip() for tag in old_tags if str(tag).strip()))
    category_id = _lookup_or_create(connection, categories, "每日问答")
    tag_ids = [
        _lookup_or_create(connection, tags, tag_name)
        for tag_name in tag_names
    ]

    daily_series_id = connection.execute(
        sa.select(series.c.id).where(series.c.slug == "daily-learning")
    ).scalar_one_or_none()
    if daily_series_id is None:
        connection.execute(
            sa.insert(series).values(
                slug="daily-learning",
                title="今日份学习",
                description="自动生成的学习问答内容。",
                sort_order=2,
            )
        )
        daily_series_id = connection.execute(
            sa.select(series.c.id).where(series.c.slug == "daily-learning")
        ).scalar_one()

    connection.execute(
        sa.update(settings)
        .where(settings.c.id == 1)
        .values(
            schedule_type="daily",
            generation_topic="前端面试题",
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            generation_instructions=(row["generation_instructions"] if row else None)
            or DEFAULT_INSTRUCTIONS,
            generation_count=10,
            question_label="题目",
            answer_label="参考答案",
            article_title_template="{date}-学习问答",
            article_slug_template="{date}-学习记录",
            article_summary_template="{date} 前端面试学习问答，包含 10 道题目与参考答案。",
            author="AI自动生成",
            series_id=daily_series_id,
            category_id=category_id,
            tag_ids=tag_ids,
            max_attempts=3,
            retry_delays_minutes=[10, 30],
        )
    )
    op.create_index(op.f("ix_daily_learning_settings_series_id"), "daily_learning_settings", ["series_id"], unique=False)
    op.create_index(op.f("ix_daily_learning_settings_category_id"), "daily_learning_settings", ["category_id"], unique=False)
    op.create_foreign_key(
        "fk_daily_learning_settings_series_id_series",
        "daily_learning_settings",
        "series",
        ["series_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_daily_learning_settings_category_id_article_categories",
        "daily_learning_settings",
        "article_categories",
        ["category_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_daily_learning_settings_category_id_article_categories",
        "daily_learning_settings",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_daily_learning_settings_series_id_series",
        "daily_learning_settings",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_daily_learning_settings_category_id"), table_name="daily_learning_settings")
    op.drop_index(op.f("ix_daily_learning_settings_series_id"), table_name="daily_learning_settings")
    for name in (
        "retry_delays_minutes",
        "max_attempts",
        "tag_ids",
        "category_id",
        "series_id",
        "author",
        "article_summary_template",
        "article_slug_template",
        "article_title_template",
        "answer_label",
        "question_label",
        "generation_count",
        "system_prompt",
        "generation_topic",
        "schedule_day",
        "schedule_weekday",
        "schedule_type",
    ):
        op.drop_column("daily_learning_settings", name)
