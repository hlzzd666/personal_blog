import logging
from collections.abc import Sequence
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.schemas.common import ApiResponse, ErrorDetail

logger = logging.getLogger(__name__)

# 校验错误中字段名到中文文案的映射，用于把 loc 里的英文字段名转成用户可读的提示。
_FIELD_LABELS: dict[str, str] = {
    # 登录
    "username": "账号",
    "password": "密码",
    # 文章 / 专题 / 动态公共字段
    "slug": "别名",
    "title": "标题",
    "summary": "摘要",
    "content_markdown": "正文内容",
    "cover_image_url": "封面图链接",
    "is_repost": "是否转载",
    "author": "作者",
    "source_url": "转载来源链接",
    "published_at": "发表时间",
    "updated_at": "更新时间",
    "views": "浏览量",
    "likes": "点赞数",
    "tags": "标签",
    "category": "分类",
    "series_id": "所属专题",
    "series_order": "专题内排序",
    "description": "描述",
    "sort_order": "排序值",
    "external_url": "外部链接",
    # 站点设置
    "site_subtitle": "站点副标题",
    "hero_image_url": "首页横幅图链接",
    "nav_brand": "导航品牌名",
    "site_launched_on": "建站日期",
    "owner_avatar_url": "站长头像链接",
    "owner_location_name": "站长地址",
    "owner_latitude": "站长纬度",
    "owner_longitude": "站长经度",
    "visual_assets": "视觉资产",
    "quotes": "语录",
    "key": "标识",
    "name": "名称",
    "usage": "用途",
    "image_url": "图片链接",
    "enabled": "是否启用",
    "opacity": "透明度",
    "note": "备注",
    "text": "内容",
    # 3D 展厅
    "hall_name": "展厅名称",
    "entry_title": "入口标题",
    "show_logo": "是否显示 Logo",
    "logo_url": "Logo 图片链接",
    "epithet": "称号",
    "faction": "势力",
    "bounty": "悬赏",
    "ability": "能力",
    "quote": "代表台词",
    "poster_url": "人物海报链接",
    "is_visible": "是否在展厅展示",
    "character_ids": "人物顺序",
    # 关于我
    "display_name": "展示名称",
    "role": "角色",
    "headline": "个人标语",
    "bio": "个人简介",
    "avatar_url": "头像链接",
    "resume_url": "简历链接",
    "resume_filename": "简历文件名",
    "status_text": "状态文本",
    "email": "邮箱",
    "location_name": "所在地",
    "location_longitude": "经度",
    "location_latitude": "纬度",
    "metrics": "数据指标",
    "value": "数值",
    "label": "名称",
    "work_experiences": "工作经历",
    "organization": "组织/公司",
    "period": "时间段",
    "project_experiences": "项目经历",
    "link_url": "链接",
    "technologies": "技术标签",
    "skills": "技术栈",
    "icon_url": "图标链接",
    "social_links": "社交链接",
    "platform": "平台",
    "url": "链接地址",
    "interests": "兴趣爱好",
    "site_title": "站点标题",
    "site_description": "站点描述",
    "site_launched_at": "建站时间",
    "site_stack": "站点技术栈",
    "site_repository_url": "仓库链接",
    # 每日问答
    "publish_time": "发布时间",
    "ai_base_url": "AI 接口地址",
    "ai_model": "AI 模型",
    "api_key": "API Key",
    "generation_instructions": "生成指令",
    # 查询参数
    "page": "页码",
    "page_size": "每页数量",
    "search": "搜索关键词",
    "tag": "标签",
}

# HTTP 状态码兜底文案；仅当异常 detail 为空或是 Starlette 默认英文短语时使用。
_STATUS_MESSAGES: dict[int, str] = {
    400: "请求参数有误",
    401: "请先登录",
    403: "没有权限执行该操作",
    404: "请求的资源不存在",
    405: "请求方法不允许",
    409: "数据冲突",
    413: "上传内容过大",
    415: "不支持的文件类型",
    422: "请求参数不正确",
    429: "请求过于频繁，请稍后重试",
    500: "服务器内部错误，请稍后重试",
    502: "上游服务异常，请稍后重试",
    503: "服务暂时不可用，请稍后重试",
}

_ENGLISH_DEFAULT_DETAILS = {
    "bad request",
    "unauthorized",
    "forbidden",
    "not found",
    "method not allowed",
    "conflict",
    "internal server error",
}


def _request_id_from(request: Request) -> str:
    return getattr(request.state, "request_id", uuid4().hex)


def _error_response(
    request: Request,
    status_code: int,
    message: str,
    detail: object,
) -> JSONResponse:
    payload = ApiResponse[ErrorDetail](
        code=status_code,
        status=status_code,
        message=message,
        data=ErrorDetail(detail=detail),
        request_id=_request_id_from(request),
    )
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(payload, custom_encoder={Exception: str}),
    )


