import json
import unittest
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import get_db_session
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.models.article import Article
from backend.app.models.content import Note, Series
from backend.app.schemas.auth import AdminSessionResponse
from backend.app.schemas.content import NotePayload, SeriesPayload
from backend.app.services.articles import get_article_context
from backend.app.services.auth import require_admin_session
from backend.app.services.content import (
    create_note,
    create_series,
    delete_series,
    get_series_detail,
    list_notes,
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

        self.article("second", series_id=series.id, series_order=20)
        self.article("first", series_id=series.id, series_order=10)
        detail = get_series_detail(self.session, self.session.get(Series, series.id))
        self.assertEqual([article.slug for article in detail.articles], ["first", "second"])

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
        first = self.article("first", series_id=created.id, series_order=10, tags=["vue"])
        current = self.article("current", series_id=created.id, series_order=20, tags=["vue", "api"])
        third = self.article("third", series_id=created.id, series_order=30)
        tagged = self.article("tagged", tags=["vue", "api"], published_offset=10)
        self.article("category-only", category="技术", published_offset=20)

        context = get_article_context(self.session, current.slug)
        self.assertEqual(context.previous.id, first.id)
        self.assertEqual(context.next.id, third.id)
        self.assertEqual(context.related[0].id, first.id)
        self.assertIn(tagged.id, [article.id for article in context.related])
        self.assertNotIn(current.id, [article.id for article in context.related])

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
