import hashlib
import hmac
from datetime import datetime, timedelta

from redis.exceptions import RedisError
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.app.core.cache import get_redis_client
from backend.app.core.config import settings
from backend.app.models.guestbook import GuestbookMessage
from backend.app.schemas.guestbook import (
    GuestbookCreate,
    GuestbookManageItem,
    GuestbookManageList,
    GuestbookPublicItem,
    GuestbookPublicList,
)


def visitor_hash(visitor_id: str) -> str:
    return hmac.new(
        settings.article_visitor_identity_secret.encode(), visitor_id.encode(), hashlib.sha256
    ).hexdigest()


def content_hash(nickname: str, content: str) -> str:
    value = f"{nickname.strip()}\n{content.strip()}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def allow_submission(identity: str) -> bool:
    key = f"personal-blog:guestbook:rate:{identity}"
    try:
        client = get_redis_client()
        count = client.incr(key)
        if count == 1:
            client.expire(key, 3600)
        return count <= 3
    except RedisError:
        # ponytail: 本地/测试环境 Redis 不可用时保留可用性；生产应将 Redis 配为强依赖。
        return True


def create_message(session: Session, payload: GuestbookCreate, identity: str) -> GuestbookMessage:
    if payload.honeypot.strip():
        raise ValueError("留言提交失败")
    if not allow_submission(identity):
        raise ValueError("提交过于频繁，请稍后再试")
    digest = content_hash(payload.nickname, payload.content)
    recent = session.scalar(
        select(GuestbookMessage.id).where(
            GuestbookMessage.content_hash == digest,
            GuestbookMessage.created_at >= datetime.now() - timedelta(days=1),
            GuestbookMessage.status != "deleted",
        )
    )
    if recent is not None:
        raise ValueError("相同留言已提交，请勿重复发送")
    message = GuestbookMessage(
        nickname=payload.nickname,
        content=payload.content,
        visitor_hash=visitor_hash(identity),
        content_hash=digest,
        risk_score=0,
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def list_public_messages(session: Session, page: int, page_size: int) -> GuestbookPublicList:
    where = (GuestbookMessage.status == "approved", GuestbookMessage.deleted_at.is_(None))
    total = session.scalar(select(func.count(GuestbookMessage.id)).where(*where)) or 0
    items = list(
        session.scalars(
            select(GuestbookMessage)
            .where(*where)
            .order_by(GuestbookMessage.created_at.desc(), GuestbookMessage.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return GuestbookPublicList(
        items=[GuestbookPublicItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def list_manage_messages(
    session: Session, page: int, page_size: int, status: str | None = None, keyword: str | None = None
) -> GuestbookManageList:
    filters = []
    if status:
        filters.append(GuestbookMessage.status == status)
    if keyword:
        term = f"%{keyword.strip()}%"
        filters.append(or_(GuestbookMessage.nickname.like(term), GuestbookMessage.content.like(term)))
    total = session.scalar(select(func.count(GuestbookMessage.id)).where(*filters)) or 0
    pending_count = session.scalar(
        select(func.count(GuestbookMessage.id)).where(GuestbookMessage.status == "pending")
    ) or 0
    items = list(
        session.scalars(
            select(GuestbookMessage)
            .where(*filters)
            .order_by(GuestbookMessage.created_at.desc(), GuestbookMessage.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return GuestbookManageList(
        items=[GuestbookManageItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pending_count=pending_count,
    )


def update_status(session: Session, message: GuestbookMessage, status: str, reason: str = "") -> GuestbookMessage:
    transitions = {
        "pending": {"approved", "rejected", "spam", "deleted"},
        "approved": {"rejected", "spam", "deleted"},
        "rejected": {"approved", "spam", "deleted"},
        "spam": {"approved", "deleted"},
        "deleted": set(),
    }
    if status not in transitions or status not in transitions.get(message.status, set()):
        raise ValueError("留言状态无效")
    message.status = status
    message.admin_note = reason.strip()
    message.reviewed_at = datetime.now()
    message.deleted_at = datetime.now() if status == "deleted" else None
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def update_reply(session: Session, message: GuestbookMessage, reply: str) -> GuestbookMessage:
    message.admin_reply = reply.strip()
    session.add(message)
    session.commit()
    session.refresh(message)
    return message
