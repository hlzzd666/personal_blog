import unittest
from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import get_db_session
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.schemas.auth import AdminSessionResponse
from backend.app.schemas.visitor_location import VisitorLocation
from backend.app.services.auth import require_admin_session


class VisitorRecordsTest(unittest.TestCase):
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

        cls.SessionLocal = sessionmaker(bind=cls.engine, expire_on_commit=False)

    def setUp(self) -> None:
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.session: Session = self.SessionLocal()
        app.dependency_overrides[get_db_session] = self.override_session
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def tearDown(self) -> None:
        self.session.close()
        app.dependency_overrides.clear()

    def override_session(self):
        yield self.session

    def authorize(self) -> None:
        app.dependency_overrides[require_admin_session] = lambda: AdminSessionResponse(
            username="tester",
            logged_in_at="2026-09-09T00:00:00+00:00",
            expires_at="2026-09-10T00:00:00+00:00",
        )

    def test_public_record_saves_request_fields_without_authorization(self) -> None:
        location = VisitorLocation(
            ip="203.0.113.8",
            city="上海",
            region="上海市",
            country="中国",
            location_available=True,
        )
        with patch("backend.app.api.router.resolve_visitor_location", return_value=location):
            response = self.client.post(
                "/api/v1/visitor-records",
                json={"page_path": "/articles/demo?from=home"},
                headers={
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
                    "Referer": "https://example.com/",
                    "X-Forwarded-For": "203.0.113.8",
                },
            )

        self.assertEqual(response.status_code, 200)
        record = response.json()["data"]
        self.assertEqual(record["ip"], "testclient")
        self.assertEqual(record["city"], "上海")
        self.assertEqual(record["page_path"], "/articles/demo?from=home")
        self.assertEqual(record["device_type"], "mobile")

    def test_untrusted_forwarded_ip_is_ignored(self) -> None:
        with patch(
            "backend.app.api.router.resolve_visitor_location",
            return_value=VisitorLocation(ip="testclient", location_available=False),
        ) as resolve:
            response = self.client.post(
                "/api/v1/visitor-records",
                json={"page_path": "/"},
                headers={"X-Forwarded-For": "198.51.100.20"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(resolve.call_args.args[0], "testclient")

    def test_location_failure_does_not_drop_visit(self) -> None:
        with patch(
            "backend.app.api.router.resolve_visitor_location",
            side_effect=RuntimeError("定位服务不可用"),
        ):
            response = self.client.post("/api/v1/visitor-records", json={"page_path": "/privacy"})

        self.assertEqual(response.status_code, 200)
        record = response.json()["data"]
        self.assertEqual(record["page_path"], "/privacy")
        self.assertIsNone(record["city"])

    def test_invalid_page_path_is_rejected(self) -> None:
        response = self.client.post("/api/v1/visitor-records", json={"page_path": "articles"})
        self.assertEqual(response.status_code, 422)

    def test_admin_list_and_delete_are_protected(self) -> None:
        self.client.post("/api/v1/visitor-records", json={"page_path": "/"})
        unauthorized = self.client.get("/api/v1/visitor-records")
        self.assertEqual(unauthorized.status_code, 401)

        self.authorize()
        listed = self.client.get("/api/v1/visitor-records")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json()["data"]["total"], 1)
        record_id = listed.json()["data"]["items"][0]["id"]

        deleted = self.client.delete(f"/api/v1/visitor-records/{record_id}")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/visitor-records").json()["data"]["total"], 0)

    def test_batch_delete_requires_date_range_and_deletes_matching_rows(self) -> None:
        for path in ("/", "/about", "/articles"):
            self.client.post("/api/v1/visitor-records", json={"page_path": path})
        self.authorize()

        missing_range = self.client.delete("/api/v1/visitor-records")
        self.assertEqual(missing_range.status_code, 422)

        deleted = self.client.delete(
            "/api/v1/visitor-records",
            params={"visited_from": datetime.now().date().isoformat()},
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.json()["data"]["deleted_count"], 3)


if __name__ == "__main__":
    unittest.main()
