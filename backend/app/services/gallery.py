from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.gallery import GalleryCharacter, GalleryChapter, GallerySettings
from backend.app.schemas.gallery import (
    GalleryCharacterPayload,
    GalleryCharacterResponse,
    GalleryChapterPayload,
    GalleryChapterResponse,
    GalleryResponse,
    GallerySettingsPayload,
    GallerySettingsResponse,
)

MAX_GALLERY_CHARACTERS = 40
MAX_GALLERY_CHAPTERS = 20
DEFAULT_HALL_NAME = "伟大航路人物档案馆"
DEFAULT_ENTRY_TITLE = "踏入伟大航路，查阅传奇人物档案"


def list_gallery_chapters(session: Session, *, include_hidden: bool = False) -> list[GalleryChapterResponse]:
    chapters = list(session.scalars(select(GalleryChapter).order_by(GalleryChapter.sort_order, GalleryChapter.id)))
    if not include_hidden:
        chapters = [chapter for chapter in chapters if chapter.is_visible]
    return [GalleryChapterResponse.model_validate(chapter) for chapter in chapters]


def get_or_create_gallery_settings(session: Session) -> GallerySettings:
    settings = session.get(GallerySettings, 1)
    if settings is not None:
        return settings
    settings = GallerySettings(
        id=1,
        hall_name=DEFAULT_HALL_NAME,
        entry_title=DEFAULT_ENTRY_TITLE,
        show_entry=True,
        show_logo=False,
        logo_url=None,
    )
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings


def get_gallery(session: Session, *, include_hidden: bool = False) -> GalleryResponse:
    query = select(GalleryCharacter)
    if not include_hidden:
        query = query.where(GalleryCharacter.is_visible.is_(True))
    characters = list(
        session.scalars(query.order_by(GalleryCharacter.sort_order, GalleryCharacter.id))
    )
    return GalleryResponse(
        settings=GallerySettingsResponse.model_validate(get_or_create_gallery_settings(session)),
        chapters=list_gallery_chapters(session, include_hidden=include_hidden),
        characters=[GalleryCharacterResponse.model_validate(item) for item in characters],
    )


def create_gallery_chapter(session: Session, payload: GalleryChapterPayload) -> GalleryChapterResponse:
    total = session.scalar(select(func.count(GalleryChapter.id))) or 0
    if total >= MAX_GALLERY_CHAPTERS:
        raise ValueError("展厅最多维护 20 个分类标签")
    current_max_order = session.scalar(select(func.max(GalleryChapter.sort_order)))
    chapter = GalleryChapter(**payload.model_dump(), sort_order=(current_max_order if current_max_order is not None else -1) + 1)
    session.add(chapter)
    _commit_gallery_chapter(session)
    session.refresh(chapter)
    return GalleryChapterResponse.model_validate(chapter)


def get_gallery_chapter(session: Session, chapter_id: int) -> GalleryChapter | None:
    return session.get(GalleryChapter, chapter_id)


def update_gallery_chapter(session: Session, chapter: GalleryChapter, payload: GalleryChapterPayload) -> GalleryChapterResponse:
    for key, value in payload.model_dump().items():
        setattr(chapter, key, value)
    _commit_gallery_chapter(session)
    session.refresh(chapter)
    return GalleryChapterResponse.model_validate(chapter)


def _commit_gallery_chapter(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ValueError("分类名称已存在，请使用其他名称") from error


def delete_gallery_chapter(session: Session, chapter: GalleryChapter) -> None:
    if session.scalar(select(func.count(GalleryCharacter.id)).where(GalleryCharacter.chapter_id == chapter.id)):
        raise ValueError("该分类仍有人物使用，请先调整人物分类")
    session.delete(chapter)
    session.commit()
    _normalize_gallery_chapter_order(session)


def reorder_gallery_chapters(session: Session, chapter_ids: list[int]) -> list[GalleryChapterResponse]:
    chapters = list(session.scalars(select(GalleryChapter).order_by(GalleryChapter.sort_order, GalleryChapter.id)))
    if len(chapter_ids) != len(chapters) or set(chapter_ids) != {chapter.id for chapter in chapters}:
        raise ValueError("分类排序必须包含当前全部分类，且不能包含未知分类")
    chapter_map = {chapter.id: chapter for chapter in chapters}
    for index, chapter_id in enumerate(chapter_ids):
        chapter_map[chapter_id].sort_order = index
    session.commit()
    return list_gallery_chapters(session, include_hidden=True)


def update_gallery_settings(
    session: Session, payload: GallerySettingsPayload
) -> GallerySettingsResponse:
    settings = get_or_create_gallery_settings(session)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, key, value)
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return GallerySettingsResponse.model_validate(settings)


def create_gallery_character(
    session: Session, payload: GalleryCharacterPayload
) -> GalleryCharacterResponse:
    total = session.scalar(select(func.count(GalleryCharacter.id))) or 0
    if total >= MAX_GALLERY_CHARACTERS:
        raise ValueError("3D 展厅最多维护 40 位人物")
    if payload.chapter_id is not None and get_gallery_chapter(session, payload.chapter_id) is None:
        raise ValueError("人物分类不存在")
    current_max_order = session.scalar(select(func.max(GalleryCharacter.sort_order)))
    next_order = (current_max_order if current_max_order is not None else -1) + 1
    character = GalleryCharacter(**payload.model_dump(), sort_order=next_order)
    session.add(character)
    session.commit()
    session.refresh(character)
    return GalleryCharacterResponse.model_validate(character)


def get_gallery_character(session: Session, character_id: int) -> GalleryCharacter | None:
    return session.get(GalleryCharacter, character_id)


def update_gallery_character(
    session: Session,
    character: GalleryCharacter,
    payload: GalleryCharacterPayload,
) -> GalleryCharacterResponse:
    if payload.chapter_id is not None and get_gallery_chapter(session, payload.chapter_id) is None:
        raise ValueError("人物分类不存在")
    for key, value in payload.model_dump().items():
        # 旧客户端未携带分类字段时，保留已有归属；显式 null 表示取消分类。
        if key == "chapter_id" and key not in payload.model_fields_set:
            continue
        setattr(character, key, value)
    session.add(character)
    session.commit()
    session.refresh(character)
    return GalleryCharacterResponse.model_validate(character)


def delete_gallery_character(session: Session, character: GalleryCharacter) -> None:
    session.delete(character)
    session.commit()
    _normalize_gallery_order(session)


def reorder_gallery_characters(session: Session, character_ids: list[int]) -> list[GalleryCharacterResponse]:
    items = list(session.scalars(select(GalleryCharacter)))
    existing_ids = {item.id for item in items}
    if len(character_ids) != len(items) or set(character_ids) != existing_ids:
        raise ValueError("人物排序必须包含当前全部人物，且不能包含未知人物")
    item_map = {item.id: item for item in items}
    for index, character_id in enumerate(character_ids):
        item_map[character_id].sort_order = index
    session.commit()
    return get_gallery(session, include_hidden=True).characters


def _normalize_gallery_order(session: Session) -> None:
    items = list(
        session.scalars(select(GalleryCharacter).order_by(GalleryCharacter.sort_order, GalleryCharacter.id))
    )
    for index, item in enumerate(items):
        item.sort_order = index
    session.commit()


def _normalize_gallery_chapter_order(session: Session) -> None:
    chapters = list(session.scalars(select(GalleryChapter).order_by(GalleryChapter.sort_order, GalleryChapter.id)))
    for index, chapter in enumerate(chapters):
        chapter.sort_order = index
    session.commit()
