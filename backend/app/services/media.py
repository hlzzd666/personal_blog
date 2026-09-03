from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import mimetypes
from pathlib import Path
from typing import Any
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.about_profile import AboutProfile
from backend.app.models.article import Article
from backend.app.models.content import Note, Series
from backend.app.models.gallery import GalleryCharacter, GallerySettings
from backend.app.schemas.media import (
    MediaCleanupResponse,
    MediaFileItem,
    MediaListResponse,
    MediaReference,
)
from backend.app.services.site_settings import get_site_settings


@dataclass(frozen=True)
class MediaReferenceCandidate:
    source: str
    label: str
    value: str


def list_media_files(session: Session) -> MediaListResponse:
    upload_root = settings.upload_path.resolve()
    reference_candidates = _collect_reference_candidates(session)
    items = [
        _build_media_item(upload_root, path, reference_candidates)
        for path in _iter_upload_files(upload_root)
    ]
    items.sort(key=lambda item: item.modified_at, reverse=True)

    total_size = sum(item.size for item in items)
    unused_items = [item for item in items if not item.referenced]
    return MediaListResponse(
        items=items,
        total=len(items),
        used_count=len(items) - len(unused_items),
        unused_count=len(unused_items),
        total_size=total_size,
        unused_size=sum(item.size for item in unused_items),
    )


def cleanup_unreferenced_media_files(session: Session) -> MediaCleanupResponse:
    upload_root = settings.upload_path.resolve()
    media_files = list_media_files(session)
    deleted_files: list[str] = []
    deleted_size = 0

    for item in media_files.items:
        if item.referenced:
            continue

        target_path = (upload_root / item.relative_path).resolve()
        try:
            target_path.relative_to(upload_root)
        except ValueError:
            continue

        if not target_path.is_file():
            continue

        target_path.unlink()
        deleted_files.append(item.relative_path)
        deleted_size += item.size
        _remove_empty_parent_dirs(target_path.parent, upload_root)

    return MediaCleanupResponse(
        deleted_count=len(deleted_files),
        deleted_size=deleted_size,
        deleted_files=deleted_files,
    )


def _iter_upload_files(upload_root: Path) -> list[Path]:
    if not upload_root.exists():
        return []

    files: list[Path] = []
    for path in upload_root.rglob("*"):
        resolved_path = path.resolve()
        try:
            resolved_path.relative_to(upload_root)
        except ValueError:
            continue
        if resolved_path.is_file():
            files.append(resolved_path)
    return files


def _build_media_item(
    upload_root: Path,
    path: Path,
    reference_candidates: list[MediaReferenceCandidate],
) -> MediaFileItem:
    relative_path = path.relative_to(upload_root).as_posix()
    stat = path.stat()
    content_type = mimetypes.guess_type(relative_path)[0] or "application/octet-stream"
    media_type = _get_media_type(content_type, relative_path)
    references = _find_references(relative_path, reference_candidates)

    return MediaFileItem(
        filename=path.name,
        relative_path=relative_path,
        url=_build_public_url(relative_path),
        content_type=content_type,
        media_type=media_type,
        size=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
        referenced=len(references) > 0,
        references=references,
    )


def _collect_reference_candidates(session: Session) -> list[MediaReferenceCandidate]:
    candidates: list[MediaReferenceCandidate] = []
    site_settings = get_site_settings().model_dump(mode="json")
    candidates.extend(
        _collect_from_payload(site_settings, source="站点设置", label_prefix="站点设置")
    )

    about_profile = session.scalar(select(AboutProfile).where(AboutProfile.id == 1))
    if about_profile is not None:
        candidates.extend(
            _collect_from_payload(
                _model_to_payload(about_profile),
                source="关于我",
                label_prefix="关于我资料",
            )
        )

    articles = session.scalars(select(Article)).all()
    for article in articles:
        article_payload = _model_to_payload(article)
        candidates.extend(
            _collect_from_payload(
                article_payload,
                source="文章",
                label_prefix=f"文章：{article.title}",
            )
        )

    for series in session.scalars(select(Series)).all():
        candidates.extend(
            _collect_from_payload(
                _model_to_payload(series), source="专题", label_prefix=f"专题：{series.title}"
            )
        )

    for note in session.scalars(select(Note)).all():
        candidates.extend(
            _collect_from_payload(
                _model_to_payload(note), source="短动态", label_prefix=f"动态：{note.slug}"
            )
        )

    gallery_settings = session.get(GallerySettings, 1)
    if gallery_settings is not None:
        candidates.extend(
            _collect_from_payload(
                _model_to_payload(gallery_settings),
                source="3D 展厅",
                label_prefix="展厅设置",
            )
        )

    for character in session.scalars(select(GalleryCharacter)).all():
        candidates.extend(
            _collect_from_payload(
                _model_to_payload(character),
                source="3D 展厅",
                label_prefix=f"展厅人物：{character.name}",
            )
        )

    return candidates


def _collect_from_payload(
    payload: Any,
    *,
    source: str,
    label_prefix: str,
) -> list[MediaReferenceCandidate]:
    candidates: list[MediaReferenceCandidate] = []
    for field_path, value in _iter_strings(payload):
        if "/uploads/" not in value:
            continue
        label = f"{label_prefix} / {field_path}" if field_path else label_prefix
        candidates.append(MediaReferenceCandidate(source=source, label=label, value=value))
    return candidates


def _iter_strings(value: Any, path: str = "") -> list[tuple[str, str]]:
    if value is None:
        return []
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, dict):
        strings: list[tuple[str, str]] = []
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            strings.extend(_iter_strings(child, child_path))
        return strings
    if isinstance(value, (list, tuple)):
        strings = []
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            strings.extend(_iter_strings(child, child_path))
        return strings
    return []


def _model_to_payload(model: Any) -> dict[str, Any]:
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}


def _find_references(
    relative_path: str,
    reference_candidates: list[MediaReferenceCandidate],
) -> list[MediaReference]:
    matches: list[MediaReference] = []
    seen: set[tuple[str, str]] = set()
    public_path = f"/uploads/{relative_path}"
    encoded_public_path = f"/uploads/{quote(relative_path, safe='/')}"
    public_url = _build_public_url(relative_path)
    encoded_public_url = _build_public_url(quote(relative_path, safe="/"))
    targets = {public_path, encoded_public_path, public_url, encoded_public_url}

    for candidate in reference_candidates:
        if not any(target in candidate.value or candidate.value.endswith(target) for target in targets):
            continue
        key = (candidate.source, candidate.label)
        if key in seen:
            continue
        seen.add(key)
        matches.append(MediaReference(source=candidate.source, label=candidate.label))

    return matches


def _build_public_url(relative_path: str) -> str:
    return f"{settings.public_base_url.rstrip('/')}/uploads/{relative_path}"


def _get_media_type(content_type: str, relative_path: str) -> str:
    if content_type.startswith("image/"):
        return "image"
    if relative_path.startswith("resumes/") or content_type == "application/pdf":
        return "resume"
    return "other"


def _remove_empty_parent_dirs(directory: Path, upload_root: Path) -> None:
    current = directory.resolve()
    while current != upload_root:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent
