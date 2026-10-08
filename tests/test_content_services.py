import hashlib
import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import get_db_session
from backend.app.core.cache import build_article_list_cache_key
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.models.article import Article, ArticleCategory, ArticleTag
from backend.app.models.content import Note, Series
from backend.app.models.daily_learning import DailyLearningRun
from backend.app.schemas.auth import AdminSessionResponse
from backend.app.schemas.article import ArticleCreate
from backend.app.schemas.content import NotePayload, SeriesPayload
from backend.app.schemas.taxonomy import TaxonomyPayload
from backend.app.services.articles import get_article_context, list_articles
from backend.app.services.articles import create_article
from backend.app.services.auth import require_admin_session
from backend.app.services.content import (
    create_note,
    create_series,
    delete_series,
    get_series_detail,
    list_notes,
    next_note_slug,
)
from backend.app.services.taxonomy import (
    apply_article_taxonomy,
    create_category,
    create_tag,
    delete_category,
    delete_tag,
    list_categories,
    list_tags,
    update_category,
    update_tag,
)


def _json_contains(document: str, candidate: str) -> int:
    try:
        return int(json.loads(candidate) in json.loads(document))
    except (TypeError, ValueError):
        return 0


class ContentServicesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            "sqlite+pysqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(cls.engine, "connect")
        def configure_sqlite(connection, _record) -> None:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.create_function("json_contains", 2, _json_contains)

        cls.SessionLocal = sessionmaker(bind=cls.engine, expire_on_commit=False)

    def setUp(self) -> None:
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.session: Session = self.SessionLocal()

    def tearDown(self) -> None:
        self.session.close()
        app.dependency_overrides.clear()

    def article(
        self,
        slug: str,
        *,
        series_id: int | None = None,
        series_order: int | None = None,
        tags: list[str] | None = None,
        category: str = "技术",
        published_offset: int = 0,
    ) -> Article:
        article = Article(
            slug=slug,
            title=slug,
            summary=f"{slug} summary",
            content_markdown=f"# {slug}",
            author="tester",
            tags=tags or [],
            category=category,
            series_id=series_id,
            series_order=series_order,
            published_at=datetime(2026, 1, 1) + timedelta(days=published_offset),
            views=0,
            likes=0,
        )
        self.session.add(article)
        self.session.commit()
        self.session.refresh(article)
        return article

    def test_series_slug_conflict_and_article_order(self) -> None:
        series = create_series(
            self.session,
            SeriesPayload(slug="deep-vue", title="Vue 深入", sort_order=10),
        )
        with self.assertRaisesRegex(ValueError, "专题别名已存在"):
            create_series(
                self.session,
                SeriesPayload(slug="deep-vue", title="重复专题"),
            )

        self.article("second", series_id=series.id, series_order=20, published_offset=1)
        self.article("first", series_id=series.id, series_order=10, published_offset=2)
        detail = get_series_detail(self.session, self.session.get(Series, series.id))
        self.assertEqual([article.slug for article in detail.articles], ["first", "second"])

    def test_next_note_slug_uses_highest_sequence_for_day(self) -> None:
        self.session.add_all(
            [
                Note(slug="20260909-1", content_markdown="one", tags=[]),
                Note(slug="20260909-3", content_markdown="three", tags=[]),
                Note(slug="20260909-draft", content_markdown="draft", tags=[]),
                Note(slug="20260908-9", content_markdown="old", tags=[]),
            ]
        )
        self.session.commit()

        self.assertEqual(next_note_slug(self.session, datetime(2026, 9, 9).date()), "20260909-4")

    def test_series_delete_unlinks_articles(self) -> None:
        created = create_series(
            self.session,
            SeriesPayload(slug="temporary", title="临时专题"),
        )
        article = self.article("kept-article", series_id=created.id, series_order=1)
        delete_series(self.session, self.session.get(Series, created.id))
        self.session.refresh(article)
        self.assertIsNone(article.series_id)
        self.assertIsNone(article.series_order)
        self.assertIsNotNone(self.session.get(Article, article.id))

    def test_article_context_prefers_series_and_shared_tags(self) -> None:
        created = create_series(
            self.session,
            SeriesPayload(slug="route", title="阅读路线"),
        )
        first = self.article(
            "first",
            series_id=created.id,
            series_order=10,
            tags=["vue"],
            published_offset=3,
        )
        current = self.article(
            "current",
            series_id=created.id,
            series_order=20,
            tags=["vue", "api"],
            published_offset=2,
        )
        third = self.article("third", series_id=created.id, series_order=30, published_offset=1)
        tagged = self.article("tagged", tags=["vue", "api"], published_offset=10)
        self.article("category-only", category="技术", published_offset=20)

        context = get_article_context(self.session, current.slug)
        self.assertEqual(context.previous.id, first.id)
        self.assertEqual(context.next.id, third.id)
        self.assertEqual(context.related[0].id, first.id)
        self.assertIn(tagged.id, [article.id for article in context.related])
        self.assertNotIn(current.id, [article.id for article in context.related])

    def test_article_search_matches_slug(self) -> None:
        article = self.article("2026-08-27-学习记录")
        article.title = "每日学习问答"
        article.summary = "前端知识练习"
        article.content_markdown = "# 今日内容"
        self.session.commit()

        items, total = list_articles(
            self.session,
            public_only=False,
            page=1,
            page_size=20,
            search="2026-08-27-学习记录",
        )

        self.assertEqual(total, 1)
        self.assertEqual([item.id for item in items], [article.id])

    def test_article_list_filters_by_attribute_and_time_ranges(self) -> None:
        original = self.article("original", published_offset=1)
        repost = self.article("repost", published_offset=3)
        repost.is_repost = True
        original.updated_at = datetime(2026, 2, 1, 10, 0)
        repost.updated_at = datetime(2026, 2, 3, 10, 0)
        self.session.commit()

        items, total = list_articles(
            self.session,
            public_only=False,
            page=1,
            page_size=20,
            is_repost=True,
            published_from=datetime(2026, 1, 3),
            published_to=datetime(2026, 1, 5),
            updated_from=datetime(2026, 2, 2),
            updated_to=datetime(2026, 2, 4),
        )

        self.assertEqual(total, 1)
        self.assertEqual([item.id for item in items], [repost.id])

    def test_learning_articles_only_appear_in_series_and_management(self) -> None:
        series = create_series(self.session, SeriesPayload(slug="daily-learning", title="今日份学习"))
        ordinary_series = create_series(self.session, SeriesPayload(slug="ai-tools", title="AI 工具"))
        older = self.article("older", tags=["vue"], published_offset=0)
        latest = self.article("latest", category="AI", series_id=ordinary_series.id, tags=["vue"], published_offset=1)
        daily = self.article("daily", series_id=series.id, category="AI 问答", tags=["定时问答"], published_offset=70)
        renamed = self.article("renamed", series_id=series.id, category="学习", tags=["定时问答"], published_offset=71)
        legacy = self.article("legacy", category="AI 问答", tags=["定时问答"], published_offset=72)
        self.session.add(DailyLearningRun(
            run_date=datetime(2026, 3, 14).date(), scheduled_for=datetime(2026, 3, 14),
            status="succeeded", article_id=legacy.id,
        ))
        self.session.commit()
        app.dependency_overrides[get_db_session] = lambda: self.session
        app.dependency_overrides[require_admin_session] = lambda: "admin"

        with (
            patch("backend.app.services.articles.build_article_list_cache_key", return_value=None),
            patch("backend.app.services.articles.invalidate_article_list_cache"),
            TestClient(app) as client,
        ):
            first = client.get("/api/v1/articles", params={"page_size": 1})
            self.assertEqual(first.status_code, 200)
            data = first.json()["data"]
            self.assertEqual(data["total"], 2)
            self.assertEqual([item["id"] for item in data["items"]], [latest.id])
            self.assertEqual(data["stats"]["months"], [{"key": "2026-01", "count": 2}])
            self.assertEqual({item["name"] for item in data["stats"]["categories"]}, {"技术", "AI"})
            self.assertEqual(data["stats"]["tags"], [{"name": "vue", "count": 2}])
            second = client.get("/api/v1/articles", params={"page_size": 1, "page": 2}).json()["data"]
            self.assertEqual([item["id"] for item in second["items"]], [older.id])
            for params in ({"category": "AI 问答"}, {"tag": "定时问答"}, {"search": "legacy"}):
                with self.subTest(params=params):
                    filtered = client.get("/api/v1/articles", params=params).json()["data"]
                    self.assertEqual(filtered["items"], [])
                    self.assertEqual(filtered["total"], 0)
                    self.assertEqual(filtered["stats"]["months"], [])

            managed = client.get("/api/v1/articles/manage").json()["data"]
            self.assertEqual(managed["total"], 5)
            self.assertEqual({item["id"] for item in managed["items"]}, {older.id, latest.id, daily.id, renamed.id, legacy.id})
            self.assertIn({"name": "AI 问答", "count": 2}, managed["stats"]["categories"])
            topic = client.get("/api/v1/series/daily-learning").json()["data"]
            self.assertEqual([item["id"] for item in topic["articles"]], [renamed.id, daily.id])
            self.assertEqual(client.get("/api/v1/articles/daily").status_code, 200)

        context = get_article_context(self.session, older.slug)
        self.assertEqual(context.next.id, latest.id)
        self.assertEqual([item.id for item in context.related], [latest.id])
        daily_context = get_article_context(self.session, daily.slug)
        self.assertEqual(daily_context.previous.id, renamed.id)
        self.assertEqual(daily_context.series.slug, "daily-learning")

    def test_public_article_cache_does_not_reuse_unfiltered_list(self) -> None:
        params = dict(
            public_only=True, page=1, page_size=6, category=None, tag=None, search=None,
            is_repost=None, published_from=None, published_to=None, updated_from=None, updated_to=None,
        )
        legacy_digest = hashlib.sha256(
            json.dumps(params, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        with patch("backend.app.core.cache.get_redis_client") as redis:
            redis.return_value.get.return_value = "0"
            public_key = build_article_list_cache_key(**params)
        self.assertIsNotNone(public_key)
        self.assertNotEqual(public_key, f"personal-blog:articles:list:0:{legacy_digest}")

    def test_notes_filter_uses_exact_json_membership(self) -> None:
        create_note(
            self.session,
            NotePayload(slug="vue-note", content_markdown="Vue", tags=["vue"]),
        )
        create_note(
            self.session,
            NotePayload(slug="vue-router-note", content_markdown="Router", tags=["vue-router"]),
        )
        result = list_notes(self.session, page=1, page_size=20, tag="vue")
        self.assertEqual([note.slug for note in result.items], ["vue-note"])

    def test_article_taxonomy_mirrors_existing_article_fields(self) -> None:
        category = create_category(self.session, TaxonomyPayload(name="技术", sort_order=2))
        tag = create_tag(self.session, TaxonomyPayload(name="vue", sort_order=1))
        article = self.article("taxonomy-article", tags=["vue"], category="技术")

        apply_article_taxonomy(self.session, self.session.get(Article, article.id))
        self.session.commit()
        self.session.refresh(article)
        self.assertEqual(article.category_id, category.id)
        self.assertEqual(article.tag_ids, [tag.id])
        self.assertEqual(list_categories(self.session).items[0].article_count, 1)
        self.assertEqual(list_tags(self.session).items[0].article_count, 1)

        update_category(self.session, self.session.get(ArticleCategory, category.id), TaxonomyPayload(name="工程", sort_order=0))
        update_tag(self.session, self.session.get(ArticleTag, tag.id), TaxonomyPayload(name="vue3", sort_order=0))
        self.session.refresh(article)
        self.assertEqual(article.category, "工程")
        self.assertEqual(article.tags, ["vue3"])

        with self.assertRaisesRegex(ValueError, "正在被文章使用"):
            delete_category(self.session, self.session.get(ArticleCategory, category.id))
        with self.assertRaisesRegex(ValueError, "正在被文章使用"):
            delete_tag(self.session, self.session.get(ArticleTag, tag.id))

    def test_article_create_uses_taxonomy_ids(self) -> None:
        category = create_category(self.session, TaxonomyPayload(name="前端", sort_order=0))
        tag = create_tag(self.session, TaxonomyPayload(name="vue", sort_order=0))
        article = create_article(
            self.session,
            ArticleCreate(
                slug="taxonomy-id-article",
                title="Taxonomy ID",
                content_markdown="# Taxonomy ID",
                category="旧分类",
                category_id=category.id,
                tags=["旧标签"],
                tag_ids=[tag.id],
            ),
        )
        self.assertEqual(article.category, "前端")
        self.assertEqual(article.tags, ["vue"])
        self.assertEqual(article.category_id, category.id)
        self.assertEqual(article.tag_ids, [tag.id])

    def test_admin_write_requires_session(self) -> None:
        def override_session():
            yield self.session

        app.dependency_overrides[get_db_session] = override_session
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/series",
                json={"slug": "protected", "title": "Protected", "description": "", "sort_order": 0},
            )
        self.assertEqual(response.status_code, 401)

    def test_admin_api_reports_slug_conflict(self) -> None:
        def override_session():
            yield self.session

        def override_admin() -> AdminSessionResponse:
            return AdminSessionResponse(
                username="tester",
                logged_in_at="2026-01-01T00:00:00+00:00",
                expires_at="2026-01-02T00:00:00+00:00",
            )

        app.dependency_overrides[get_db_session] = override_session
        app.dependency_overrides[require_admin_session] = override_admin
        payload = {"slug": "api-series", "title": "API Series", "description": "", "sort_order": 0}
        with TestClient(app) as client:
            self.assertEqual(client.post("/api/v1/series", json=payload).status_code, 200)
            response = client.post("/api/v1/series", json=payload)
        self.assertEqual(response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
