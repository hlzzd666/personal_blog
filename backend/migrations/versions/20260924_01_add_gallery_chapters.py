"""make gallery chapter tabs configurable

Revision ID: 20260924_01
Revises: 20260913_01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260924_01"
down_revision = "20260913_01"
branch_labels = None
depends_on = None

CHAPTERS = [
    ("东海群像", "每一段传奇，都始于一次启航。", "梦想的起点\n东海群像", "小小的港口，装得下最辽阔的梦想。\n在成为同伴以前，他们先选择了自己的航向。", "从风车村出发，读懂最初的约定。", "CHAPTER II · EAST BLUE", "路飞向大海许下成为海贼王的愿望；索隆守住与挚友的约定；娜美想画出世界的海图；乌索普追逐勇敢；山治寻找传说中的 All Blue。"),
    ("伟大航路", "以相遇为坐标，以信念为方向。", "相遇与远方\n伟大航路", "航路并不承诺答案，只不断带来新的相遇。\n有人寻找历史，有人寻找一处可以归来的地方。", "循着记录指针，翻开下一段航海志。", "CHAPTER III · GRAND LINE", "越过颠倒山，气候、岛屿和规则都变得陌生。乔巴把医者的心带上船；罗宾继续追寻历史；弗兰奇把造船的梦想交付大海。"),
    ("新世界", "穿过风暴，抵达自己的答案。", "时代的回声\n新世界", "当航程驶入风暴深处，梦想仍然指向远方。\n那些被守护的约定，成为继续前行的力量。", "越过地平线，重访仍在继续的故事。", "CHAPTER IV · NEW WORLD", "新世界让每一个选择都承担更大的重量。甚平带着对同伴的承诺走上甲板，旧时代的意志与新的航程在这里交汇。"),
]


def upgrade() -> None:
    op.create_table(
        "gallery_chapters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=80), nullable=False),
        sa.Column("subtitle", sa.String(length=200), nullable=False),
        sa.Column("heading", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("note", sa.String(length=300), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("story", sa.Text(), nullable=False),
        sa.Column("artwork_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_visible", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("title", name="uq_gallery_chapters_title"),
    )
    op.add_column("gallery_characters", sa.Column("chapter_id", sa.Integer(), nullable=True))
    op.create_index("ix_gallery_chapters_sort_order", "gallery_chapters", ["sort_order"])
    op.create_index("ix_gallery_characters_chapter_id", "gallery_characters", ["chapter_id"])
    with op.batch_alter_table("gallery_characters") as batch:
        batch.create_foreign_key("fk_gallery_characters_chapter_id", "gallery_chapters", ["chapter_id"], ["id"])

    connection = op.get_bind()
    chapter_table = sa.table(
        "gallery_chapters",
        sa.column("id", sa.Integer),
        sa.column("title", sa.String),
        sa.column("subtitle", sa.String),
        sa.column("heading", sa.String),
        sa.column("description", sa.String),
        sa.column("note", sa.String),
        sa.column("label", sa.String),
        sa.column("story", sa.Text),
        sa.column("artwork_index", sa.Integer),
        sa.column("is_visible", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    character_table = sa.table("gallery_characters", sa.column("name", sa.String), sa.column("chapter_id", sa.Integer))
    for index, chapter in enumerate(CHAPTERS):
        chapter_id = index + 1
        connection.execute(
            sa.insert(chapter_table).values(
                id=chapter_id, title=chapter[0], subtitle=chapter[1], heading=chapter[2], description=chapter[3],
                note=chapter[4], label=chapter[5], story=chapter[6], artwork_index=chapter_id, is_visible=True, sort_order=index,
            )
        )
        names = (
            ("路飞", "索隆", "娜美", "乌索普", "山治") if index == 0
            else ("乔巴", "罗宾", "弗兰奇", "布鲁克") if index == 1
            else ("甚平",)
        )
        connection.execute(character_table.update().where(
            character_table.c.chapter_id.is_(None),
            sa.or_(*(character_table.c.name.contains(name) for name in names)),
        ).values(chapter_id=chapter_id))


def downgrade() -> None:
    with op.batch_alter_table("gallery_characters") as batch:
        batch.drop_constraint("fk_gallery_characters_chapter_id", type_="foreignkey")
    op.drop_index("ix_gallery_characters_chapter_id", table_name="gallery_characters")
    op.drop_index("ix_gallery_chapters_sort_order", table_name="gallery_chapters")
    op.drop_column("gallery_characters", "chapter_id")
    op.drop_table("gallery_chapters")
