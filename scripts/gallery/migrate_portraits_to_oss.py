"""将展馆内置九宫格示例海报裁切后上传 OSS，并回写人物海报地址。

使用前将 backend/.env 的 MEDIA_STORAGE_DRIVER 设为 oss，并配置 OSS_* 环境变量：
    .\\.venv\\Scripts\\python.exe scripts/gallery/migrate_portraits_to_oss.py --dry-run
    .\\.venv\\Scripts\\python.exe scripts/gallery/migrate_portraits_to_oss.py --force
"""

from __future__ import annotations

import argparse
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image
from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.models.gallery import GalleryCharacter
from backend.app.services.gallery_media import create_gallery_image_variants

SOURCE = PROJECT_ROOT / "web/public/gallery/museum/portraits.webp"
NAMES = ("路飞", "索隆", "娜美", "乌索普", "山治", "乔巴", "罗宾", "弗兰奇", "甚平")
ROW_STARTS = (0, 477, 960)
ROW_HEIGHTS = (477, 483, 576)
ATLAS_HEIGHT = 1536


def _region(index: int, width: int, height: int) -> tuple[int, int, int, int]:
    column, row = index % 3, index // 3
    left = round(column * width / 3)
    right = round((column + 1) * width / 3)
    top = round(ROW_STARTS[row] * height / ATLAS_HEIGHT)
    bottom = round((ROW_STARTS[row] + ROW_HEIGHTS[row]) * height / ATLAS_HEIGHT)
    return left, top, right, bottom


def _character_index(name: str) -> int:
    return next((index for index, part in enumerate(NAMES) if part in name), -1)


def _poster_bytes(atlas: Image.Image, index: int) -> bytes:
    crop = atlas.crop(_region(index, atlas.width, atlas.height)).convert("RGB")
    output = BytesIO()
    crop.save(output, format="WEBP", quality=90, method=6)
    return output.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description="迁移展馆示例海报到 OSS")
    parser.add_argument("--source", type=Path, default=SOURCE, help="九宫格海报图路径")
    parser.add_argument("--dry-run", action="store_true", help="只检查匹配，不上传或修改数据库")
    parser.add_argument("--force", action="store_true", help="覆盖已有 poster_url")
    args = parser.parse_args()

    if not args.source.is_file():
        parser.error(f"找不到海报图集：{args.source}")
    if not args.dry_run and settings.media_storage_driver.strip().lower() != "oss":
        parser.error("正式迁移前请将 MEDIA_STORAGE_DRIVER=oss，并配置 OSS_* 环境变量")

    with Image.open(args.source) as source:
        atlas = source.copy()
    with SessionLocal() as session:
        characters = list(
            session.scalars(
                select(GalleryCharacter).order_by(GalleryCharacter.sort_order, GalleryCharacter.id)
            )
        )
        matches = [(character, _character_index(character.name)) for character in characters]
        matches = [(character, index) for character, index in matches if index >= 0]
        if not matches:
            print("没有匹配到九位示例人物，未执行任何操作。")
            return 0
        migrated = 0
        for character, index in matches:
            action = "覆盖" if args.force or not character.poster_url else "跳过"
            print(f"{action}: {character.id} {character.name} -> {NAMES[index]}")
            if args.dry_run or (character.poster_url and not args.force):
                continue
            result = create_gallery_image_variants(_poster_bytes(atlas, index), "poster")
            character.poster_url = result.url
            migrated += 1
        if not args.dry_run:
            session.commit()
            print(f"已上传并更新 {migrated} 条记录。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
