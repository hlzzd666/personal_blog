import calendar
import ipaddress
import json
import logging
import re
import socket
import string
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
from backend.app.models.article import Article, ArticleCategory, ArticleTag
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
from backend.app.services.taxonomy import apply_article_taxonomy

logger = logging.getLogger(__name__)

BEIJING_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
DAILY_CATEGORY = "每日问答"
DEFAULT_DAILY_TAGS = ["前端面试", "每日问答"]
DEFAULT_GENERATION_TOPIC = "前端面试题"
DEFAULT_SYSTEM_PROMPT = "你是严谨的资深前端面试官，只输出符合要求的 JSON。"
DEFAULT_GENERATION_INSTRUCTIONS = (
    "题目覆盖 JavaScript、TypeScript、Vue、React、浏览器、CSS、网络、性能和工程化，"
    "兼顾基础、中级和高级难度。答案准确、清晰，必要时给出简短代码示例。"
)
DEFAULT_GENERATION_COUNT = 10
DEFAULT_QUESTION_LABEL = "题目"
DEFAULT_ANSWER_LABEL = "参考答案"
DEFAULT_TITLE_TEMPLATE = "{date}-学习问答"
DEFAULT_SLUG_TEMPLATE = "{date}-学习记录"
DEFAULT_SUMMARY_TEMPLATE = "{date} 前端面试学习问答，包含 10 道题目与参考答案。"
DEFAULT_AUTHOR = "AI自动生成"
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_RETRY_DELAYS_MINUTES = [10, 30]
MAX_SAFE_ATTEMPTS = 10
MAX_SAFE_RETRY_DELAY_MINUTES = 1440
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
    generation_instructions: str = DEFAULT_GENERATION_INSTRUCTIONS
    generation_topic: str = DEFAULT_GENERATION_TOPIC
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    generation_count: int = DEFAULT_GENERATION_COUNT


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
        schedule_type="daily",
        generation_instructions=DEFAULT_GENERATION_INSTRUCTIONS,
        generation_topic=DEFAULT_GENERATION_TOPIC,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        generation_count=DEFAULT_GENERATION_COUNT,
        question_label=DEFAULT_QUESTION_LABEL,
        answer_label=DEFAULT_ANSWER_LABEL,
        article_title_template=DEFAULT_TITLE_TEMPLATE,
        article_slug_template=DEFAULT_SLUG_TEMPLATE,
        article_summary_template=DEFAULT_SUMMARY_TEMPLATE,
        author=DEFAULT_AUTHOR,
        tags=list(DEFAULT_DAILY_TAGS),
        max_attempts=DEFAULT_MAX_ATTEMPTS,
        retry_delays_minutes=list(DEFAULT_RETRY_DELAYS_MINUTES),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def serialize_settings(
    session: Session, record: DailyLearningSettings
) -> DailyLearningSettingsResponse:
    category = session.get(ArticleCategory, record.category_id) if record.category_id else None
    selected_tag_ids = list(record.tag_ids or [])
    selected_tags = list(record.tags or [])
    if selected_tag_ids:
        tag_rows = list(session.scalars(select(ArticleTag).where(ArticleTag.id.in_(selected_tag_ids))))
        tag_by_id = {tag.id: tag for tag in tag_rows}
        selected_tags = [tag_by_id[tag_id].name for tag_id in selected_tag_ids if tag_id in tag_by_id]
    series = session.get(Series, record.series_id) if record.series_id else None
    return DailyLearningSettingsResponse(
        enabled=record.enabled,
        publish_time=record.publish_time,
        schedule_type=record.schedule_type or "daily",
        schedule_weekday=record.schedule_weekday,
        schedule_day=record.schedule_day,
        ai_base_url=record.ai_base_url,
        ai_model=record.ai_model,
        api_key_configured=bool(record.encrypted_api_key),
        generation_topic=record.generation_topic or DEFAULT_GENERATION_TOPIC,
        system_prompt=record.system_prompt or DEFAULT_SYSTEM_PROMPT,
        generation_instructions=(
            record.generation_instructions
            if record.generation_instructions is not None
            else DEFAULT_GENERATION_INSTRUCTIONS
        ),
        generation_count=record.generation_count or DEFAULT_GENERATION_COUNT,
        question_label=record.question_label or DEFAULT_QUESTION_LABEL,
        answer_label=record.answer_label or DEFAULT_ANSWER_LABEL,
        article_title_template=record.article_title_template or DEFAULT_TITLE_TEMPLATE,
        article_slug_template=record.article_slug_template or DEFAULT_SLUG_TEMPLATE,
        article_summary_template=(
            record.article_summary_template
            if record.article_summary_template is not None
            else DEFAULT_SUMMARY_TEMPLATE
        ),
        author=record.author or "",
        series_id=record.series_id,
        series_title=series.title if series else None,
        category_id=record.category_id,
        category=category.name if category else None,
        tag_ids=selected_tag_ids,
        tags=selected_tags,
        max_attempts=record.max_attempts or DEFAULT_MAX_ATTEMPTS,
        retry_delays_minutes=(
            list(record.retry_delays_minutes)
            if record.retry_delays_minutes is not None
            else list(DEFAULT_RETRY_DELAYS_MINUTES)
        ),
        updated_at=record.updated_at,
    )


