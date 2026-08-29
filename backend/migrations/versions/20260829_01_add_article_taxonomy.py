"""add article categories and tags

Revision ID: 20260829_01
Revises: 20260827_02
"""

import json

from alembic import op
import sqlalchemy as sa


revision = "20260829_01"
down_revision = "20260827_02"
branch_labels = None
depends_on = None


def _tag_values(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            value = []
    return value if isinstance(value, list) else []


def _lookup_or_create(connection, table, name):
    """Use the database collation for deduplication (for example, Vue/vue)."""
    existing_id = connection.execute(
        sa.select(table.c.id).where(table.c.name == name)
    ).scalar_one_or_none()
    if existing_id is not None:
        return existing_id

    connection.execute(sa.insert(table).values(name=name))
    return connection.execute(
        sa.select(table.c.id).where(table.c.name == name)
    ).scalar_one()


def upgrade() -> None:
    op.create_table(
        "article_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_article_categories_name"), "article_categories", ["name"], unique=True)
    op.create_table(
        "article_tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_article_tags_name"), "article_tags", ["name"], unique=True)
    op.create_table(
        "article_tag_links",
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["article_tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("article_id", "tag_id"),
    )
    op.create_index(op.f("ix_article_tag_links_tag_id"), "article_tag_links", ["tag_id"], unique=False)
    op.add_column("articles", sa.Column("category_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_articles_category_id"), "articles", ["category_id"], unique=False)
    op.create_foreign_key(
        "fk_articles_category_id_article_categories",
        "articles",
        "article_categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )

    connection = op.get_bind()
    articles = sa.table(
        "articles",
        sa.column("id", sa.Integer),
        sa.column("category", sa.String),
        sa.column("tags", sa.JSON),
        sa.column("category_id", sa.Integer),
    )
    categories = sa.table("article_categories", sa.column("id", sa.Integer), sa.column("name", sa.String))
    tags = sa.table("article_tags", sa.column("id", sa.Integer), sa.column("name", sa.String))
    links = sa.table("article_tag_links", sa.column("article_id", sa.Integer), sa.column("tag_id", sa.Integer))

    category_ids = {}
    tag_ids = {}
    category_ids["未分类".casefold()] = _lookup_or_create(
        connection, categories, "未分类"
    )
    rows = connection.execute(sa.select(articles)).mappings()
    for row in rows:
        category_name = (row["category"] or "").strip() or "未分类"
        category_key = category_name.casefold()
        if category_key not in category_ids:
            category_ids[category_key] = _lookup_or_create(
                connection, categories, category_name
            )

        connection.execute(
            sa.update(articles)
            .where(articles.c.id == row["id"])
            .values(category_id=category_ids[category_key], category=category_name)
        )
        for raw_tag in _tag_values(row["tags"]):
            tag_name = str(raw_tag).strip()
            if not tag_name:
                continue
            tag_key = tag_name.casefold()
            if tag_key not in tag_ids:
                tag_ids[tag_key] = _lookup_or_create(connection, tags, tag_name)
            tag_id = tag_ids[tag_key]
            link_exists = connection.execute(
                sa.select(links.c.article_id)
                .where(links.c.article_id == row["id"])
                .where(links.c.tag_id == tag_id)
            ).first()
            if link_exists is None:
                connection.execute(
                    sa.insert(links).values(article_id=row["id"], tag_id=tag_id)
                )


def downgrade() -> None:
    op.drop_constraint("fk_articles_category_id_article_categories", "articles", type_="foreignkey")
    op.drop_index(op.f("ix_articles_category_id"), table_name="articles")
    op.drop_column("articles", "category_id")
    op.drop_index(op.f("ix_article_tag_links_tag_id"), table_name="article_tag_links")
    op.drop_table("article_tag_links")
    op.drop_index(op.f("ix_article_tags_name"), table_name="article_tags")
    op.drop_table("article_tags")
    op.drop_index(op.f("ix_article_categories_name"), table_name="article_categories")
    op.drop_table("article_categories")
