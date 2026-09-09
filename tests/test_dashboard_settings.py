import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.auth import require_admin_session
from backend.app.services.site_settings import DEFAULT_SITE_SETTINGS


class DashboardSettingsTest(unittest.TestCase):
    def setUp(self) -> None:
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.settings_path = Path(directory.name) / "site_settings.json"
        for name, value in (("DATA_DIR", Path(directory.name)), ("SETTINGS_PATH", self.settings_path)):
            patcher = patch(f"backend.app.services.site_settings.{name}", value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.payload = DEFAULT_SITE_SETTINGS.model_dump(mode="json")

    def authorize(self) -> None:
        app.dependency_overrides[require_admin_session] = lambda: "admin"
        self.addCleanup(app.dependency_overrides.pop, require_admin_session)

    def test_legacy_settings_receive_dashboard_defaults(self) -> None:
        self.payload.pop("dashboard_years")
        self.payload.pop("dashboard_show_entry")
        self.settings_path.write_text(json.dumps(self.payload), encoding="utf-8")
        response = self.client.get("/api/v1/site-settings")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["dashboard_years"], [2024, 2025, 2026])
        self.assertTrue(response.json()["data"]["dashboard_show_entry"])

    def test_admin_save_persists_years_and_visibility_for_public_read(self) -> None:
        self.authorize()
        self.payload.update(dashboard_years=[2026, 2022, 2026], dashboard_show_entry=False)
        saved = self.client.put("/api/v1/site-settings", json=self.payload)
        self.assertEqual(saved.status_code, 200)
        public = self.client.get("/api/v1/site-settings").json()["data"]
        self.assertEqual(public["dashboard_years"], [2022, 2026])
        self.assertFalse(public["dashboard_show_entry"])
        self.assertEqual(json.loads(self.settings_path.read_text(encoding="utf-8")), public)
        self.assertEqual(public["quotes"], self.payload["quotes"])

    def test_invalid_years_are_rejected_without_overwriting_settings(self) -> None:
        self.authorize()
        self.client.get("/api/v1/site-settings")
        before = self.settings_path.read_bytes()
        for years in ([], [1969], [2101], [2025.5], [True], ["2026"], list(range(2000, 2013))):
            with self.subTest(years=years):
                response = self.client.put("/api/v1/site-settings", json={**self.payload, "dashboard_years": years})
                self.assertEqual(response.status_code, 422)
                self.assertIn("大屏可选年份", response.json()["message"])
                self.assertEqual(self.settings_path.read_bytes(), before)

    def test_anonymous_write_is_rejected(self) -> None:
        response = self.client.put("/api/v1/site-settings", json=self.payload)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(self.settings_path.exists())


if __name__ == "__main__":
    unittest.main()
