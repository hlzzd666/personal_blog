import ipaddress
import json
import logging
import re
import socket
import time as time_module
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlsplit
from uuid import uuid4

import httpx
from cryptography.fernet import Fernet, InvalidToken
from pydantic import ValidationError
from redis.exceptions import RedisError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.cache import get_redis_client, invalidate_article_list_cache
from backend.app.core.config import settings
from backend.app.models.article import Article
from backend.app.models.content import Series
from backend.app.models.daily_learning import DailyLearningRun, DailyLearningSettings
from backend.app.schemas.daily_learning import (
    DailyLearningRunListResponse,
    DailyLearningRunResponse,
    DailyLearningSettingsResponse,
    DailyLearningSettingsUpdate,
    DailyLearningTestResponse,
    GeneratedQuestionSet,
)

logger = logging.getLogger(__name__)

BEIJING_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
DAILY_CATEGORY = "每日问答"
DAILY_SERIES_SLUG = "daily-learning"
DAILY_SERIES_TITLE = "今日份学习"
DEFAULT_DAILY_TAGS = ["前端面试", "每日问答"]
DEFAULT_GENERATION_INSTRUCTIONS = (
    "题目覆盖 JavaScript、TypeScript、Vue、React、浏览器、CSS、网络、性能和工程化，"
    "兼顾基础、中级和高级难度。答案准确、清晰，必要时给出简短代码示例。"
)
MAX_ATTEMPTS = 3
RETRY_DELAYS = (timedelta(minutes=10), timedelta(minutes=30))
RUN_LOCK_KEY = "personal-blog:daily-learning:runner-lock"
QUESTION_HEADING_PATTERN = re.compile(r"^##\s+\d+[.、]\s*(.+?)\s*$", re.MULTILINE)


class DailyLearningError(RuntimeError):
    pass


class DailyLearningConfigurationError(DailyLearningError):
    pass


class DailyLearningAIError(DailyLearningError):
    pass


@dataclass(frozen=True)
class AIConfiguration:
    base_url: str
    model: str
    api_key: str
    generation_instructions: str


QuestionGenerator = Callable[[AIConfiguration, list[str]], GeneratedQuestionSet]


def beijing_now() -> datetime:
    return datetime.now(BEIJING_TZ)


