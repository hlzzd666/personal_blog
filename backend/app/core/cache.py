import hashlib
import json
import logging
from functools import lru_cache

from redis import Redis
from redis.exceptions import RedisError

from .config import settings

logger = logging.getLogger(__name__)

ARTICLE_LIST_VERSION_KEY = "personal-blog:articles:list:version"


@lru_cache
def get_redis_client() -> Redis:
    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=0.2,
        socket_timeout=0.2,
    )


def build_article_list_cache_key(
    *,
    public_only: bool,
    page: int,
    page_size: int,
    category: str | None,
    tag: str | None,
    search: str | None,
) -> str | None:
    try:
        version = get_redis_client().get(ARTICLE_LIST_VERSION_KEY) or "0"
    except RedisError:
        logger.warning("Redis is unavailable while reading the article list cache version")
        return None

    params = {
        "public_only": public_only,
        "page": page,
        "page_size": page_size,
        "category": category,
        "tag": tag,
        "search": search,
    }
    digest = hashlib.sha256(
        json.dumps(params, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return f"personal-blog:articles:list:{version}:{digest}"


def get_cache_value(key: str | None) -> str | None:
    if key is None:
        return None
    try:
        return get_redis_client().get(key)
    except RedisError:
        logger.warning("Redis is unavailable while reading the article list cache")
        return None


def set_cache_value(key: str | None, value: str) -> None:
    if key is None:
        return
    try:
        get_redis_client().setex(key, settings.article_list_cache_ttl, value)
    except RedisError:
        logger.warning("Redis is unavailable while writing the article list cache")


def invalidate_article_list_cache() -> None:
    try:
        get_redis_client().incr(ARTICLE_LIST_VERSION_KEY)
    except RedisError:
        logger.warning("Redis is unavailable while invalidating the article list cache")
