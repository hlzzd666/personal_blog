import html
import json
import re
from datetime import UTC, datetime
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, tostring

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.article import Article
from backend.app.models.content import Note, Series


def _absolute_url(path: str) -> str:
    return urljoin(f"{settings.site_url.rstrip('/')}/", path.lstrip("/"))


def _web_url(path: str = "") -> str:
    base = settings.web_base_path.strip("/")
    suffix = path.lstrip("/")
    return _absolute_url("/".join(part for part in (base, suffix) if part))


def _plain_markdown(value: str, limit: int = 180) -> str:
    value = re.sub(r"```[\s\S]*?```", " ", value)
    value = re.sub(r"[#>*_`\[\]()!-]", " ", value)
    return re.sub(r"\s+", " ", value).strip()[:limit]


def _iso_date(value: datetime | None) -> str:
    date = value or datetime.now(UTC)
    if date.tzinfo is None:
        date = date.replace(tzinfo=UTC)
    return date.isoformat()


def _read_index_shell() -> str:
    index_path = settings.web_dist_path / "index.html"
    if index_path.is_file():
        return index_path.read_text(encoding="utf-8")
    return """<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>个人博客</title></head><body><div id=\"app\"></div></body></html>"""


def build_metadata_shell(
    *,
    title: str,
    description: str,
    canonical_url: str,
    page_type: str = "website",
    image_url: str | None = None,
    json_ld: dict | None = None,
    published_at: datetime | None = None,
) -> str:
    shell = _read_index_shell()
    full_title = f"{title} | 个人博客"
    shell = re.sub(r"<title>[\s\S]*?</title>", f"<title>{html.escape(full_title)}</title>", shell, count=1)
    tags = [
        f'<meta name="description" content="{html.escape(description, quote=True)}">',
        f'<link rel="canonical" href="{html.escape(canonical_url, quote=True)}">',
        f'<meta property="og:title" content="{html.escape(title, quote=True)}">',
        f'<meta property="og:description" content="{html.escape(description, quote=True)}">',
        f'<meta property="og:type" content="{html.escape(page_type, quote=True)}">',
        f'<meta property="og:url" content="{html.escape(canonical_url, quote=True)}">',
    ]
    if image_url:
        tags.append(f'<meta property="og:image" content="{html.escape(_absolute_url(image_url), quote=True)}">')
    if published_at:
        tags.append(f'<meta property="article:published_time" content="{_iso_date(published_at)}">')
    if json_ld:
        serialized = json.dumps(json_ld, ensure_ascii=False).replace("</", "<\\/")
        tags.append(f'<script type="application/ld+json">{serialized}</script>')
    return shell.replace("</head>", f"{' '.join(tags)}</head>", 1)


def article_metadata_shell(session: Session, slug: str) -> tuple[str, bool]:
    article = session.scalar(select(Article).where(Article.slug == slug))
    if article is None:
        return generic_metadata_shell("文章不存在", "没有找到这篇文章。", f"articles/{slug}"), False
    canonical = _web_url(f"articles/{article.slug}")
    description = article.summary or _plain_markdown(article.content_markdown)
    return build_metadata_shell(
        title=article.title,
        description=description,
        canonical_url=canonical,
        page_type="article",
        image_url=article.cover_image_url,
        published_at=article.published_at or article.created_at,
        json_ld={
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": article.title,
            "description": description,
            "datePublished": _iso_date(article.published_at or article.created_at),
            "dateModified": _iso_date(article.updated_at),
            "author": {"@type": "Person", "name": article.author},
            "mainEntityOfPage": canonical,
            **({"image": _absolute_url(article.cover_image_url)} if article.cover_image_url else {}),
        },
    ), True


def series_metadata_shell(session: Session, slug: str) -> tuple[str, bool]:
    series = session.scalar(select(Series).where(Series.slug == slug))
    if series is None:
        return generic_metadata_shell("专题不存在", "没有找到这个专题。", f"series/{slug}"), False
    description = series.description or f"专题《{series.title}》的完整文章航线。"
    canonical = _web_url(f"series/{series.slug}")
    return build_metadata_shell(
        title=series.title,
        description=description,
        canonical_url=canonical,
        image_url=series.cover_image_url,
        json_ld={
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": series.title,
            "description": description,
            "url": canonical,
        },
    ), True


def note_metadata_shell(session: Session, slug: str) -> tuple[str, bool]:
    note = session.scalar(select(Note).where(Note.slug == slug))
    if note is None:
        return generic_metadata_shell("动态不存在", "没有找到这条短动态。", f"notes/{slug}"), False
    description = _plain_markdown(note.content_markdown)
    title = description[:36] or "短动态"
    canonical = _web_url(f"notes/{note.slug}")
    return build_metadata_shell(
        title=title,
        description=description,
        canonical_url=canonical,
        page_type="article",
        published_at=note.published_at or note.created_at,
        json_ld={
            "@context": "https://schema.org",
            "@type": "SocialMediaPosting",
            "articleBody": description,
            "datePublished": _iso_date(note.published_at or note.created_at),
            "url": canonical,
        },
    ), True


def generic_metadata_shell(title: str, description: str, path: str = "") -> str:
    return build_metadata_shell(
        title=title,
        description=description,
        canonical_url=_web_url(path),
    )


def build_rss(session: Session) -> str:
    articles = list(
        session.scalars(
            select(Article)
            .order_by(Article.published_at.is_(None), Article.published_at.desc(), Article.created_at.desc())
            .limit(50)
        )
    )
    rss = Element("rss", {"version": "2.0"})
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = "个人博客"
    SubElement(channel, "link").text = _web_url()
    SubElement(channel, "description").text = "个人博客文章更新"
    SubElement(channel, "language").text = "zh-CN"
    for article in articles:
        item = SubElement(channel, "item")
        SubElement(item, "title").text = article.title
        link = _web_url(f"articles/{article.slug}")
        SubElement(item, "link").text = link
        SubElement(item, "guid", {"isPermaLink": "true"}).text = link
        SubElement(item, "description").text = article.summary or _plain_markdown(article.content_markdown)
        date = article.published_at or article.created_at
        if date.tzinfo is None:
            date = date.replace(tzinfo=UTC)
        SubElement(item, "pubDate").text = format_datetime(date)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(rss, encoding="unicode")


def build_sitemap(session: Session) -> str:
    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    root = Element("urlset", {"xmlns": namespace})

    def add_url(location: str, modified: datetime | None = None) -> None:
        node = SubElement(root, "url")
        SubElement(node, "loc").text = location
        if modified:
            SubElement(node, "lastmod").text = _iso_date(modified)

    for path in ("", "articles", "series", "notes", "about", "privacy"):
        add_url(_web_url(path))
    for article in session.scalars(select(Article)):
        add_url(_web_url(f"articles/{article.slug}"), article.updated_at)
    for series in session.scalars(select(Series)):
        add_url(_web_url(f"series/{series.slug}"), series.updated_at)
    for note in session.scalars(select(Note)):
        add_url(_web_url(f"notes/{note.slug}"), note.updated_at)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(root, encoding="unicode")


def build_robots() -> str:
    return f"User-agent: *\nAllow: /\nSitemap: {_absolute_url('sitemap.xml')}\n"
