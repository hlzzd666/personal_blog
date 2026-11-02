from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote, urlparse

from backend.app.core.config import settings


class ObjectStorageError(RuntimeError):
    """对象存储配置或上传失败。"""


def managed_prefix() -> str:
    prefix = settings.oss_object_prefix.strip("/")
    if not prefix:
        raise ObjectStorageError("管理 OSS 资源必须设置专属目录 OSS_OBJECT_PREFIX")
    return prefix + "/"


def list_objects() -> list:
    """只列举本站目录，遍历全部分页，失败时不返回部分清单。"""
    prefix = managed_prefix()
    objects = []
    marker = ""
    try:
        while True:
            page = _bucket().list_objects(prefix=prefix, marker=marker, max_keys=1000)
            objects.extend(item for item in page.object_list if not item.key.endswith("/"))
            if not page.is_truncated:
                return objects
            if not page.next_marker or page.next_marker == marker:
                raise ObjectStorageError("OSS 分页异常，请刷新重试")
            marker = page.next_marker
    except ObjectStorageError:
        raise
    except Exception as error:
        raise ObjectStorageError("OSS 列表读取失败，请检查网络及 oss:ListObjects 权限") from error


def delete_object(key: str) -> None:
    if not key.startswith(managed_prefix()) or key.endswith("/"):
        raise ObjectStorageError("只能删除本站目录内的文件")
    try:
        _bucket().delete_object(key)
    except Exception as error:
        raise ObjectStorageError("OSS 删除失败，请检查 oss:DeleteObject 权限") from error


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