def _naive_beijing(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(BEIJING_TZ).replace(tzinfo=None)


def _fernet() -> Fernet:
    key = settings.daily_learning_encryption_key.strip()
    if not key:
        raise DailyLearningConfigurationError("服务端尚未配置每日问答加密主密钥")
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as error:
        raise DailyLearningConfigurationError("每日问答加密主密钥格式无效") from error


def encrypt_api_key(api_key: str) -> str:
    value = api_key.strip()
    if not value:
        raise DailyLearningConfigurationError("AI API Key 不能为空")
    return _fernet().encrypt(value.encode()).decode("ascii")


def decrypt_api_key(encrypted_api_key: str | None) -> str:
    if not encrypted_api_key:
        raise DailyLearningConfigurationError("尚未配置 AI API Key")
    try:
        return _fernet().decrypt(encrypted_api_key.encode("ascii")).decode()
    except (InvalidToken, UnicodeError) as error:
        raise DailyLearningConfigurationError("AI API Key 无法解密，请重新配置") from error


def validate_ai_base_url(value: str) -> str:
    normalized = value.strip().rstrip("/")
    parsed = urlsplit(normalized)
    if parsed.scheme != "https" or not parsed.hostname:
        raise DailyLearningConfigurationError("AI 接口地址必须是 HTTPS 公网地址")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise DailyLearningConfigurationError("AI 接口地址不能包含账号、查询参数或片段")
    try:
        port = parsed.port or 443
    except ValueError as error:
        raise DailyLearningConfigurationError("AI 接口端口无效") from error
    try:
        addresses = {
            info[4][0]
            for info in socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as error:
        raise DailyLearningConfigurationError("AI 接口域名无法解析") from error
    if not addresses:
        raise DailyLearningConfigurationError("AI 接口域名没有可用地址")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise DailyLearningConfigurationError("AI 接口地址不能指向内网或本机")
    return normalized


def get_or_create_settings(session: Session) -> DailyLearningSettings:
    record = session.get(DailyLearningSettings, 1)
    if record is not None:
        return record
    record = DailyLearningSettings(
        id=1,
        enabled=False,
        generation_instructions=DEFAULT_GENERATION_INSTRUCTIONS,
        tags=list(DEFAULT_DAILY_TAGS),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def serialize_settings(record: DailyLearningSettings) -> DailyLearningSettingsResponse:
    return DailyLearningSettingsResponse(
        enabled=record.enabled,
        publish_time=record.publish_time,
        ai_base_url=record.ai_base_url,
        ai_model=record.ai_model,
        api_key_configured=bool(record.encrypted_api_key),
        generation_instructions=record.generation_instructions or DEFAULT_GENERATION_INSTRUCTIONS,
        tags=list(record.tags or DEFAULT_DAILY_TAGS),
        updated_at=record.updated_at,
    )


def update_daily_learning_settings(
    session: Session, payload: DailyLearningSettingsUpdate
) -> DailyLearningSettingsResponse:
    record = get_or_create_settings(session)
    ai_base_url = validate_ai_base_url(payload.ai_base_url) if payload.ai_base_url else ""
    api_key = (payload.api_key or "").strip()
    encrypted_api_key = encrypt_api_key(api_key) if api_key else record.encrypted_api_key
    if payload.enabled and not (ai_base_url and payload.ai_model and encrypted_api_key):
        raise DailyLearningConfigurationError("启用前请完整配置 AI 地址、模型和 API Key")

    record.enabled = payload.enabled
    record.publish_time = payload.publish_time
    record.ai_base_url = ai_base_url
    record.ai_model = payload.ai_model
    record.encrypted_api_key = encrypted_api_key
    record.generation_instructions = payload.generation_instructions
    record.tags = payload.tags
    session.add(record)
    session.commit()
    session.refresh(record)
    return serialize_settings(record)


def _ai_configuration(record: DailyLearningSettings) -> AIConfiguration:
    if not record.ai_base_url or not record.ai_model:
        raise DailyLearningConfigurationError("请先配置 AI 接口地址和模型")
    return AIConfiguration(
        base_url=validate_ai_base_url(record.ai_base_url),
        model=record.ai_model,
        api_key=decrypt_api_key(record.encrypted_api_key),
        generation_instructions=record.generation_instructions or DEFAULT_GENERATION_INSTRUCTIONS,
    )


def _normalize_question(value: str) -> str:
    return re.sub(r"[\W_]+", "", value, flags=re.UNICODE).casefold()


def _parse_generated_questions(content: str, previous_questions: list[str]) -> GeneratedQuestionSet:
    value = content.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*", "", value, count=1, flags=re.IGNORECASE)
        value = re.sub(r"\s*```$", "", value, count=1)
    if not value.startswith("{"):
        start = value.find("{")
        end = value.rfind("}")
        if start >= 0 and end > start:
            value = value[start : end + 1]
    try:
        generated = GeneratedQuestionSet.model_validate(json.loads(value))
    except (json.JSONDecodeError, ValidationError, TypeError) as error:
        raise DailyLearningAIError("AI 返回内容不是有效的 10 道问答 JSON") from error

    normalized = [_normalize_question(item.question) for item in generated.questions]
    if len(set(normalized)) != len(normalized):
        raise DailyLearningAIError("AI 返回了重复题目")
    previous = {_normalize_question(item) for item in previous_questions}
    if previous.intersection(normalized):
        raise DailyLearningAIError("AI 返回了最近已经发布过的题目")
    return generated


def generate_daily_questions(
    configuration: AIConfiguration,
    previous_questions: list[str],
) -> GeneratedQuestionSet:
    previous_text = "\n".join(f"- {item}" for item in previous_questions[-300:]) or "无"
    prompt = (
        "请生成恰好 10 道中文前端面试题和参考答案。\n"
        f"额外要求：{configuration.generation_instructions}\n"
        "难度应混合，题目之间不能重复，也不要复用最近题目。\n"
        f"最近题目：\n{previous_text}\n"
        "只返回 JSON，不要使用 Markdown 代码围栏。格式必须是："
        '{"questions":[{"question":"题目","answer":"参考答案"}]}。'
    )
    endpoint = f"{configuration.base_url}/chat/completions"
    try:
        with httpx.Client(timeout=120, follow_redirects=False, trust_env=False) as client:
            response = client.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {configuration.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": configuration.model,
                    "temperature": 0.7,
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是严谨的资深前端面试官，只输出符合要求的 JSON。",
                        },
                        {"role": "user", "content": prompt},
                    ],
                },
            )
    except httpx.HTTPError as error:
        raise DailyLearningAIError("AI 服务连接失败") from error
    if response.is_redirect:
        raise DailyLearningAIError("AI 服务返回了不允许的重定向")
    if response.status_code >= 400:
        raise DailyLearningAIError(f"AI 服务返回 HTTP {response.status_code}")
    try:
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as error:
        raise DailyLearningAIError("AI 服务响应格式不兼容") from error
    if not isinstance(content, str):
        raise DailyLearningAIError("AI 服务没有返回文本内容")
    return _parse_generated_questions(content, previous_questions)