def _get_or_create_tag(session: Session, name: str) -> ArticleTag:
    tag = session.scalar(select(ArticleTag).where(ArticleTag.name == name))
    if tag is None:
        tag = ArticleTag(name=name)
        session.add(tag)
        session.flush()
    return tag


def _resolve_taxonomy(
    session: Session,
    record: DailyLearningSettings,
    payload: DailyLearningSettingsUpdate,
) -> tuple[ArticleCategory, list[ArticleTag]]:
    if "category_id" in payload.model_fields_set:
        if payload.category_id is None:
            raise DailyLearningConfigurationError("每日问答必须选择文章分类")
        category = session.get(ArticleCategory, payload.category_id)
        if category is None:
            raise DailyLearningConfigurationError("所选文章分类不存在")
    else:
        category = session.get(ArticleCategory, record.category_id) if record.category_id else None
    if category is None:
        category = session.scalar(select(ArticleCategory).where(ArticleCategory.name == DAILY_CATEGORY))
    if category is None:
        category = ArticleCategory(name=DAILY_CATEGORY)
        session.add(category)
        session.flush()

    if payload.tag_ids is not None:
        tag_ids = list(dict.fromkeys(payload.tag_ids))
        tags = list(session.scalars(select(ArticleTag).where(ArticleTag.id.in_(tag_ids)))) if tag_ids else []
        if len(tags) != len(tag_ids):
            raise DailyLearningConfigurationError("所选文章标签中存在无效项")
        by_id = {tag.id: tag for tag in tags}
        return category, [by_id[tag_id] for tag_id in tag_ids]

    if payload.tags is not None:
        tag_names = payload.tags
    elif record.tag_ids:
        tag_names = [
            tag.name
            for tag in session.scalars(select(ArticleTag).where(ArticleTag.id.in_(record.tag_ids)))
        ]
    else:
        tag_names = list(record.tags or DEFAULT_DAILY_TAGS)
    tags = [_get_or_create_tag(session, tag_name) for tag_name in dict.fromkeys(tag_names)]
    return category, tags


TEMPLATE_FIELDS = {"date", "year", "month", "day"}


def _validate_template(value: str, *, field_name: str, require_date: bool = False) -> None:
    fields = set()
    formatter = string.Formatter()
    try:
        for _, field, format_spec, conversion in formatter.parse(value):
            if field:
                if format_spec or conversion:
                    raise DailyLearningConfigurationError(
                        f"{field_name}模板只支持简单变量，不支持格式化修饰符"
                    )
                fields.add(field)
    except ValueError as error:
        raise DailyLearningConfigurationError(f"{field_name}模板格式无效") from error
    if fields - TEMPLATE_FIELDS:
        raise DailyLearningConfigurationError(f"{field_name}模板只支持 date、year、month、day 变量")
    if require_date and "date" not in fields:
        raise DailyLearningConfigurationError("文章别名模板必须包含 {date}")


