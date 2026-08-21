"""flatten about profile skills

Revision ID: 20260821_04
Revises: 20260821_03
"""

import json

from alembic import op
import sqlalchemy as sa


revision = "20260821_04"
down_revision = "20260821_03"
branch_labels = None
depends_on = None


def _decode_json(value: object) -> list[dict[str, object]]:
    if isinstance(value, str):
        decoded = json.loads(value)
        return decoded if isinstance(decoded, list) else []
    return value if isinstance(value, list) else []


def upgrade() -> None:
    op.add_column("about_profiles", sa.Column("skills", sa.JSON(), nullable=True))

    connection = op.get_bind()
    profiles = connection.execute(sa.text("SELECT id, skill_groups FROM about_profiles")).mappings()
    for profile in profiles:
        skills: list[dict[str, str]] = []
        seen: set[str] = set()
        for group in _decode_json(profile["skill_groups"]):
            for raw_name in group.get("skills", []):
                name = str(raw_name).strip()
                if not name or name in seen:
                    continue
                seen.add(name)
                skills.append({"name": name, "icon_url": ""})
        connection.execute(
            sa.text("UPDATE about_profiles SET skills = :skills WHERE id = :profile_id"),
            {"skills": json.dumps(skills, ensure_ascii=False), "profile_id": profile["id"]},
        )

    op.alter_column("about_profiles", "skills", existing_type=sa.JSON(), nullable=False)
    op.drop_column("about_profiles", "skill_groups")


def downgrade() -> None:
    op.add_column("about_profiles", sa.Column("skill_groups", sa.JSON(), nullable=True))

    connection = op.get_bind()
    profiles = connection.execute(sa.text("SELECT id, skills FROM about_profiles")).mappings()
    for profile in profiles:
        names = [str(item.get("name", "")).strip() for item in _decode_json(profile["skills"])]
        names = [name for name in names if name]
        groups = [{"name": "技术栈", "description": "", "skills": names}] if names else []
        connection.execute(
            sa.text("UPDATE about_profiles SET skill_groups = :groups WHERE id = :profile_id"),
            {"groups": json.dumps(groups, ensure_ascii=False), "profile_id": profile["id"]},
        )

    op.alter_column("about_profiles", "skill_groups", existing_type=sa.JSON(), nullable=False)
    op.drop_column("about_profiles", "skills")