def _recent_question_titles(session: Session) -> list[str]:
    articles = list(
        session.scalars(
            select(Article)
            .where(Article.category == DAILY_CATEGORY)
            .order_by(Article.published_at.desc(), Article.id.desc())
            .limit(30)
        )
    )
    return [
        title.strip()
        for article in articles
        for title in QUESTION_HEADING_PATTERN.findall(article.content_markdown)
    ]


def test_daily_learning_ai(session: Session) -> DailyLearningTestResponse:
    record = get_or_create_settings(session)
    configuration = _ai_configuration(record)
    started = time_module.monotonic()
    result = generate_daily_questions(configuration, _recent_question_titles(session))
    return DailyLearningTestResponse(
        ok=True,
        model=configuration.model,
        question_count=len(result.questions),
        first_question=result.questions[0].question,
        latency_ms=round((time_module.monotonic() - started) * 1000),
    )


def _article_slug(run_date: date) -> str:
    return f"{run_date.isoformat()}-学习记录"


def _serialize_run(session: Session, run: DailyLearningRun) -> DailyLearningRunResponse:
    article = session.get(Article, run.article_id) if run.article_id else None
    return DailyLearningRunResponse(
        **{column.name: getattr(run, column.name) for column in run.__table__.columns},
        article_slug=article.slug if article else None,
        article_title=article.title if article else None,
    )


def list_daily_learning_runs(session: Session, limit: int) -> DailyLearningRunListResponse:
    runs = list(
        session.scalars(
            select(DailyLearningRun).order_by(DailyLearningRun.run_date.desc()).limit(limit)
        )
    )
    total = session.scalar(select(func.count(DailyLearningRun.id))) or 0
    return DailyLearningRunListResponse(
        items=[_serialize_run(session, run) for run in runs], total=total
    )


def queue_daily_learning_run(session: Session, now: datetime | None = None) -> DailyLearningRunResponse:
    current = (now or beijing_now()).astimezone(BEIJING_TZ)
    current_naive = _naive_beijing(current)
    record = get_or_create_settings(session)
    _ai_configuration(record)
    run_date = current.date()
    article = session.scalar(select(Article).where(Article.slug == _article_slug(run_date)))
    run = session.scalar(select(DailyLearningRun).where(DailyLearningRun.run_date == run_date))
    if run is None:
        run = DailyLearningRun(
            run_date=run_date,
            scheduled_for=current_naive,
            status="succeeded" if article else "pending",
            article_id=article.id if article else None,
            completed_at=current_naive if article else None,
            next_retry_at=current_naive if not article else None,
        )
    elif article:
        run.status = "succeeded"
        run.article_id = article.id
        run.completed_at = current_naive
        run.last_error = None
        run.next_retry_at = None
    else:
        run.status = "pending"
        run.attempt_count = 0
        run.scheduled_for = current_naive
        run.started_at = None
        run.completed_at = None
        run.last_error = None
        run.next_retry_at = current_naive
    session.add(run)
    session.commit()
    session.refresh(run)
    return _serialize_run(session, run)


def _build_markdown(result: GeneratedQuestionSet) -> str:
    sections = []
    for index, item in enumerate(result.questions, 1):
        sections.append(f"## {index}. {item.question}\n\n**参考答案：**\n\n{item.answer}")
    return "\n\n---\n\n".join(sections)


def _mark_failed(session: Session, run_id: int, error: Exception, now: datetime) -> None:
    run = session.get(DailyLearningRun, run_id)
    if run is None:
        return
    run.status = "failed"
    run.last_error = str(error)[:2000] or error.__class__.__name__
    run.completed_at = now
    run.next_retry_at = (
        now + RETRY_DELAYS[run.attempt_count - 1]
        if run.attempt_count < MAX_ATTEMPTS
        else None
    )
    session.add(run)
    session.commit()
    logger.error("Daily learning generation failed on attempt %s: %s", run.attempt_count, error)


def _acquire_runner_lock() -> str | None:
    token = uuid4().hex
    try:
        acquired = get_redis_client().set(RUN_LOCK_KEY, token, nx=True, ex=300)
    except RedisError:
        logger.warning("Redis unavailable; continuing with database idempotency only")
        return token
    return token if acquired else None


def _release_runner_lock(token: str) -> None:
    try:
        get_redis_client().eval(
            "if redis.call('get', KEYS[1]) == ARGV[1] then "
            "return redis.call('del', KEYS[1]) else return 0 end",
            1,
            RUN_LOCK_KEY,
            token,
        )
    except RedisError:
        logger.warning("Redis unavailable while releasing the daily learning lock")