def render_article_template(template: str, run_date: date) -> str:
    return template.format(
        date=run_date.isoformat(),
        year=f"{run_date.year:04d}",
        month=f"{run_date.month:02d}",
        day=f"{run_date.day:02d}",
    ).strip()


def is_publish_date(run_date: date, record: DailyLearningSettings) -> bool:
    schedule_type = record.schedule_type or "daily"
    if schedule_type == "daily":
        return True
    if schedule_type == "weekly":
        return run_date.isoweekday() == (record.schedule_weekday or 1)
    if schedule_type == "monthly":
        configured_day = record.schedule_day or 1
        last_day = calendar.monthrange(run_date.year, run_date.month)[1]
        return run_date.day == min(configured_day, last_day)
    return False


def retry_delay(record: DailyLearningSettings, attempt_count: int) -> timedelta:
    delays = list(record.retry_delays_minutes or DEFAULT_RETRY_DELAYS_MINUTES)
    minutes = delays[min(max(attempt_count - 1, 0), len(delays) - 1)]
    return timedelta(minutes=minutes)


def update_daily_learning_settings(
    session: Session, payload: DailyLearningSettingsUpdate
) -> DailyLearningSettingsResponse:
    record = get_or_create_settings(session)
    ai_base_url = validate_ai_base_url(payload.ai_base_url) if payload.ai_base_url else ""
    api_key = (payload.api_key or "").strip()
    encrypted_api_key = encrypt_api_key(api_key) if api_key else record.encrypted_api_key
    if payload.enabled and not (ai_base_url and payload.ai_model and encrypted_api_key):
        raise DailyLearningConfigurationError("启用前请完整配置 AI 地址、模型和 API Key")

    schedule_type = payload.schedule_type or record.schedule_type or "daily"
    if schedule_type == "weekly" and payload.schedule_weekday is None and record.schedule_weekday is None:
        raise DailyLearningConfigurationError("每周发布必须选择星期几")
    if schedule_type == "monthly" and payload.schedule_day is None and record.schedule_day is None:
        raise DailyLearningConfigurationError("每月发布必须选择日期")
    schedule_weekday = payload.schedule_weekday if payload.schedule_type is not None else record.schedule_weekday
    schedule_day = payload.schedule_day if payload.schedule_type is not None else record.schedule_day
    if schedule_type == "daily":
        schedule_weekday = None
        schedule_day = None

    if "series_id" in payload.model_fields_set:
        if payload.series_id is not None and session.get(Series, payload.series_id) is None:
            raise DailyLearningConfigurationError("所选专题不存在")

    generation_topic = (
        payload.generation_topic
        if payload.generation_topic is not None
        else record.generation_topic or DEFAULT_GENERATION_TOPIC
    )
    system_prompt = (
        payload.system_prompt
        if payload.system_prompt is not None
        else record.system_prompt or DEFAULT_SYSTEM_PROMPT
    )
    generation_instructions = (
        payload.generation_instructions
        if payload.generation_instructions is not None
        else (
            record.generation_instructions
            if record.generation_instructions is not None
            else DEFAULT_GENERATION_INSTRUCTIONS
        )
    )
    generation_count = (
        payload.generation_count
        if payload.generation_count is not None
        else record.generation_count or DEFAULT_GENERATION_COUNT
    )
    question_label = (
        payload.question_label
        if payload.question_label is not None
        else record.question_label or DEFAULT_QUESTION_LABEL
    )
    answer_label = (
        payload.answer_label
        if payload.answer_label is not None
        else record.answer_label or DEFAULT_ANSWER_LABEL
    )
    title_template = (
        payload.article_title_template
        if payload.article_title_template is not None
        else record.article_title_template or DEFAULT_TITLE_TEMPLATE
    )
    slug_template = (
        payload.article_slug_template
        if payload.article_slug_template is not None
        else record.article_slug_template or DEFAULT_SLUG_TEMPLATE
    )
    summary_template = (
        payload.article_summary_template
        if payload.article_summary_template is not None
        else (
            record.article_summary_template
            if record.article_summary_template is not None
            else DEFAULT_SUMMARY_TEMPLATE
        )
    )
    if not title_template or not slug_template:
        raise DailyLearningConfigurationError("文章标题和文章别名模板不能为空")
    _validate_template(title_template, field_name="文章标题")
    _validate_template(slug_template, field_name="文章别名", require_date=True)
    _validate_template(summary_template, field_name="文章摘要")
    if not generation_topic or not system_prompt or not question_label or not answer_label:
        raise DailyLearningConfigurationError("生成主题、AI 角色、问题标题和答案标题不能为空")
    max_attempts = (
        payload.max_attempts
        if payload.max_attempts is not None
        else record.max_attempts or DEFAULT_MAX_ATTEMPTS
    )
    retry_delays = list(
        payload.retry_delays_minutes
        if payload.retry_delays_minutes is not None
        else record.retry_delays_minutes or DEFAULT_RETRY_DELAYS_MINUTES
    )
    if max_attempts > MAX_SAFE_ATTEMPTS:
        raise DailyLearningConfigurationError(f"最大尝试次数不能超过 {MAX_SAFE_ATTEMPTS} 次")
    if len(retry_delays) > max_attempts - 1:
        raise DailyLearningConfigurationError("重试间隔数量不能超过最大尝试次数减一")
    if max_attempts > 1 and not retry_delays:
        raise DailyLearningConfigurationError("存在重试时必须配置重试间隔")
    if any(delay < 1 or delay > MAX_SAFE_RETRY_DELAY_MINUTES for delay in retry_delays):
        raise DailyLearningConfigurationError("重试间隔必须在 1 至 1440 分钟之间")

    category, tags = _resolve_taxonomy(session, record, payload)

    record.enabled = payload.enabled
    record.publish_time = payload.publish_time
    record.schedule_type = schedule_type
    record.schedule_weekday = schedule_weekday
    record.schedule_day = schedule_day
    record.ai_base_url = ai_base_url
    record.ai_model = payload.ai_model
    record.encrypted_api_key = encrypted_api_key
    record.generation_topic = generation_topic
    record.system_prompt = system_prompt
    record.generation_instructions = generation_instructions
    record.generation_count = generation_count
    record.question_label = question_label
    record.answer_label = answer_label
    record.article_title_template = title_template
    record.article_slug_template = slug_template
    record.article_summary_template = summary_template
    record.author = payload.author if payload.author is not None else (record.author or DEFAULT_AUTHOR)
    if "series_id" in payload.model_fields_set:
        record.series_id = payload.series_id
    record.category_id = category.id
    record.tag_ids = [tag.id for tag in tags]
    record.tags = [tag.name for tag in tags]
    record.max_attempts = max_attempts
    record.retry_delays_minutes = retry_delays
    session.add(record)
    session.commit()
    session.refresh(record)
    return serialize_settings(session, record)


