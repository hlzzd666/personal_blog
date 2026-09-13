import unittest
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import get_db_session
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.schemas.auth import AdminSessionResponse
from backend.app.services.auth import require_admin_session


class GuestbookApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        cls.SessionLocal = sessionmaker(bind=cls.engine, expire_on_commit=False)

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.session: Session = self.SessionLocal()
        app.dependency_overrides[get_db_session] = lambda: self.session

    def tearDown(self):
        self.session.close()
        app.dependency_overrides.clear()

    def test_submission_is_pending_and_not_public_until_approved(self):
        with TestClient(app) as client:
            response = client.post("/api/v1/guestbook", json={"nickname": "小航海家", "content": "你好，博客很棒"})
            self.assertEqual(response.status_code, 202)
            self.assertEqual(response.json()["data"]["status"], "pending")
            self.assertEqual(client.get("/api/v1/guestbook").json()["data"]["total"], 0)

    def test_admin_can_approve_and_reply(self):
        from backend.app.models.guestbook import GuestbookMessage

        message = GuestbookMessage(
            nickname="访客", content="留言", visitor_hash="v", content_hash="c", created_at=datetime.now()
        )
        self.session.add(message)
        self.session.commit()
        app.dependency_overrides[require_admin_session] = lambda: AdminSessionResponse(
            username="admin", logged_in_at="2026-01-01T00:00:00Z", expires_at="2026-01-02T00:00:00Z"
        )
        with TestClient(app) as client:
            approved = client.patch(f"/api/v1/guestbook/{message.id}/status", json={"status": "approved"})
            self.assertEqual(approved.status_code, 200)
            replied = client.patch(f"/api/v1/guestbook/{message.id}/reply", json={"admin_reply": "感谢留言"})
            self.assertEqual(replied.status_code, 200)
            public = client.get("/api/v1/guestbook").json()["data"]
            self.assertEqual(public["total"], 1)
            self.assertEqual(public["items"][0]["admin_reply"], "感谢留言")


if __name__ == "__main__":
    unittest.main()