def process_daily_learning_tick(
    session: Session,
    *,
    now: datetime | None = None,
    question_generator: QuestionGenerator = generate_daily_questions,
) -> str:
    lock_token = _acquire_runner_lock()
    if lock_token is None:
        return "locked"
    try:
        current = (now or beijing_now()).astimezone(BEIJING_TZ)
        current_naive = _naive_beijing(current)
        record = get_or_create_settings(session)
        run = session.scalar(
            select(DailyLearningRun).where(DailyLearningRun.run_date == current.date())
        )

        if run and run.status == "succeeded":
            return "already-published"
        manually_queued = bool(run and run.status == "pending" and run.scheduled_for <= current_naive)
        if not manually_queued:
            if not record.enabled:
                return "disabled"
            if current.time().replace(tzinfo=None) < record.publish_time:
                return "not-due"
            if run is None:
                run = DailyLearningRun(
                    run_date=current.date(),
                    scheduled_for=datetime.combine(current.date(), record.publish_time),
                    status="pending",
                    next_retry_at=current_naive,
                )
                session.add(run)
                try:
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    run = session.scalar(
                        select(DailyLearningRun).where(DailyLearningRun.run_date == current.date())
                    )

        if run is None:
            return "not-due"
        if run.status == "running" and run.started_at:
            if run.started_at > current_naive - timedelta(minutes=10):
                return "running"
            run.status = "failed"
            run.last_error = "上一次任务运行超时"
            run.next_retry_at = current_naive
        if run.status == "failed":
            if not record.enabled and not manually_queued:
                return "disabled"
            if run.attempt_count >= MAX_ATTEMPTS:
                return "failed"
            if run.next_retry_at and run.next_retry_at > current_naive:
                return "retry-wait"

        article = session.scalar(
            select(Article).where(Article.slug == _article_slug(current.date()))
        )
        if article:
            run.status = "succeeded"
            run.article_id = article.id
            run.completed_at = current_naive
            run.last_error = None
            run.next_retry_at = None
            session.commit()
            return "already-published"

        try:
            configuration = _ai_configuration(record)
        except DailyLearningError as error:
            run.status = "failed"
            run.last_error = str(error)
            run.next_retry_at = None
            run.completed_at = current_naive
            session.commit()
            return "failed"

        run.status = "running"
        run.attempt_count += 1
        run.started_at = current_naive
        run.completed_at = None
        run.last_error = None
        run.next_retry_at = None
        session.add(run)
        session.commit()
        run_id = run.id

        previous_questions = _recent_question_titles(session)
        try:
            generated = question_generator(configuration, previous_questions)
        except Exception as error:
            _mark_failed(session, run_id, error, current_naive)
            return "failed"

        run = session.get(DailyLearningRun, run_id)
        try:
            series = session.scalar(
                select(Series).where(Series.slug == DAILY_SERIES_SLUG).with_for_update()
            )
            if series is None:
                series = Series(
                    slug=DAILY_SERIES_SLUG,
                    title=DAILY_SERIES_TITLE,
                    description="每天十道前端面试题与参考答案。",
                    sort_order=2,
                )
                session.add(series)
                session.flush()
            max_order = session.scalar(
                select(func.max(Article.series_order)).where(Article.series_id == series.id)
            ) or 0
            article = Article(
                slug=_article_slug(current.date()),
                title=f"{current.date().isoformat()}-学习问答",
                summary=f"{current.date().isoformat()} 前端面试学习问答，包含 10 道题目与参考答案。",
                content_markdown=_build_markdown(generated),
                cover_image_url=None,
                is_repost=False,
                author="AI自动生成",
                source_url=None,
                published_at=current_naive,
                updated_at=current_naive,
                views=0,
                likes=0,
                tags=list(record.tags or DEFAULT_DAILY_TAGS),
                category=DAILY_CATEGORY,
                series_id=series.id,
                series_order=max_order + 1,
            )
            session.add(article)
            session.flush()
            run.status = "succeeded"
            run.article_id = article.id
            run.completed_at = current_naive
            run.last_error = None
            run.next_retry_at = None
            session.add(run)
            session.commit()
        except IntegrityError as error:
            session.rollback()
            article = session.scalar(
                select(Article).where(Article.slug == _article_slug(current.date()))
            )
            if article is None:
                _mark_failed(session, run_id, error, current_naive)
                return "failed"
            run = session.get(DailyLearningRun, run_id)
            run.status = "succeeded"
            run.article_id = article.id
            run.completed_at = current_naive
            run.last_error = None
            run.next_retry_at = None
            session.commit()
        invalidate_article_list_cache()
        return "published"
    finally:
        _release_runner_lock(lock_token)