def _ai_configuration(record: DailyLearningSettings) -> AIConfiguration:
    if not record.ai_base_url or not record.ai_model:
        raise DailyLearningConfigurationError("请先配置 AI 接口地址和模型")
    return AIConfiguration(
        base_url=validate_ai_base_url(record.ai_base_url),
        model=record.ai_model,
        api_key=decrypt_api_key(record.encrypted_api_key),
        generation_topic=record.generation_topic or DEFAULT_GENERATION_TOPIC,
        system_prompt=record.system_prompt or DEFAULT_SYSTEM_PROMPT,
        generation_instructions=(
            record.generation_instructions
            if record.generation_instructions is not None
            else DEFAULT_GENERATION_INSTRUCTIONS
        ),
        generation_count=record.generation_count or DEFAULT_GENERATION_COUNT,
    )


def _normalize_question(value: str) -> str:
    return re.sub(r"[\W_]+", "", value, flags=re.UNICODE).casefold()


def _parse_generated_questions(
    content: str,
    previous_questions: list[str],
    expected_count: int = DEFAULT_GENERATION_COUNT,
) -> GeneratedQuestionSet:
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
        raise DailyLearningAIError(f"AI 返回内容不是有效的 {expected_count} 道问答 JSON") from error
    if len(generated.questions) != expected_count:
        raise DailyLearningAIError(f"AI 必须返回恰好 {expected_count} 道问答")

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
        f"请围绕“{configuration.generation_topic}”生成恰好 {configuration.generation_count} 道问答，"
        "每道问答包含一个问题和对应的参考答案。\n"
        f"额外要求：{configuration.generation_instructions}\n"
        "题目之间不能重复，也不要复用最近题目。\n"
        f"最近题目：\n{previous_text}\n"
        "只返回 JSON，不要使用 Markdown 代码围栏。格式必须是："
        '{"questions":[{"question":"问题内容","answer":"参考答案内容"}]}。'
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
                            "content": configuration.system_prompt,
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
    return _parse_generated_questions(content, previous_questions, configuration.generation_count)


