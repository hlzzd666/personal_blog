from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from backend.app.core.config import settings

MAX_GALLERY_IMAGE_PIXELS = 48_000_000
SUPPORTED_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


class GalleryImageError(ValueError):
    pass


@dataclass(frozen=True)
class GalleryImageVariants:
    url: str


def create_gallery_image_variants(content: bytes, kind: str) -> GalleryImageVariants:
    extension = _validate_image(content)
    asset_id = uuid4().hex
    return _write_image(content, asset_id, kind, extension)


def _validate_image(content: bytes) -> str:
    try:
        with Image.open(BytesIO(content)) as source:
            source.verify()
        with Image.open(BytesIO(content)) as source:
            if source.format not in SUPPORTED_FORMATS or getattr(source, "is_animated", False):
                raise GalleryImageError("展厅图片仅支持静态 JPG、PNG 或 WebP")
            width, height = source.size
            if width < 1 or height < 1 or width * height > MAX_GALLERY_IMAGE_PIXELS:
                raise GalleryImageError("图片尺寸无效或过大")
            return SUPPORTED_FORMATS[source.format]
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise GalleryImageError("无法识别有效的图片文件") from error


def _write_image(content: bytes, asset_id: str, kind: str, extension: str) -> GalleryImageVariants:
    if kind not in {"poster", "logo"}:
        raise GalleryImageError("不支持的展厅图片类型")
    image_path = settings.upload_path / "gallery" / f"{asset_id}{extension}"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = image_path.with_name(f".{image_path.name}.tmp")
    try:
        temporary_path.write_bytes(content)
        temporary_path.replace(image_path)
    except OSError:
        temporary_path.unlink(missing_ok=True)
        raise
    return GalleryImageVariants(url=_public_url(image_path))


def _public_url(path: Path) -> str:
    relative_path = path.resolve().relative_to(settings.upload_path.resolve()).as_posix()
    return f"{settings.public_base_url.rstrip('/')}/uploads/{relative_path}"