def _http_exception_message(status_code: int, detail: object) -> str:
    if isinstance(detail, str) and detail.strip():
        if detail.strip().lower() not in _ENGLISH_DEFAULT_DETAILS:
            return detail
    return _STATUS_MESSAGES.get(status_code, "请求失败，请稍后重试")


def _format_error_location(loc: Sequence[object]) -> str:
    parts = list(loc)
    if parts and str(parts[0]) in {"body", "query", "path", "header", "cookie"}:
        parts = parts[1:]
    segments: list[str] = []
    for part in parts:
        if isinstance(part, int):
            segments.append(f"第 {part + 1} 项")
        else:
            segments.append(_FIELD_LABELS.get(str(part), str(part)))
    return " ".join(segments)


def _describe_validation_error(error: dict[str, object]) -> str:
    error_type = str(error.get("type", ""))
    msg = str(error.get("msg", "")).strip()
    ctx = error.get("ctx") if isinstance(error.get("ctx"), dict) else {}

    if error_type == "missing":
        return "为必填项，请填写"
    if error_type == "string_too_short":
        return f"长度至少为 {ctx.get('min_length')} 个字符"
    if error_type == "string_too_long":
        return f"长度不能超过 {ctx.get('max_length')} 个字符"
    if error_type == "string_pattern_mismatch":
        pattern = str(ctx.get("pattern", ""))
        if "a-z0-9" in pattern and "-" in pattern:
            return "只能包含小写字母、数字和中划线"
        return "格式不符合要求"
    if error_type == "too_short":
        return f"至少需要 {ctx.get('min_length')} 项"
    if error_type == "too_long":
        return f"最多允许 {ctx.get('max_length')} 项"
    if error_type == "greater_than_equal":
        return f"不能小于 {ctx.get('ge')}"
    if error_type == "less_than_equal":
        return f"不能大于 {ctx.get('le')}"
    if error_type == "greater_than":
        return f"必须大于 {ctx.get('gt')}"
    if error_type == "less_than":
        return f"必须小于 {ctx.get('lt')}"
    if error_type.startswith("url"):
        return "链接格式不正确，需要完整的 http(s) 地址"
    if error_type in {"datetime_parsing", "datetime_from_date_parsing", "datetime_type"}:
        return "时间格式不正确"
    if error_type in {"date_parsing", "date_from_datetime_parsing", "date_type"}:
        return "日期格式不正确"
    if error_type in {"time_parsing", "time_type"}:
        return "时间格式不正确"
    if error_type in {"int_parsing", "int_type"}:
        return "必须是整数"
    if error_type in {"float_parsing", "float_type", "finite_number"}:
        return "必须是数字"
    if error_type in {"bool_parsing", "bool_type"}:
        return "必须是布尔值"
    if error_type == "string_type":
        return "必须是字符串"
    if error_type == "list_type":
        return "必须是数组"
    if error_type in {"dict_type", "model_type", "model_attributes_type"}:
        return "数据格式不正确"
    if error_type in {"literal_error", "enum"}:
        return "取值不在允许范围内"
    if error_type == "json_invalid":
        return "不是合法的 JSON"
    if error_type == "extra_forbidden":
        return "不允许传入该字段"
    if error_type == "value_error":
        # schema 里 raise ValueError("中文原因") 产生的错误，msg 带 "Value error, " 前缀。
        prefix = "Value error, "
        return msg[len(prefix):] if msg.startswith(prefix) else (msg or "取值不合法")
    return msg or "取值不合法"


def build_validation_message(errors: Sequence[dict[str, object]]) -> str:
    items: list[str] = []
    for error in errors[:3]:
        if error.get("type") == "json_invalid":
            # JSON 解析失败的 loc 是字节偏移，不是字段路径，直接给整体提示。
            items.append("请求体不是合法的 JSON")
            continue
        label = _format_error_location(error.get("loc", ()))
        description = _describe_validation_error(error)
        items.append(f"{label}：{description}" if label else description)
    if not items:
        return "请求参数校验失败"
    message = "；".join(items)
    if len(errors) > 3:
        message += f"；等 {len(errors)} 项错误"
    return f"请求参数校验失败：{message}"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        return _error_response(
            request,
            exc.status_code,
            _http_exception_message(exc.status_code, exc.detail),
            exc.detail,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_starlette_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return _error_response(
            request,
            exc.status_code,
            _http_exception_message(exc.status_code, exc.detail),
            exc.detail,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        return _error_response(
            request,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            build_validation_message(errors),
            errors,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "未处理的服务器异常 request_id=%s path=%s",
            _request_id_from(request),
            request.url.path,
        )
        return _error_response(
            request,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "服务器内部错误，请稍后重试",
            str(exc),
        )
