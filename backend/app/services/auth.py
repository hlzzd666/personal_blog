import hashlib
import hmac
import json
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, Request, Response, status
from redis.exceptions import RedisError

from backend.app.core.cache import get_redis_client
from backend.app.core.config import settings
from backend.app.core.passwords import verify_password
from backend.app.schemas.auth import AdminSessionResponse

logger = logging.getLogger(__name__)

ADMIN_SESSION_KEY_PREFIX = "personal-blog:admin:sessions:"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _hash_session_token(session_token: str) -> str:
    return hashlib.sha256(session_token.encode("utf-8")).hexdigest()


def _session_key(session_token: str) -> str:
    return f"{ADMIN_SESSION_KEY_PREFIX}{_hash_session_token(session_token)}"


def _set_auth_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    cookie_options = {
        "max_age": settings.admin_session_ttl_seconds,
        "secure": settings.cookie_secure,
        "samesite": "lax",
        "path": "/",
    }
    response.set_cookie(
        key=settings.admin_session_cookie_name,
        value=session_token,
        httponly=True,
        **cookie_options,
    )
    response.set_cookie(
        key=settings.admin_csrf_cookie_name,
        value=csrf_token,
        httponly=False,
        **cookie_options,
    )


def clear_auth_cookies(response: Response) -> None:
    cookie_options = {
        "secure": settings.cookie_secure,
        "samesite": "lax",
        "path": "/",
    }
    response.delete_cookie(settings.admin_session_cookie_name, **cookie_options)
    response.delete_cookie(settings.admin_csrf_cookie_name, **cookie_options)


def authenticate_admin(username: str, password: str) -> None:
    if not settings.admin_password_hash:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="管理员密码未配置",
        )
    if username != settings.admin_username or not verify_password(password, settings.admin_password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")


def create_admin_session(response: Response, username: str) -> AdminSessionResponse:
    session_token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    logged_in_at = _utc_now()
    expires_at = logged_in_at + timedelta(seconds=settings.admin_session_ttl_seconds)
    session_data = {
        "username": username,
        "created_at": logged_in_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "csrf_token": csrf_token,
    }

    try:
        get_redis_client().setex(
            _session_key(session_token),
            settings.admin_session_ttl_seconds,
            json.dumps(session_data, ensure_ascii=True, separators=(",", ":")),
        )
    except RedisError as error:
        logger.warning("Redis is unavailable while creating an admin session")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="认证服务暂时不可用",
        ) from error

    _set_auth_cookies(response, session_token, csrf_token)
    return AdminSessionResponse(
        username=username,
        logged_in_at=session_data["created_at"],
        expires_at=session_data["expires_at"],
    )


def delete_admin_session(request: Request, response: Response) -> None:
    session_token = request.cookies.get(settings.admin_session_cookie_name)
    if session_token:
        try:
            get_redis_client().delete(_session_key(session_token))
        except RedisError:
            logger.warning("Redis is unavailable while deleting an admin session")
    clear_auth_cookies(response)


def _load_session(session_token: str) -> dict[str, Any]:
    try:
        raw_session = get_redis_client().get(_session_key(session_token))
    except RedisError as error:
        logger.warning("Redis is unavailable while reading an admin session")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="认证服务暂时不可用",
        ) from error

    if raw_session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录")

    try:
        session_data = json.loads(raw_session)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录") from error

    if not isinstance(session_data, dict):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录")
    return session_data


def _require_csrf(request: Request, session_data: dict[str, Any]) -> None:
    header_token = request.headers.get(CSRF_HEADER_NAME)
    cookie_token = request.cookies.get(settings.admin_csrf_cookie_name)
    session_token = session_data.get("csrf_token")
    if not (
        isinstance(session_token, str)
        and isinstance(header_token, str)
        and isinstance(cookie_token, str)
        and hmac.compare_digest(header_token, cookie_token)
        and hmac.compare_digest(header_token, session_token)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF 校验失败")


def require_admin_session(request: Request) -> AdminSessionResponse:
    session_token = request.cookies.get(settings.admin_session_cookie_name)
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")

    session_data = _load_session(session_token)
    if request.method.upper() in CSRF_METHODS:
        _require_csrf(request, session_data)

    username = session_data.get("username")
    logged_in_at = session_data.get("created_at")
    expires_at = session_data.get("expires_at")
    if not all(isinstance(value, str) for value in (username, logged_in_at, expires_at)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录")

    return AdminSessionResponse(
        username=username,
        logged_in_at=logged_in_at,
        expires_at=expires_at,
    )
