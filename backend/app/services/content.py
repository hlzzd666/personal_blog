import json

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.cache import invalidate_article_list_cache
from backend.app.models.article import Article
from backend.app.models.content import Note, Series
from backend.app.schemas.article import ArticleResponse
from backend.app.schemas.content import (
    DashboardStatsResponse,
    NoteListResponse,
    NotePayload,
    NoteResponse,
    SeriesDetailResponse,
    SeriesListResponse,
    SeriesPayload,
    SeriesResponse,
)


def _article_date_order():
    return (
        Article.published_at.is_(None),
        Article.published_at.desc(),
        Article.created_at.desc(),
        Article.id.desc(),
    )


def serialize_series(session: Session, series: Series) -> SeriesResponse:
    article_count = session.scalar(
        select(func.count(Article.id)).where(Article.series_id == series.id)
    ) or 0
    return SeriesResponse(
        **{column.name: getattr(series, column.name) for column in series.__table__.columns},
        article_count=article_count,
    )


def list_series(session: Session) -> SeriesListResponse:
    items = list(session.scalars(select(Series).order_by(Series.sort_order.desc(), Series.id.desc())))
    return SeriesListResponse(
        items=[serialize_series(session, item) for item in items],
        total=len(items),
    )


def get_series_by_slug(session: Session, slug: str) -> Series | None:
    return session.scalar(select(Series).where(Series.slug == slug))


def get_series(session: Session, series_id: int) -> Series | None:
    return session.get(Series, series_id)


def get_series_detail(session: Session, series: Series) -> SeriesDetailResponse:
    articles = list(
        session.scalars(
            select(Article)
            .where(Article.series_id == series.id)
            .order_by(Article.series_order.is_(None), Article.series_order.asc(), *_article_date_order())
        )
    )
    return SeriesDetailResponse(
        **serialize_series(session, series).model_dump(),
        articles=[ArticleResponse.model_validate(article) for article in articles],
    )


def create_series(session: Session, payload: SeriesPayload) -> SeriesResponse:
    series = Series(**payload.model_dump())
    session.add(series)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ValueError("专题别名已存在") from error
    session.refresh(series)
    return serialize_series(session, series)


def update_series(session: Session, series: Series, payload: SeriesPayload) -> SeriesResponse:
    for key, value in payload.model_dump().items():
        setattr(series, key, value)
    session.add(series)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ValueError("专题别名已存在") from error
    session.refresh(series)
    return serialize_series(session, series)


def delete_series(session: Session, series: Series) -> None:
    session.execute(
        update(Article)
        .where(Article.series_id == series.id)
        .values(series_id=None, series_order=None)
    )
    session.delete(series)
    session.commit()
    invalidate_article_list_cache()


def list_notes(
    session: Session,
    *,
    page: int,
    page_size: int,
    tag: str | None = None,
) -> NoteListResponse:
    filters = [func.json_contains(Note.tags, json.dumps(tag, ensure_ascii=False)) == 1] if tag else []
    total = session.scalar(select(func.count(Note.id)).where(*filters)) or 0
    items = list(
        session.scalars(
            select(Note)
            .where(*filters)
            .order_by(
                Note.published_at.is_(None),
                Note.published_at.desc(),
                Note.created_at.desc(),
                Note.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return NoteListResponse(
        items=[NoteResponse.model_validate(note) for note in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_note_by_slug(session: Session, slug: str) -> Note | None:
    return session.scalar(select(Note).where(Note.slug == slug))


def get_note(session: Session, note_id: int) -> Note | None:
    return session.get(Note, note_id)


def _note_values(payload: NotePayload) -> dict:
    values = payload.model_dump()
    if values["external_url"] is not None:
        values["external_url"] = str(values["external_url"])
    return values


def create_note(session: Session, payload: NotePayload) -> Note:
    note = Note(**_note_values(payload))
    session.add(note)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ValueError("动态别名已存在") from error
    session.refresh(note)
    return note


def update_note(session: Session, note: Note, payload: NotePayload) -> Note:
    for key, value in _note_values(payload).items():
        setattr(note, key, value)
    session.add(note)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ValueError("动态别名已存在") from error
    session.refresh(note)
    return note


def delete_note(session: Session, note: Note) -> None:
    session.delete(note)
    session.commit()


def get_dashboard_stats(session: Session) -> DashboardStatsResponse:
    article_count = session.scalar(select(func.count(Article.id))) or 0
    series_count = session.scalar(select(func.count(Series.id))) or 0
    note_count = session.scalar(select(func.count(Note.id))) or 0
    total_views = session.scalar(select(func.coalesce(func.sum(Article.views), 0))) or 0
    total_likes = session.scalar(select(func.coalesce(func.sum(Article.likes), 0))) or 0
    top_articles = list(
        session.scalars(
            select(Article).order_by(Article.views.desc(), Article.likes.desc(), Article.id.desc()).limit(5)
        )
    )
    recent_articles = list(session.scalars(select(Article).order_by(*_article_date_order()).limit(5)))
    return DashboardStatsResponse(
        article_count=article_count,
        series_count=series_count,
        note_count=note_count,
        total_views=total_views,
        total_likes=total_likes,
        top_articles=[ArticleResponse.model_validate(article) for article in top_articles],
        recent_articles=[ArticleResponse.model_validate(article) for article in recent_articles],
    )
