from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote, urlparse

from backend.app.core.config import settings


class ObjectStorageError(RuntimeError):
    """对象存储配置或上传失败。"""


def storage_enabled() -> bool:
    return settings.media_storage_driver.strip().lower() == "oss"


@lru_cache
def _bucket():
    if not storage_enabled():
        raise ObjectStorageError("对象存储未启用")
    values = {
        "endpoint": settings.oss_endpoint.strip(),
        "bucket": settings.oss_bucket.strip(),
        "access_key_id": settings.oss_access_key_id.strip(),
        "access_key_secret": settings.oss_access_key_secret.strip(),
    }
    if not all(values.values()):
        raise ObjectStorageError(
            "OSS 模式需要配置 OSS_ENDPOINT、OSS_BUCKET、OSS_ACCESS_KEY_ID 和 OSS_ACCESS_KEY_SECRET"
        )
    try:
        import oss2
    except ImportError as error:  # pragma: no cover - 依赖缺失只在 OSS 模式触发
        raise ObjectStorageError("OSS 模式需要安装 oss2 依赖") from error
    return oss2.Bucket(
        oss2.Auth(values["access_key_id"], values["access_key_secret"]),
        values["endpoint"],
        values["bucket"],
    )


def put_object(key: str, content: bytes, content_type: str) -> str:
    try:
        result = _bucket().put_object(
            key,
            content,
            headers={
                "Content-Type": content_type,
                "Cache-Control": "public, max-age=31536000, immutable",
            },
        )
    except ObjectStorageError:
        raise
    except Exception as error:
        raise ObjectStorageError("OSS 对象上传失败") from error
    if result.status >= 300:
        raise ObjectStorageError(f"OSS 对象上传失败：HTTP {result.status}")
    return public_url(key)


def public_url(key: str) -> str:
    base = settings.oss_public_base_url.strip().rstrip("/")
    if not base:
        endpoint = settings.oss_endpoint.strip().rstrip("/")
        parsed = urlparse(endpoint if "://" in endpoint else f"https://{endpoint}")
        base = f"{parsed.scheme}://{settings.oss_bucket.strip()}.{parsed.netloc}"
    return f"{base}/{quote(key, safe='/')}"
