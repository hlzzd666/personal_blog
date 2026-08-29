from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.cache import invalidate_article_list_cache
from backend.app.models.article import Article, ArticleCategory, ArticleTag, ArticleTagLink
from backend.app.schemas.article import ArticlePayload
from backend.app.schemas.taxonomy import (
    ArticleTaxonomyResponse,
    TaxonomyItem,
    TaxonomyListResponse,
    TaxonomyPayload,
)


def _category_count(session: Session, category_id: int) -> int:
    return session.scalar(select(func.count(Article.id)).where(Article.category_id == category_id)) or 0


def _tag_count(session: Session, tag_id: int) -> int:
    return session.scalar(select(func.count(ArticleTagLink.article_id)).where(ArticleTagLink.tag_id == tag_id)) or 0


def _category_item(session: Session, category: ArticleCategory) -> TaxonomyItem:
    return TaxonomyItem(
        id=category.id,
        name=category.name,
        sort_order=category.sort_order,
        article_count=_category_count(session, category.id),
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


def _tag_item(session: Session, tag: ArticleTag) -> TaxonomyItem:
    return TaxonomyItem(
        id=tag.id,
        name=tag.name,
        sort_order=tag.sort_order,
        article_count=_tag_count(session, tag.id),
        created_at=tag.created_at,
        updated_at=tag.updated_at,
    )


def list_categories(session: Session) -> TaxonomyListResponse:
    items = list(
        session.scalars(
            select(ArticleCategory).order_by(ArticleCategory.sort_order.asc(), ArticleCategory.name.asc())
        )
    )
    return TaxonomyListResponse(items=[_category_item(session, item) for item in items], total=len(items))


def list_tags(session: Session) -> TaxonomyListResponse:
    items = list(session.scalars(select(ArticleTag).order_by(ArticleTag.sort_order.asc(), ArticleTag.name.asc())))
    return TaxonomyListResponse(items=[_tag_item(session, item) for item in items], total=len(items))


def get_article_taxonomy(session: Session) -> ArticleTaxonomyResponse:
    return ArticleTaxonomyResponse(
        categories=list_categories(session).items,
        tags=list_tags(session).items,
    )


def create_category(session: Session, payload: TaxonomyPayload) -> TaxonomyItem:
    category = ArticleCategory(**payload.model_dump())
    session.add(category)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ValueError("分类名称已存在") from error
    session.refresh(category)
    invalidate_article_list_cache()
    return _category_item(session, category)


def update_category(session: Session, category: ArticleCategory, payload: TaxonomyPayload) -> TaxonomyItem:
    category.name = payload.name
    category.sort_order = payload.sort_order
    for article in session.scalars(select(Article).where(Article.category_id == category.id)):
        article.category = category.name
    session.add(category)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ValueError("分类名称已存在") from error
    session.refresh(category)
    invalidate_article_list_cache()
    return _category_item(session, category)


def delete_category(session: Session, category: ArticleCategory) -> None:
    if _category_count(session, category.id):
        raise ValueError("分类正在被文章使用，不能删除")
    session.delete(category)
    session.commit()
    invalidate_article_list_cache()


def create_tag(session: Session, payload: TaxonomyPayload) -> TaxonomyItem:
    tag = ArticleTag(**payload.model_dump())
    session.add(tag)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ValueError("标签名称已存在") from error
    session.refresh(tag)
    invalidate_article_list_cache()
    return _tag_item(session, tag)


def update_tag(session: Session, tag: ArticleTag, payload: TaxonomyPayload) -> TaxonomyItem:
    old_name = tag.name
    tag.name = payload.name
    tag.sort_order = payload.sort_order
    for article in session.scalars(select(Article).join(ArticleTagLink).where(ArticleTagLink.tag_id == tag.id)):
        article.tags = [tag.name if value == old_name else value for value in (article.tags or [])]
    session.add(tag)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ValueError("标签名称已存在") from error
    session.refresh(tag)
    invalidate_article_list_cache()
    return _tag_item(session, tag)


def delete_tag(session: Session, tag: ArticleTag) -> None:
    if _tag_count(session, tag.id):
        raise ValueError("标签正在被文章使用，不能删除")
    session.delete(tag)
    session.commit()
    invalidate_article_list_cache()


def apply_article_taxonomy(
    session: Session,
    article: Article,
    payload: ArticlePayload | None = None,
) -> None:
    values = (
        payload.model_dump()
        if payload is not None
        else {"category_id": None, "tag_ids": None, "category": article.category, "tags": article.tags}
    )
    category_id = values.pop("category_id")
    tag_ids = values.pop("tag_ids")

    if category_id is not None:
        category = session.get(ArticleCategory, category_id)
        if category is None:
            raise ValueError("所选分类不存在")
    else:
        category_name = (values.get("category") or "").strip() or "未分类"
        category = session.scalar(select(ArticleCategory).where(ArticleCategory.name == category_name))
        if category is None:
            category = ArticleCategory(name=category_name)
            session.add(category)
            session.flush()

    if tag_ids is not None:
        unique_tag_ids = list(dict.fromkeys(tag_ids))
        tags = list(session.scalars(select(ArticleTag).where(ArticleTag.id.in_(unique_tag_ids)))) if unique_tag_ids else []
        if len(tags) != len(unique_tag_ids):
            raise ValueError("所选标签中存在无效项")
        tags_by_id = {tag.id: tag for tag in tags}
        tags = [tags_by_id[tag_id] for tag_id in unique_tag_ids]
    else:
        tag_names = list(dict.fromkeys((tag or "").strip() for tag in values.get("tags", []) if (tag or "").strip()))
        tags = []
        for tag_name in tag_names:
            tag = session.scalar(select(ArticleTag).where(ArticleTag.name == tag_name))
            if tag is None:
                tag = ArticleTag(name=tag_name)
                session.add(tag)
                session.flush()
            tags.append(tag)

    article.category_id = category.id
    article.category = category.name
    article.tags = [tag.name for tag in tags]
    article.tag_links = [ArticleTagLink(tag=tag) for tag in tags]
