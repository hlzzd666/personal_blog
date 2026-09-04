import json
from datetime import date
from pathlib import Path

from backend.app.schemas.site_settings import SiteSettings, SiteSettingsUpdate

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SETTINGS_PATH = DATA_DIR / "site_settings.json"

DEFAULT_SITE_SETTINGS = SiteSettings(
    site_subtitle="自由、梦想、伙伴，这里记录我向前航行的每一步。",
    hero_image_url="https://images.hdqwalls.com/download/one-piece-anime-artwork-i6-2560x1440.jpg",
    nav_brand="某某某的个人空间",
    icp_filing_number=None,
    police_filing_number=None,
    site_launched_on=date(2026, 1, 1),
    owner_avatar_url="/owner-avatar.jpg",
    owner_location_name="未设置站长地址",
    owner_latitude=None,
    owner_longitude=None,
    visual_assets=[
        {
            "key": "article_list_background",
            "name": "文章列表页背景",
            "usage": "background",
            "image_url": "",
            "enabled": False,
            "opacity": 0.28,
            "note": "用于文章列表页的氛围底图，建议上传抽象海图、纹理或低对比度照片。",
        },
    ],
    quotes=[
        {
            "author": "路飞",
            "text": "我是要成为海贼王的男人。",
        },
        {
            "author": "希鲁鲁克",
            "text": "人被世人遗忘的时候，才是真正的死亡。",
        },
        {
            "author": "罗宾",
            "text": "我想活下去。",
        },
        {
            "author": "艾斯",
            "text": "谢谢你们爱我。",
        },
    ],
)


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_site_settings() -> SiteSettings:
    _ensure_data_dir()
    if not SETTINGS_PATH.exists():
        SETTINGS_PATH.write_text(
            DEFAULT_SITE_SETTINGS.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return DEFAULT_SITE_SETTINGS

    with SETTINGS_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return SiteSettings.model_validate(payload)


def update_site_settings(payload: SiteSettingsUpdate) -> SiteSettings:
    _ensure_data_dir()
    settings = SiteSettings.model_validate(payload.model_dump())
    SETTINGS_PATH.write_text(settings.model_dump_json(indent=2), encoding="utf-8")
    return settings
