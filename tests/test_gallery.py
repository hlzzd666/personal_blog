import unittest
import importlib
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from PIL import Image
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy import text
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import get_db_session
from backend.app.core.config import settings
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.models.gallery import GalleryCharacter
from backend.app.schemas.gallery import GalleryCharacterPayload, GalleryChapterPayload, GallerySettingsPayload
from backend.app.services.auth import require_admin_session
from backend.app.services.gallery import (
    create_gallery_character,
    create_gallery_chapter,
    delete_gallery_chapter,
    delete_gallery_character,
    get_gallery,
    get_gallery_chapter,
    reorder_gallery_characters,
    reorder_gallery_chapters,
    update_gallery_chapter,
    update_gallery_character,
    update_gallery_settings,
)
from backend.app.services.media import _collect_reference_candidates, _find_references
from backend.app.services.gallery_media import GalleryImageError, create_gallery_image_variants


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
        # 本地配置可能已启用真实 OSS；常规测试必须使用临时目录，避免外部写入。
        storage = patch.object(settings, "media_storage_driver", "local")
        storage.start()
        self.addCleanup(storage.stop)
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

    def test_gallery_chapters_are_configurable_and_guarded(self) -> None:
        self.assertEqual(get_gallery(self.session).chapters, [])
        chapter = create_gallery_chapter(
            self.session,
            GalleryChapterPayload(
                title="测试航线", subtitle="副标题", heading="测试标题", description="说明", note="提示", label="TEST", story="故事"
            ),
        )
        other = create_gallery_chapter(self.session, GalleryChapterPayload(title="另一分类"))
        character_payload_with_chapter = character_payload(2)
        character_payload_with_chapter.chapter_id = chapter.id
        assigned = create_gallery_character(self.session, character_payload_with_chapter)
        self.assertEqual(assigned.chapter_id, chapter.id)
        updated = update_gallery_chapter(
            self.session,
            get_gallery_chapter(self.session, chapter.id),
            GalleryChapterPayload(
                title="已更新", subtitle="副标题", heading="测试标题", description="说明", note="提示", label="TEST", story="故事"
            ),
        )
        self.assertEqual(updated.title, "已更新")
        with self.assertRaisesRegex(ValueError, "仍有人物使用"):
            delete_gallery_chapter(self.session, get_gallery_chapter(self.session, chapter.id))
        reordered = reorder_gallery_chapters(self.session, [item.id for item in reversed(get_gallery(self.session, include_hidden=True).chapters)])
        self.assertEqual([item.id for item in reordered], [other.id, chapter.id])
        with self.assertRaisesRegex(ValueError, "全部分类"):
            reorder_gallery_chapters(self.session, [chapter.id, chapter.id])
        with self.assertRaisesRegex(ValueError, "名称已存在"):
            create_gallery_chapter(self.session, GalleryChapterPayload(title="已更新"))
        hidden_payload = GalleryChapterPayload(title="已更新", is_visible=False)
        update_gallery_chapter(self.session, get_gallery_chapter(self.session, chapter.id), hidden_payload)
        self.assertEqual([item.id for item in get_gallery(self.session).chapters], [other.id])
        self.assertEqual(len(get_gallery(self.session).characters), 1)
        record = self.session.get(GalleryCharacter, assigned.id)
        old_client_payload = character_payload(2)
        self.assertEqual(update_gallery_character(self.session, record, old_client_payload).chapter_id, chapter.id)
        invalid = character_payload(2)
        invalid.chapter_id = 9999
        with self.assertRaisesRegex(ValueError, "分类不存在"):
            update_gallery_character(self.session, record, invalid)
        old_client_payload.chapter_id = None
        self.assertIsNone(update_gallery_character(self.session, record, old_client_payload).chapter_id)
        delete_gallery_chapter(self.session, get_gallery_chapter(self.session, chapter.id))
        delete_gallery_chapter(self.session, get_gallery_chapter(self.session, other.id))
        self.assertEqual(get_gallery(self.session).chapters, [])
        self.assertEqual(reorder_gallery_chapters(self.session, []), [])

    def test_chapter_migration_preserves_characters_and_seeds_membership(self) -> None:
        migration = importlib.import_module("backend.migrations.versions.20260924_01_add_gallery_chapters")
        engine = create_engine("sqlite+pysqlite://")
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE gallery_characters (id INTEGER PRIMARY KEY, name VARCHAR(80), poster_url VARCHAR(2048))"))
            names = ["蒙奇·D·路飞", "索隆", "娜美", "乌索普", "山治", "乔巴", "妮可·罗宾", "弗兰奇", "布鲁克", "甚平", "未分类人物"]
            connection.execute(text("INSERT INTO gallery_characters (id, name, poster_url) VALUES (:id, :name, :url)"), [
                {"id": index + 1, "name": name, "url": f"/poster/{index}.webp"} for index, name in enumerate(names)
            ])
            before = connection.execute(text("SELECT id,name,poster_url FROM gallery_characters ORDER BY id")).all()
            with patch.object(migration, "op", Operations(MigrationContext.configure(connection))):
                migration.upgrade()
                self.assertEqual(connection.execute(text("SELECT chapter_id FROM gallery_characters ORDER BY id")).scalars().all(), [1]*5 + [2]*4 + [3, None])
                self.assertEqual(connection.execute(text("SELECT title FROM gallery_chapters ORDER BY sort_order")).scalars().all(), ["东海群像", "伟大航路", "新世界"])
                self.assertEqual(connection.execute(text("SELECT id,name,poster_url FROM gallery_characters ORDER BY id")).all(), before)
                migration.downgrade()
                self.assertEqual(connection.execute(text("SELECT id,name,poster_url FROM gallery_characters ORDER BY id")).all(), before)
        engine.dispose()

    def test_chapter_api_auth_validation_and_persistence(self) -> None:
        client = TestClient(app)
        for method, path, payload in [
            ("post", "/gallery/chapters", {"title": "测试"}),
            ("put", "/gallery/chapters/1", {"title": "测试"}),
            ("put", "/gallery/chapters/order", {"chapter_ids": []}),
            ("delete", "/gallery/chapters/1", None),
        ]:
            response = client.request(method, "/api/v1" + path, json=payload)
            self.assertEqual(response.status_code, 401)
        app.dependency_overrides[require_admin_session] = lambda: "admin"
        self.assertEqual(client.post("/api/v1/gallery/chapters", json={"title": " "}).status_code, 422)
        self.assertEqual(client.post("/api/v1/gallery/chapters", json={"title": "测试", "artwork_index": 9}).status_code, 422)
        response = client.post("/api/v1/gallery/chapters", json={"title": "可配置分类"})
        self.assertEqual(response.status_code, 200)
        chapter_id = response.json()["data"]["id"]
        self.assertEqual(client.post("/api/v1/gallery/chapters", json={"title": "可配置分类"}).status_code, 409)
        payload = character_payload(1).model_dump() | {"chapter_id": chapter_id}
        response = client.post("/api/v1/gallery/characters", json=payload)
        self.assertEqual(response.status_code, 200)
        character_id = response.json()["data"]["id"]
        self.assertEqual(client.put(f"/api/v1/gallery/characters/{character_id}", json=payload | {"chapter_id": 9999}).status_code, 409)
        self.assertEqual(client.delete(f"/api/v1/gallery/chapters/{chapter_id}").status_code, 409)
        self.assertEqual(client.put("/api/v1/gallery/chapters/order", json={"chapter_ids": [chapter_id, chapter_id]}).status_code, 422)
        self.assertEqual(client.put("/api/v1/gallery/chapters/order", json={"chapter_ids": [chapter_id]}).status_code, 200)
        client.put(f"/api/v1/gallery/chapters/{chapter_id}", json={"title": "新名称", "is_visible": False})
        self.assertEqual(client.get("/api/v1/gallery").json()["data"]["chapters"], [])
        self.assertEqual(client.get("/api/v1/gallery/manage").json()["data"]["chapters"][0]["title"], "新名称")
        client.put(f"/api/v1/gallery/characters/{character_id}", json=payload | {"chapter_id": None})
        self.assertEqual(client.delete(f"/api/v1/gallery/chapters/{chapter_id}").status_code, 200)
        self.assertEqual(client.get("/api/v1/gallery/manage").json()["data"]["chapters"], [])

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
            ),
        )
        payload = character_payload(1)
        payload.poster_url = "/uploads/gallery/poster.png"
        create_gallery_character(self.session, payload)

        candidates = _collect_reference_candidates(self.session)
        logo_references = _find_references("gallery/logo.png", candidates)
        poster_references = _find_references("gallery/poster.png", candidates)
        self.assertEqual([item.source for item in logo_references], ["3D 展厅"])
        self.assertEqual([item.source for item in poster_references], ["3D 展厅"])

    def test_gallery_image_upload_uses_one_frontend_processed_file(self) -> None:
        poster_bytes = image_bytes("PNG", (1200, 1800))
        variants = create_gallery_image_variants(poster_bytes, "poster")
        poster_path = upload_path_from_url(variants.url)
        self.assertTrue(variants.url)
        self.assertTrue(poster_path.is_file())
        self.assertEqual(poster_path.suffix, ".png")
        self.assertEqual(poster_path.read_bytes(), poster_bytes)
        with Image.open(poster_path) as poster:
            self.assertEqual((poster.format, poster.size), ("PNG", (1200, 1800)))

        logo = Image.new("RGBA", (900, 300), (20, 60, 80, 0))
        logo.putpixel((100, 100), (255, 210, 120, 255))
        logo_buffer = BytesIO()
        logo.save(logo_buffer, "PNG")
        logo_variants = create_gallery_image_variants(logo_buffer.getvalue(), "logo")
        with Image.open(upload_path_from_url(logo_variants.url)) as rendered_logo:
            self.assertEqual(rendered_logo.format, "PNG")
            self.assertEqual(rendered_logo.size, (900, 300))

        with self.assertRaises(GalleryImageError):
            create_gallery_image_variants(b"not an image", "poster")
        with self.assertRaises(GalleryImageError):
            create_gallery_image_variants(image_bytes("GIF", (30, 30)), "poster")

    def test_oss_upload_and_failure_do_not_write_local_files(self) -> None:
        content = image_bytes("WEBP", (30, 45))
        bucket = Mock()
        bucket.put_object.return_value.status = 200
        with patch.object(settings, "media_storage_driver", "oss"), patch.object(
            settings, "oss_public_base_url", "https://images.example.com"
        ), patch.object(settings, "oss_object_prefix", "personal-blog"), patch(
            "backend.app.services.object_storage._bucket", return_value=bucket
        ):
            url = create_gallery_image_variants(content, "poster").url
            self.assertTrue(url.startswith("https://images.example.com/personal-blog/gallery/poster/"))
            args, kwargs = bucket.put_object.call_args
            self.assertEqual(args[1], content)
            self.assertEqual(kwargs["headers"]["Content-Type"], "image/webp")
            with self.assertRaises(GalleryImageError):
                create_gallery_image_variants(b"invalid", "poster")
            self.assertEqual(bucket.put_object.call_count, 1)
            bucket.put_object.side_effect = RuntimeError("provider error")
            with self.assertRaises(GalleryImageError):
                create_gallery_image_variants(content, "poster")
        self.assertEqual(list(Path(self.upload_directory.name).rglob("*")), [])

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
        self.assertIn("url", upload_response.json()["data"])


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
