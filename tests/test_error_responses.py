import json
import unittest

from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient

from backend.app.core.exceptions import build_validation_message
from backend.app.main import app
from backend.app.services.auth import require_admin_session


class ErrorResponseTest(unittest.TestCase):
    """接口错误响应契约：message 必须给出具体的中文原因，前端可直接回显。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_login_missing_fields_names_every_field(self) -> None:
        response = self.client.post("/api/v1/auth/login", json={})
        self.assertEqual(response.status_code, 422)
        payload = response.json()
        self.assertEqual(payload["code"], 422)
        self.assertEqual(payload["status"], 422)
        self.assertTrue(payload["request_id"])
        self.assertIn("请求参数校验失败", payload["message"])
        self.assertIn("账号", payload["message"])
        self.assertIn("密码", payload["message"])
        self.assertIn("必填", payload["message"])

    def test_login_short_field_reports_field_and_constraint(self) -> None:
        response = self.client.post(
            "/api/v1/auth/login", json={"username": "", "password": "secret"}
        )
        self.assertEqual(response.status_code, 422)
        payload = response.json()
        self.assertIn("账号", payload["message"])
        self.assertIn("长度至少为 1 个字符", payload["message"])

    def test_login_wrong_type_reports_type_hint(self) -> None:
        response = self.client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": 123456}
        )
        self.assertEqual(response.status_code, 422)
        payload = response.json()
        self.assertIn("密码", payload["message"])
        self.assertIn("必须是字符串", payload["message"])

    def test_unknown_route_returns_chinese_404_message(self) -> None:
        response = self.client.get("/api/v1/definitely-not-exists")
        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["message"], "请求的资源不存在")

    def test_value_error_message_strips_prefix_and_stays_serializable(self) -> None:
        # schema 里 raise ValueError("中文原因") 的错误：msg 前缀要剥掉，
        # 且 ctx 里的异常对象不能导致响应体 JSON 序列化崩溃（此前的隐藏 bug）。
        errors = [
            {
                "type": "value_error",
                "loc": ("body",),
                "msg": "Value error, 位置经纬度必须同时填写",
                "input": {},
                "ctx": {"error": ValueError("位置经纬度必须同时填写")},
            }
        ]
        self.assertEqual(
            build_validation_message(errors),
            "请求参数校验失败：位置经纬度必须同时填写",
        )
        encoded = jsonable_encoder({"detail": errors}, custom_encoder={Exception: str})
        json.dumps(encoded)

    def test_nested_list_field_location_is_readable(self) -> None:
        errors = [
            {
                "type": "string_too_short",
                "loc": ("body", "skills", 2, "name"),
                "msg": "String should have at least 1 character",
                "input": "",
                "ctx": {"min_length": 1},
            }
        ]
        self.assertEqual(
            build_validation_message(errors),
            "请求参数校验失败：技术栈 第 3 项 名称：长度至少为 1 个字符",
        )

    def test_article_save_with_empty_category_names_category_field(self) -> None:
        # 复现后台“编辑文章保存”时的 422：分类为空必须点名“分类”字段。
        app.dependency_overrides[require_admin_session] = lambda: "admin"
        try:
            response = self.client.put(
                "/api/v1/articles/1",
                json={
                    "slug": "demo-article",
                    "title": "演示文章",
                    "summary": "",
                    "content_markdown": "正文",
                    "cover_image_url": None,
                    "is_repost": False,
                    "author": "站长",
                    "source_url": None,
                    "published_at": None,
                    "updated_at": None,
                    "views": 0,
                    "likes": 0,
                    "tags": [],
                    "category": "",
                    "series_id": None,
                    "series_order": None,
                },
            )
            self.assertEqual(response.status_code, 422)
            payload = response.json()
            self.assertIn("分类", payload["message"])
            self.assertIn("长度至少为 1 个字符", payload["message"])
        finally:
            app.dependency_overrides.pop(require_admin_session, None)


if __name__ == "__main__":
    unittest.main()
