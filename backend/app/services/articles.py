from datetime import datetime
from typing import Literal

from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.cache import (
    build_article_list_cache_key,
    get_cache_value,
    invalidate_article_list_cache,
    set_cache_value,
)
from backend.app.models.article import Article, ArticleLikeRecord
from backend.app.models.content import Series
from backend.app.schemas.article import (
    ArticleContextResponse,
    ArticleCountItem,
    ArticleCreate,
    ArticleListResponse,
    ArticleListStats,
    ArticleMonthCount,
    ArticleUpdate,
    ArticleSeriesSummary,
    ArticleSummary,
)

ArticleListCacheStatus = Literal["HIT", "MISS", "BYPASS"]


def build_article_filters(
    *,
    category: str | None = None,
    tag: str | None = None,
    search: str | None = None,
) -> list:
    filters = []
    if category:
        filters.append(Article.category == category)
    if tag:
        filters.append(Article.tags.contains(tag))
    if search:
        keyword = f"%{search.strip()}%"
        filters.append(
            or_(
                Article.title.like(keyword),
                Article.slug.like(keyword),
                Article.summary.like(keyword),
                Article.content_markdown.like(keyword),
            )
        )
    return filters


def list_articles(
    session: Session,
    *,
    public_only: bool,
    page: int,
    page_size: int,
    category: str | None = None,
    tag: str | None = None,
    search: str | None = None,
) -> tuple[list[Article], int]:
    query = select(Article)
    count_query = select(func.count(Article.id))
    # 文章不区分草稿和发布状态，public_only 参数保留用于兼容调用方。
    filters = build_article_filters(category=category, tag=tag, search=search)

    # 归档按发表时间形成唯一时间线；未填写发表时间时回退到创建时间。
    query = query.where(*filters).order_by(
        Article.published_at.is_(None),
        Article.published_at.desc(),
        Article.created_at.desc(),
        Article.id.desc(),
    )
    count_query = count_query.where(*filters)
    total = session.scalar(count_query) or 0
    items = list(session.scalars(query.offset((page - 1) * page_size).limit(page_size)))
    return items, total


