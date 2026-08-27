import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.config import settings
from backend.app.core.database import get_db_session
from backend.app.main import app
from backend.app.models import Base
from backend.app.models.article import Article
from backend.app.models.content import Series
from backend.app.models.daily_learning import DailyLearningRun, DailyLearningSettings
from backend.app.schemas.auth import AdminSessionResponse
from backend.app.schemas.daily_learning import (
    DailyLearningSettingsUpdate,
    GeneratedQuestion,
    GeneratedQuestionSet,
)
from backend.app.services.auth import require_admin_session
from backend.app.services.daily_learning import (
    DailyLearningAIError,
    DailyLearningConfigurationError,
    _parse_generated_questions,
    encrypt_api_key,
    process_daily_learning_tick,
    update_daily_learning_settings,
    validate_ai_base_url,
)


BEIJING = timezone(timedelta(hours=8))


def generated_questions(prefix: str = "题目") -> GeneratedQuestionSet:
    return GeneratedQuestionSet(
        questions=[
            GeneratedQuestion(
                question=f"{prefix}{index}是什么？",
                answer=f"这是第 {index} 道题的完整参考答案，包含足够的解释。",
            )
            for index in range(1, 11)
        ]
    )


class FakeRedisSession:
    def get(self, _key: str) -> str:
        return json.dumps(
            {
                "username": "tester",
                "created_at": "2026-08-27T00:00:00+00:00",
                "expires_at": "2026-08-28T00:00:00+00:00",
                "csrf_token": "csrf-value",
            }
        )


class DailyLearningTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            "sqlite+pysqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.SessionLocal = sessionmaker(bind=cls.engine, expire_on_commit=False)

    def setUp(self) -> None:
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.session: Session = self.SessionLocal()
        self.previous_encryption_key = settings.daily_learning_encryption_key
        settings.daily_learning_encryption_key = Fernet.generate_key().decode()

    def tearDown(self) -> None:
        settings.daily_learning_encryption_key = self.previous_encryption_key
        self.session.close()
        app.dependency_overrides.clear()

    def add_settings(self, *, enabled: bool = True) -> DailyLearningSettings:
        record = DailyLearningSettings(
            id=1,
            enabled=enabled,
            publish_time=datetime.strptime("09:00", "%H:%M").time(),
            ai_base_url="https://api.example.com/v1",
            ai_model="test-model",
            encrypted_api_key=encrypt_api_key("secret-key"),
            generation_instructions="生成严谨的前端题目",
            tags=["前端基础", "每日练习"],
        )
        self.session.add(record)
        self.session.commit()
        return record

    def test_base_url_rejects_non_https_and_private_addresses(self) -> None:
        with self.assertRaises(DailyLearningConfigurationError):
            validate_ai_base_url("http://api.example.com/v1")
        with patch(
            "backend.app.services.daily_learning.socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("127.0.0.1", 443))],
        ):
            with self.assertRaises(DailyLearningConfigurationError):
                validate_ai_base_url("https://api.example.com/v1")

    def test_settings_encrypt_key_and_never_serialize_it(self) -> None:
        with patch(
            "backend.app.services.daily_learning.socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("93.184.216.34", 443))],
        ):
            response = update_daily_learning_settings(
                self.session,
                DailyLearningSettingsUpdate(
                    enabled=True,
                    publish_time="09:00",
                    ai_base_url="https://api.example.com/v1/",
                    ai_model="test-model",
                    api_key="plain-secret",
                    generation_instructions="测试要求",
                    tags=[" Vue ", "每日问答", "Vue"],
                ),
            )
        record = self.session.get(DailyLearningSettings, 1)
        self.assertNotIn("plain-secret", record.encrypted_api_key)
        payload = response.model_dump()
        self.assertTrue(payload["api_key_configured"])
        self.assertNotIn("api_key", payload)
        self.assertNotIn("encrypted_api_key", payload)
        self.assertEqual(payload["tags"], ["Vue", "每日问答"])

    def test_generated_content_requires_exactly_ten_unique_questions(self) -> None:
        valid = generated_questions().model_dump_json()
        self.assertEqual(len(_parse_generated_questions(valid, []).questions), 10)

        invalid = {"questions": generated_questions().model_dump()["questions"][:9]}
        with self.assertRaises(DailyLearningAIError):
            _parse_generated_questions(json.dumps(invalid, ensure_ascii=False), [])

        duplicate = generated_questions().model_dump()
        duplicate["questions"][9] = duplicate["questions"][0]
        with self.assertRaises(DailyLearningAIError):
            _parse_generated_questions(json.dumps(duplicate, ensure_ascii=False), [])

    def test_settings_require_at_least_one_tag(self) -> None:
        with self.assertRaises(ValidationError):
            DailyLearningSettingsUpdate(tags=[" ", ""])

    def test_tick_publishes_once_and_orders_series(self) -> None:
        self.add_settings()
        calls = 0

        def generator(_configuration, _previous):
            nonlocal calls
            calls += 1
            return generated_questions()

        now = datetime(2026, 8, 27, 9, 0, tzinfo=BEIJING)
        with (
            patch("backend.app.services.daily_learning._acquire_runner_lock", return_value="token"),
            patch("backend.app.services.daily_learning._release_runner_lock"),
            patch("backend.app.services.daily_learning.validate_ai_base_url", side_effect=lambda value: value),
            patch("backend.app.services.daily_learning.invalidate_article_list_cache"),
        ):
            self.assertEqual(
                process_daily_learning_tick(self.session, now=now, question_generator=generator),
                "published",
            )
            self.assertEqual(
                process_daily_learning_tick(self.session, now=now, question_generator=generator),
                "already-published",
            )

        articles = list(self.session.scalars(select(Article)))
        self.assertEqual(len(articles), 1)
        self.assertEqual(calls, 1)
        self.assertEqual(articles[0].slug, "2026-08-27-学习记录")
        self.assertEqual(articles[0].category, "每日问答")
        self.assertEqual(articles[0].author, "AI自动生成")
        self.assertEqual(articles[0].tags, ["前端基础", "每日练习"])
        self.assertEqual(articles[0].series_order, 1)
        series = self.session.scalar(select(Series).where(Series.slug == "daily-learning"))
        self.assertEqual(series.title, "今日份学习")
        run = self.session.scalar(select(DailyLearningRun))
        self.assertEqual(run.status, "succeeded")
        self.assertEqual(run.article_id, articles[0].id)

    def test_failed_generation_retries_three_times(self) -> None:
        self.add_settings()

        def generator(_configuration, _previous):
            raise DailyLearningAIError("provider unavailable")

        start = datetime(2026, 8, 27, 9, 0, tzinfo=BEIJING)
        with (
            patch("backend.app.services.daily_learning._acquire_runner_lock", return_value="token"),
            patch("backend.app.services.daily_learning._release_runner_lock"),
            patch("backend.app.services.daily_learning.validate_ai_base_url", side_effect=lambda value: value),
        ):
            self.assertEqual(
                process_daily_learning_tick(self.session, now=start, question_generator=generator),
                "failed",
            )
            self.assertEqual(
                process_daily_learning_tick(
                    self.session, now=start + timedelta(minutes=11), question_generator=generator
                ),
                "failed",
            )
            self.assertEqual(
                process_daily_learning_tick(
                    self.session, now=start + timedelta(minutes=42), question_generator=generator
                ),
                "failed",
            )

        run = self.session.scalar(select(DailyLearningRun))
        self.assertEqual(run.attempt_count, 3)
        self.assertEqual(run.status, "failed")
        self.assertIsNone(run.next_retry_at)
        self.assertIsNone(self.session.scalar(select(Article)))

    def test_admin_endpoints_require_session_and_csrf(self) -> None:
        def override_session():
            yield self.session

        app.dependency_overrides[get_db_session] = override_session
        with TestClient(app) as client:
            self.assertEqual(client.get("/api/v1/daily-learning/settings").status_code, 401)

        with patch("backend.app.services.auth.get_redis_client", return_value=FakeRedisSession()):
            with TestClient(app) as client:
                client.cookies.set(settings.admin_session_cookie_name, "session-token")
                client.cookies.set(settings.admin_csrf_cookie_name, "csrf-value")
                response = client.put(
                    "/api/v1/daily-learning/settings",
                    json={
                        "enabled": False,
                        "publish_time": "09:00",
                        "ai_base_url": "",
                        "ai_model": "",
                        "api_key": None,
                        "generation_instructions": "",
                    },
                )
            self.assertEqual(response.status_code, 403)

    def test_settings_api_does_not_return_key(self) -> None:
        self.add_settings(enabled=False)

        def override_session():
            yield self.session

        def override_admin() -> AdminSessionResponse:
            return AdminSessionResponse(
                username="tester",
                logged_in_at="2026-08-27T00:00:00+00:00",
                expires_at="2026-08-28T00:00:00+00:00",
            )

        app.dependency_overrides[get_db_session] = override_session
        app.dependency_overrides[require_admin_session] = override_admin
        with TestClient(app) as client:
            response = client.get("/api/v1/daily-learning/settings")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertTrue(data["api_key_configured"])
        self.assertNotIn("api_key", data)
        self.assertNotIn("encrypted_api_key", data)


if __name__ == "__main__":
    unittest.main()
