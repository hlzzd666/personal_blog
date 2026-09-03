"""add 3d character gallery

Revision ID: 20260831_01
Revises: 20260829_02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260831_01"
down_revision = "20260829_02"
branch_labels = None
depends_on = None


DEMO_CHARACTERS = [
    ("蒙奇·D·路飞", "草帽小子", "草帽一伙", "30亿贝里", "橡胶般自由伸展的身体与霸王色霸气", "草帽一伙船长，以成为海贼王为目标踏上伟大航路。", "我是要成为海贼王的男人！"),
    ("罗罗诺亚·索隆", "海贼猎人", "草帽一伙", "11亿1100万贝里", "三刀流剑术与武装色霸气", "草帽一伙剑士，为实现世界第一大剑豪的约定不断磨炼剑术。", "背上的伤是剑士的耻辱。"),
    ("娜美", "小贼猫", "草帽一伙", "3亿6600万贝里", "天候操控与卓越航海术", "草帽一伙航海士，能够读取海图与天气并带领伙伴穿越危险海域。", "我要画出全世界的海图。"),
    ("乌索普", "狙击之王", "草帽一伙", "5亿贝里", "远距离狙击与植物弹药", "草帽一伙狙击手，希望成长为勇敢的海上战士。", "我可是勇敢的海上战士！"),
    ("山治", "黑足", "草帽一伙", "10亿3200万贝里", "黑足踢技与精湛料理", "草帽一伙厨师，为寻找传说中的蔚蓝海域 All Blue 而航行。", "能原谅女人谎话的，才是男人。"),
    ("托尼托尼·乔巴", "爱吃棉花糖的乔巴", "草帽一伙", "1000贝里", "人人果实与专业医术", "草帽一伙船医，希望成为能够治愈任何疾病的医生。", "我才不会因为被夸而高兴呢！"),
    ("妮可·罗宾", "恶魔之子", "草帽一伙", "9亿3000万贝里", "花花果实与历史解读", "草帽一伙考古学家，寻找真正的历史正文与被遗忘的历史。", "我想活下去！"),
    ("弗兰奇", "铁人", "草帽一伙", "3亿9400万贝里", "改造人武装与船舶建造", "草帽一伙船匠，亲手打造并守护承载伙伴梦想的万里阳光号。", "SUPER！"),
]


def upgrade() -> None:
    op.create_table(
        "gallery_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hall_name", sa.String(length=120), nullable=False),
        sa.Column("entry_title", sa.String(length=200), nullable=False),
        sa.Column("show_logo", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("logo_url", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "gallery_characters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("epithet", sa.String(length=120), nullable=False),
        sa.Column("faction", sa.String(length=120), nullable=False),
        sa.Column("bounty", sa.String(length=120), nullable=False),
        sa.Column("ability", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("quote", sa.String(length=500), nullable=False),
        sa.Column("poster_url", sa.String(length=2048), nullable=True),
        sa.Column("is_visible", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gallery_characters_sort_order", "gallery_characters", ["sort_order"])

    connection = op.get_bind()
    settings_table = sa.table(
        "gallery_settings",
        sa.column("id", sa.Integer),
        sa.column("hall_name", sa.String),
        sa.column("entry_title", sa.String),
        sa.column("show_logo", sa.Boolean),
        sa.column("logo_url", sa.String),
    )
    character_table = sa.table(
        "gallery_characters",
        sa.column("name", sa.String),
        sa.column("epithet", sa.String),
        sa.column("faction", sa.String),
        sa.column("bounty", sa.String),
        sa.column("ability", sa.String),
        sa.column("description", sa.Text),
        sa.column("quote", sa.String),
        sa.column("poster_url", sa.String),
        sa.column("is_visible", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    connection.execute(
        sa.insert(settings_table).values(
            id=1,
            hall_name="伟大航路人物档案馆",
            entry_title="踏入伟大航路，查阅传奇人物档案",
            show_logo=False,
            logo_url=None,
        )
    )
    connection.execute(
        sa.insert(character_table),
        [
            {
                "name": name,
                "epithet": epithet,
                "faction": faction,
                "bounty": bounty,
                "ability": ability,
                "description": description,
                "quote": quote,
                "poster_url": None,
                "is_visible": True,
                "sort_order": index,
            }
            for index, (name, epithet, faction, bounty, ability, description, quote) in enumerate(DEMO_CHARACTERS)
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_gallery_characters_sort_order", table_name="gallery_characters")
    op.drop_table("gallery_characters")
    op.drop_table("gallery_settings")