def get_article_list_stats(
    session: Session,
    *,
    category: str | None = None,
    tag: str | None = None,
    search: str | None = None,
) -> ArticleListStats:
    filtered_articles = list(
        session.scalars(
            select(Article).where(*build_article_filters(category=category, tag=tag, search=search))
        )
    )
    all_articles = list(session.scalars(select(Article)))

    month_counts: dict[str, int] = {}
    for article in filtered_articles:
        archive_date = article.published_at or article.created_at
        key = f"{archive_date.year}-{archive_date.month:02d}"
        month_counts[key] = month_counts.get(key, 0) + 1

    category_counts: dict[str, int] = {}
    tag_counts: dict[str, int] = {}
    for article in all_articles:
        category_name = article.category or "未分类"
        category_counts[category_name] = category_counts.get(category_name, 0) + 1
        for article_tag in article.tags or []:
            tag_counts[article_tag] = tag_counts.get(article_tag, 0) + 1

    return ArticleListStats(
        categories=[
            ArticleCountItem(name=name, count=count)
            for name, count in sorted(category_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        tags=[
            ArticleCountItem(name=name, count=count)
            for name, count in sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        months=[
            ArticleMonthCount(key=key, count=count)
            for key, count in sorted(month_counts.items(), reverse=True)
        ],
    )


def get_article_list_response(
    session: Session,
    *,
    public_only: bool,
    page: int,
    page_size: int,
    category: str | None = None,
    tag: str | None = None,
    search: str | None = None,
) -> tuple[ArticleListResponse, ArticleListCacheStatus]:
    cache_key = build_article_list_cache_key(
        public_only=public_only,
        page=page,
        page_size=page_size,
        category=category,
        tag=tag,
        search=search,
    )
    cached_value = get_cache_value(cache_key)
    if cached_value is not None:
        try:
            if '"stats"' in cached_value:
                return ArticleListResponse.model_validate_json(cached_value), "HIT"
        except ValueError:
            # 缓存内容与当前响应模型不兼容时，直接回源数据库重建。
            pass

    items, total = list_articles(
        session,
        public_only=public_only,
        page=page,
        page_size=page_size,
        category=category,
        tag=tag,
        search=search,
    )
    response = ArticleListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        stats=get_article_list_stats(session, category=category, tag=tag, search=search),
    )
    set_cache_value(cache_key, response.model_dump_json())
    return response, "MISS" if cache_key is not None else "BYPASS"


def get_public_article(session: Session, slug: str) -> Article | None:
    article = session.scalar(
        select(Article).where(Article.slug == slug)
    )
    if article is None:
        return None

    session.execute(update(Article).where(Article.id == article.id).values(views=Article.views + 1))
    session.commit()
    session.refresh(article)
    invalidate_article_list_cache()
    return article


def get_article_context(session: Session, slug: str) -> ArticleContextResponse | None:
    article = session.scalar(select(Article).where(Article.slug == slug))
    if article is None:
        return None

    all_articles = list(session.scalars(select(Article).where(Article.id != article.id)))
    series = session.get(Series, article.series_id) if article.series_id else None

    if article.series_id is not None:
        series_articles = list(
            session.scalars(
                select(Article)
                .where(Article.series_id == article.series_id)
                .order_by(Article.series_order.is_(None), Article.series_order.asc(), Article.id.asc())
            )
        )
        index = next(index for index, candidate in enumerate(series_articles) if candidate.id == article.id)
        previous_article = series_articles[index - 1] if index > 0 else None
        next_article = series_articles[index + 1] if index + 1 < len(series_articles) else None
    else:
        ordered = sorted(
            [article, *all_articles],
            key=lambda item: (item.published_at or item.created_at, item.id),
            reverse=True,
        )
        index = ordered.index(article)
        next_article = ordered[index - 1] if index > 0 else None
        previous_article = ordered[index + 1] if index + 1 < len(ordered) else None

    article_tags = set(article.tags or [])
    related = sorted(
        all_articles,
        key=lambda candidate: (
            int(article.series_id is not None and candidate.series_id == article.series_id),
            len(article_tags.intersection(candidate.tags or [])),
            int(candidate.category == article.category),
            candidate.published_at or candidate.created_at,
            candidate.id,
        ),
        reverse=True,
    )[:3]

    return ArticleContextResponse(
        previous=ArticleSummary.model_validate(previous_article) if previous_article else None,
        next=ArticleSummary.model_validate(next_article) if next_article else None,
        related=[ArticleSummary.model_validate(item) for item in related],
        series=(
            ArticleSeriesSummary(id=series.id, slug=series.slug, title=series.title)
            if series
            else None
        ),
    )


def get_article(session: Session, article_id: int) -> Article | None:
    return session.get(Article, article_id)


def create_article(session: Session, payload: ArticleCreate) -> Article:
    values = payload.model_dump()
    if values["series_id"] is not None and session.get(Series, values["series_id"]) is None:
        raise ValueError("所选专题不存在")
    if values["series_id"] is None:
        values["series_order"] = None
    if values["source_url"] is not None:
        values["source_url"] = str(values["source_url"])
    article = Article(**values)
    if article.updated_at is None:
        article.updated_at = datetime.now()
    session.add(article)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ValueError("文章别名已存在") from error
    session.refresh(article)
    invalidate_article_list_cache()
    return article


def update_article(session: Session, article: Article, payload: ArticleUpdate) -> Article:
    values = payload.model_dump()
    if values["series_id"] is not None and session.get(Series, values["series_id"]) is None:
        raise ValueError("所选专题不存在")
    if values["series_id"] is None:
        values["series_order"] = None
    if values["source_url"] is not None:
        values["source_url"] = str(values["source_url"])
    if values["updated_at"] is None:
        values.pop("updated_at")
    for key, value in values.items():
        setattr(article, key, value)
    session.add(article)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ValueError("文章别名已存在") from error
    session.refresh(article)
    invalidate_article_list_cache()
    return article


def delete_article(session: Session, article: Article) -> None:
    session.delete(article)
    session.commit()
    invalidate_article_list_cache()


def like_article(
    session: Session,
    slug: str,
    visitor_hash: str,
) -> tuple[Article | None, bool]:
    article = session.scalar(select(Article).where(Article.slug == slug))
    if article is None:
        return None, False

    existing_record = session.scalar(
        select(ArticleLikeRecord.id).where(
            ArticleLikeRecord.article_id == article.id,
            ArticleLikeRecord.visitor_hash == visitor_hash,
        )
    )
    if existing_record is not None:
        return article, True

    session.add(ArticleLikeRecord(article_id=article.id, visitor_hash=visitor_hash))
    try:
        session.flush()
        session.execute(update(Article).where(Article.id == article.id).values(likes=Article.likes + 1))
        session.commit()
    except IntegrityError:
        # 唯一约束处理并发重复点赞，保证计数只在首次记录成功时增加。
        session.rollback()
        article = session.scalar(select(Article).where(Article.slug == slug))
        return article, article is not None
    session.refresh(article)
    invalidate_article_list_cache()
    return article, True