def _recent_question_titles(session: Session) -> list[str]:
    articles = list(
        session.scalars(
            select(Article)
            .join(DailyLearningRun, DailyLearningRun.article_id == Article.id)
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


def _article_slug(record: DailyLearningSettings, run_date: date) -> str:
    return render_article_template(record.article_slug_template or DEFAULT_SLUG_TEMPLATE, run_date)


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
    article = session.scalar(select(Article).where(Article.slug == _article_slug(record, run_date)))
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


def _build_markdown(
    result: GeneratedQuestionSet,
    question_label: str = DEFAULT_QUESTION_LABEL,
    answer_label: str = DEFAULT_ANSWER_LABEL,
) -> str:
    sections = []
    for index, item in enumerate(result.questions, 1):
        question = f"{question_label}：{item.question}" if question_label else item.question
        sections.append(f"## {index}. {question}\n\n**{answer_label}：**\n\n{item.answer}")
    return "\n\n---\n\n".join(sections)


def _mark_failed(
    session: Session,
    run_id: int,
    error: Exception,
    now: datetime,
    record: DailyLearningSettings,
) -> None:
    run = session.get(DailyLearningRun, run_id)
    if run is None:
        return
    run.status = "failed"
    run.last_error = str(error)[:2000] or error.__class__.__name__
    run.completed_at = now
    run.next_retry_at = (
        now + retry_delay(record, run.attempt_count)
        if run.attempt_count < (record.max_attempts or DEFAULT_MAX_ATTEMPTS)
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
            if (
                not is_publish_date(current.date(), record)
                or current.time().replace(tzinfo=None) < record.publish_time
            ):
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
            if run.attempt_count >= (record.max_attempts or DEFAULT_MAX_ATTEMPTS):
                return "failed"
            if run.next_retry_at and run.next_retry_at > current_naive:
                return "retry-wait"

        article = session.scalar(
            select(Article).where(Article.slug == _article_slug(record, current.date()))
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
            _mark_failed(session, run_id, error, current_naive, record)
            return "failed"

        run = session.get(DailyLearningRun, run_id)
        try:
            series = session.get(Series, record.series_id) if record.series_id else None
            max_order = session.scalar(
                select(func.max(Article.series_order)).where(Article.series_id == series.id)
            ) or 0 if series else 0
            title = render_article_template(
                record.article_title_template or DEFAULT_TITLE_TEMPLATE, current.date()
            )
            slug = _article_slug(record, current.date())
            summary = render_article_template(
                record.article_summary_template
                if record.article_summary_template is not None
                else DEFAULT_SUMMARY_TEMPLATE,
                current.date(),
            )
            article = Article(
                slug=slug,
                title=title,
                summary=summary,
                content_markdown=_build_markdown(
                    generated, record.question_label or DEFAULT_QUESTION_LABEL, record.answer_label or DEFAULT_ANSWER_LABEL
                ),
                cover_image_url=None,
                is_repost=False,
                author=record.author or "",
                source_url=None,
                published_at=current_naive,
                updated_at=current_naive,
                views=0,
                likes=0,
                tags=list(record.tags or DEFAULT_DAILY_TAGS),
                category=DAILY_CATEGORY,
                series_id=series.id if series else None,
                series_order=max_order + 1 if series else None,
            )
            session.add(article)
            apply_article_taxonomy(
                session,
                article,
                category_id=record.category_id,
                tag_ids=record.tag_ids,
            )
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
                select(Article).where(Article.slug == _article_slug(record, current.date()))
            )
            if article is None:
                _mark_failed(session, run_id, error, current_naive, record)
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
