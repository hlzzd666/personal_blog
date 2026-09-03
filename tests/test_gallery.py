import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from PIL import Image
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import get_db_session
from backend.app.core.config import settings
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.models.gallery import GalleryCharacter
from backend.app.schemas.gallery import GalleryCharacterPayload, GallerySettingsPayload
from backend.app.services.auth import require_admin_session
from backend.app.services.gallery import (
    create_gallery_character,
    delete_gallery_character,
    get_gallery,
    reorder_gallery_characters,
    update_gallery_character,
    update_gallery_settings,
)
from backend.app.services.media import _collect_reference_candidates, _find_references
from backend.app.services.gallery_media import (
    GalleryImageError,
    create_gallery_image_variants,
    regenerate_gallery_image_derivatives,
)


def character_payload(index: int, *, visible: bool = True) -> GalleryCharacterPayload:
    return GalleryCharacterPayload(
        name=f"人物 {index}",
        epithet=f"称号 {index}",
        faction="测试势力",
        bounty="未知",
        ability="测试能力",
        description="用于验证 3D 展厅人物服务。",
        quote="向伟大航路前进。",
        poster_url=None,
        is_visible=visible,
    )


class GalleryTest(unittest.TestCase):
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
        self.upload_directory = TemporaryDirectory()
        self.previous_upload_dir = settings.upload_dir
        settings.upload_dir = self.upload_directory.name
        app.dependency_overrides[get_db_session] = self.override_session

    def tearDown(self) -> None:
        settings.upload_dir = self.previous_upload_dir
        self.upload_directory.cleanup()
        self.session.close()
        app.dependency_overrides.clear()

    def override_session(self):
        yield self.session

    def test_settings_and_public_visibility(self) -> None:
        update_gallery_settings(
            self.session,
            GallerySettingsPayload(
                hall_name="测试展厅",
                entry_title="测试入口",
                show_entry=False,
                show_logo=False,
                logo_url=None,
                logo_display_url=None,
            ),
        )
        create_gallery_character(self.session, character_payload(1, visible=True))
        hidden = create_gallery_character(self.session, character_payload(2, visible=False))
        updated = update_gallery_character(
            self.session,
            self.session.get(GalleryCharacter, hidden.id),
            character_payload(3, visible=False),
        )

        public_gallery = get_gallery(self.session)
        manage_gallery = get_gallery(self.session, include_hidden=True)

        self.assertEqual(public_gallery.settings.hall_name, "测试展厅")
        self.assertFalse(public_gallery.settings.show_entry)
        self.assertEqual([item.name for item in public_gallery.characters], ["人物 1"])
        self.assertEqual(len(manage_gallery.characters), 2)
        self.assertEqual(updated.name, "人物 3")

    def test_validation_and_media_references(self) -> None:
        invalid_payload = character_payload(1).model_dump()
        invalid_payload["name"] = "   "
        with self.assertRaises(ValidationError):
            GalleryCharacterPayload(**invalid_payload)

        update_gallery_settings(
            self.session,
            GallerySettingsPayload(
                hall_name="测试展厅",
                entry_title="测试入口",
                show_logo=True,
                logo_url="/uploads/gallery/logo.png",
                logo_display_url="/uploads/gallery/derived/logo.webp",
            ),
        )
        payload = character_payload(1)
        payload.poster_url = "/uploads/gallery/poster.png"
        payload.poster_frame_url = "/uploads/gallery/derived/poster-frame.webp"
        payload.poster_display_url = "/uploads/gallery/derived/poster-display.webp"
        create_gallery_character(self.session, payload)

        candidates = _collect_reference_candidates(self.session)
        logo_references = _find_references("gallery/logo.png", candidates)
        poster_references = _find_references("gallery/poster.png", candidates)
        frame_references = _find_references("gallery/derived/poster-frame.webp", candidates)
        self.assertEqual([item.source for item in logo_references], ["3D 展厅"])
        self.assertEqual([item.source for item in poster_references], ["3D 展厅"])
        self.assertEqual([item.source for item in frame_references], ["3D 展厅"])

    def test_gallery_image_derivatives_and_legacy_regeneration(self) -> None:
        poster_bytes = image_bytes("PNG", (1200, 1800))
        variants = create_gallery_image_variants(poster_bytes, "poster")
        frame_path = upload_path_from_url(variants.frame_url)
        display_path = upload_path_from_url(variants.display_url)
        self.assertTrue(upload_path_from_url(variants.original_url).is_file())
        with Image.open(frame_path) as frame:
            self.assertEqual((frame.format, frame.size), ("WEBP", (512, 768)))
        with Image.open(display_path) as display:
            self.assertEqual((display.format, display.size), ("WEBP", (960, 1440)))

        logo = Image.new("RGBA", (900, 300), (20, 60, 80, 0))
        logo.putpixel((100, 100), (255, 210, 120, 255))
        logo_buffer = BytesIO()
        logo.save(logo_buffer, "PNG")
        logo_variants = create_gallery_image_variants(logo_buffer.getvalue(), "logo")
        with Image.open(upload_path_from_url(logo_variants.display_url)) as rendered_logo:
            self.assertEqual(rendered_logo.format, "WEBP")
            self.assertLessEqual(max(rendered_logo.size), 512)

        with self.assertRaises(GalleryImageError):
            create_gallery_image_variants(b"not an image", "poster")
        with self.assertRaises(GalleryImageError):
            create_gallery_image_variants(image_bytes("GIF", (30, 30)), "poster")

        legacy_path = settings.upload_path / "legacy-poster.png"
        legacy_path.parent.mkdir(parents=True, exist_ok=True)
        legacy_path.write_bytes(poster_bytes)
        update_gallery_settings(
            self.session,
            GallerySettingsPayload(
                hall_name="测试展厅",
                entry_title="测试入口",
                show_logo=True,
                logo_url="/uploads/legacy-poster.png",
                logo_display_url=None,
            ),
        )
        legacy_character = character_payload(1)
        legacy_character.poster_url = "/uploads/legacy-poster.png"
        create_gallery_character(self.session, legacy_character)
        self.assertEqual(regenerate_gallery_image_derivatives(self.session), 2)
        refreshed = get_gallery(self.session, include_hidden=True)
        self.assertTrue(refreshed.settings.logo_display_url)
        self.assertTrue(refreshed.characters[0].poster_frame_url)
        self.assertTrue(refreshed.characters[0].poster_display_url)

    def test_limit_reorder_and_delete_normalization(self) -> None:
        created = [create_gallery_character(self.session, character_payload(index)) for index in range(40)]
        with self.assertRaisesRegex(ValueError, "最多维护 40 位人物"):
            create_gallery_character(self.session, character_payload(41))

        reversed_ids = [item.id for item in reversed(created)]
        reordered = reorder_gallery_characters(self.session, reversed_ids)
        self.assertEqual([item.id for item in reordered], reversed_ids)
        with self.assertRaisesRegex(ValueError, "必须包含当前全部人物"):
            reorder_gallery_characters(self.session, reversed_ids[:-1])

        delete_gallery_character(self.session, self.session.get(GalleryCharacter, reversed_ids[0]))
        remaining = get_gallery(self.session, include_hidden=True).characters
        self.assertEqual([item.sort_order for item in remaining], list(range(39)))

    def test_api_auth_and_public_contract(self) -> None:
        client = TestClient(app)
        response = client.get("/api/v1/gallery")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["settings"]["hall_name"], "伟大航路人物档案馆")
        self.assertTrue(response.json()["data"]["settings"]["show_entry"])

        response = client.get("/api/v1/gallery/manage")
        self.assertEqual(response.status_code, 401)

        response = client.post(
            "/api/v1/gallery/characters",
            json=character_payload(1).model_dump(),
        )
        self.assertEqual(response.status_code, 401)

        app.dependency_overrides[require_admin_session] = lambda: "admin"
        response = client.put(
            "/api/v1/gallery/settings",
            json={
                "hall_name": "测试展厅",
                "entry_title": "测试入口",
                "show_entry": False,
                "show_logo": False,
                "logo_url": None,
                "logo_display_url": None,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["data"]["show_entry"])

        response = client.post(
            "/api/v1/gallery/characters",
            json=character_payload(1).model_dump(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["name"], "人物 1")
        upload_response = client.post(
            "/api/v1/gallery/media/poster",
            files={"file": ("poster.png", image_bytes("PNG", (600, 900)), "image/png")},
        )
        self.assertEqual(upload_response.status_code, 200)
        self.assertIn("frame_url", upload_response.json()["data"])


def image_bytes(image_format: str, size: tuple[int, int]) -> bytes:
    image = Image.new("RGB", size, (130, 180, 210))
    buffer = BytesIO()
    image.save(buffer, image_format)
    return buffer.getvalue()


def upload_path_from_url(url: str | None) -> Path:
    if not url:
        raise AssertionError("缺少图片 URL")
    return settings.upload_path / url.split("/uploads/", 1)[1]


if __name__ == "__main__":
    unittest.main()
