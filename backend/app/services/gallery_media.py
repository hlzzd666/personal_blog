from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlsplit
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.gallery import GalleryCharacter
from backend.app.services.gallery import get_or_create_gallery_settings

MAX_GALLERY_IMAGE_PIXELS = 48_000_000
POSTER_FRAME_SIZE = (512, 768)
POSTER_DISPLAY_SIZE = (960, 1440)
LOGO_MAX_SIZE = (512, 512)
SUPPORTED_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


class GalleryImageError(ValueError):
    pass


@dataclass(frozen=True)
class GalleryImageVariants:
    original_url: str
    display_url: str
    frame_url: str | None = None


def create_gallery_image_variants(content: bytes, kind: str) -> GalleryImageVariants:
    image, extension = _open_image(content)
    asset_id = uuid4().hex
    original_path = settings.upload_path / "gallery" / "originals" / f"{asset_id}{extension}"
    original_path.parent.mkdir(parents=True, exist_ok=True)
    original_path.write_bytes(content)
    try:
        return _write_variants(image, asset_id, kind, original_url=_public_url(original_path))
    except Exception:
        original_path.unlink(missing_ok=True)
        raise


def regenerate_gallery_image_derivatives(session: Session) -> int:
    settings_record = get_or_create_gallery_settings(session)
    generated = 0
    if settings_record.logo_url and not settings_record.logo_display_url:
        variants = _generate_from_local_url(settings_record.logo_url, "logo")
        if variants:
            settings_record.logo_display_url = variants.display_url
            generated += 1

    for character in session.query(GalleryCharacter).all():
        if not character.poster_url or (character.poster_frame_url and character.poster_display_url):
            continue
        variants = _generate_from_local_url(character.poster_url, "poster")
        if not variants:
            continue
        character.poster_frame_url = variants.frame_url
        character.poster_display_url = variants.display_url
        generated += 1

    if generated:
        session.commit()
    return generated


def _generate_from_local_url(url: str, kind: str) -> GalleryImageVariants | None:
    source_path = _local_upload_path(url)
    if source_path is None or not source_path.is_file():
        return None
    try:
        image, _ = _open_image(source_path.read_bytes())
        return _write_variants(image, uuid4().hex, kind, original_url=url)
    except (GalleryImageError, OSError):
        return None


def _open_image(content: bytes) -> tuple[Image.Image, str]:
    try:
        with Image.open(BytesIO(content)) as source:
            source.verify()
        with Image.open(BytesIO(content)) as source:
            if source.format not in SUPPORTED_FORMATS or getattr(source, "is_animated", False):
                raise GalleryImageError("展厅图片仅支持静态 JPG、PNG 或 WebP")
            width, height = source.size
            if width < 1 or height < 1 or width * height > MAX_GALLERY_IMAGE_PIXELS:
                raise GalleryImageError("图片尺寸无效或过大")
            image = ImageOps.exif_transpose(source).copy()
            return image, SUPPORTED_FORMATS[source.format]
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise GalleryImageError("无法识别有效的图片文件") from error


def _write_variants(image: Image.Image, asset_id: str, kind: str, *, original_url: str) -> GalleryImageVariants:
    derived_dir = settings.upload_path / "gallery" / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)
    if kind == "poster":
        frame_path = derived_dir / f"{asset_id}-frame.webp"
        display_path = derived_dir / f"{asset_id}-display.webp"
        _save_webp(ImageOps.fit(image, POSTER_FRAME_SIZE, Image.Resampling.LANCZOS), frame_path)
        _save_webp(ImageOps.fit(image, POSTER_DISPLAY_SIZE, Image.Resampling.LANCZOS), display_path)
        return GalleryImageVariants(
            original_url=original_url,
            frame_url=_public_url(frame_path),
            display_url=_public_url(display_path),
        )
    if kind == "logo":
        display_path = derived_dir / f"{asset_id}-logo.webp"
        logo = image.copy()
        logo.thumbnail(LOGO_MAX_SIZE, Image.Resampling.LANCZOS)
        _save_webp(logo, display_path)
        return GalleryImageVariants(original_url=original_url, display_url=_public_url(display_path))
    raise GalleryImageError("不支持的展厅图片类型")


def _save_webp(image: Image.Image, path: Path) -> None:
    save_image = image.convert("RGBA") if image.mode in {"RGBA", "LA"} else image.convert("RGB")
    save_image.save(path, "WEBP", quality=88, method=6)


def _local_upload_path(url: str) -> Path | None:
    try:
        path = unquote(urlsplit(url).path)
    except ValueError:
        return None
    marker = "/uploads/"
    if marker not in path:
        return None
    relative_path = path.split(marker, 1)[1]
    candidate = (settings.upload_path / relative_path).resolve()
    try:
        candidate.relative_to(settings.upload_path.resolve())
    except ValueError:
        return None
    return candidate


def _public_url(path: Path) -> str:
    relative_path = path.resolve().relative_to(settings.upload_path.resolve()).as_posix()
    return f"{settings.public_base_url.rstrip('/')}/uploads/{relative_path}"
