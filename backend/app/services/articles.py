from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.article import Article
from backend.app.schemas.article import ArticleCreate, ArticleUpdate


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
    filters = []
    # 文章不区分草稿和发布状态，public_only 参数保留用于兼容调用方。
    if category:
        filters.append(Article.category == category)
    if tag:
        filters.append(Article.tags.contains([tag]))
    if search:
        keyword = f"%{search.strip()}%"
        filters.append(or_(Article.title.like(keyword), Article.summary.like(keyword)))

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


def get_public_article(session: Session, slug: str) -> Article | None:
    article = session.scalar(
        select(Article).where(Article.slug == slug)
    )
    if article is None:
        return None

    session.execute(update(Article).where(Article.id == article.id).values(views=Article.views + 1))
    session.commit()
    session.refresh(article)
    return article


def get_article(session: Session, article_id: int) -> Article | None:
    return session.get(Article, article_id)


def create_article(session: Session, payload: ArticleCreate) -> Article:
    values = payload.model_dump()
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
    return article


def update_article(session: Session, article: Article, payload: ArticleUpdate) -> Article:
    values = payload.model_dump()
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
    return article


def delete_article(session: Session, article: Article) -> None:
    session.delete(article)
    session.commit()


def like_article(session: Session, slug: str) -> Article | None:
    article = session.scalar(select(Article).where(Article.slug == slug))
    if article is None:
        return None
    session.execute(update(Article).where(Article.id == article.id).values(likes=Article.likes + 1))
    session.commit()
    session.refresh(article)
    return article
