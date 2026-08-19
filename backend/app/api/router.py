from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.response import build_success_response
from backend.app.core.config import settings
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.site_settings import SiteSettings, SiteSettingsUpdate
from backend.app.services.site_settings import get_site_settings, update_site_settings
from backend.app.schemas.visitor_location import VisitorLocation
from backend.app.services.visitor_location import resolve_visitor_location
from backend.app.core.database import get_db_session
from backend.app.schemas.article import (
    ArticleCreate,
    ArticleListResponse,
    ArticleResponse,
    ArticleUpdate,
)
from backend.app.services.articles import (
    create_article,
    delete_article,
    get_article,
    get_public_article,
    like_article,
    list_articles,
    update_article,
)

router = APIRouter()

MAX_IMAGE_SIZE = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


class ImageUploadResult(BaseModel):
    url: str
    filename: str
    content_type: str
    size: int


@router.get("/health", tags=["system"], response_model=ApiResponse[dict[str, str]])
def health_check(request: Request) -> ApiResponse[dict[str, str]]:
    return build_success_response(
        request,
        {"status": "ok", "service": "personal-blog-api"},
    )


def get_client_ip(request: Request) -> str:
    client_ip = request.client.host if request.client else "unknown"
    if client_ip not in settings.trusted_proxy_ip_list:
        return client_ip

    forwarded_for = request.headers.get("X-Forwarded-For")
    if not forwarded_for:
        return client_ip

    return forwarded_for.split(",", maxsplit=1)[0].strip()


@router.get("/visitor-location", tags=["site"], response_model=ApiResponse[VisitorLocation])
def read_visitor_location(request: Request) -> ApiResponse[VisitorLocation]:
    site_settings = get_site_settings()
    return build_success_response(
        request,
        resolve_visitor_location(
            get_client_ip(request),
            site_settings.owner_location_name,
            site_settings.owner_latitude,
            site_settings.owner_longitude,
        ),
    )


@router.get("/site-settings", tags=["site"], response_model=ApiResponse[SiteSettings])
def read_site_settings(request: Request) -> ApiResponse[SiteSettings]:
    return build_success_response(request, get_site_settings())


@router.put("/site-settings", tags=["site"], response_model=ApiResponse[SiteSettings])
def write_site_settings(
    request: Request, payload: SiteSettingsUpdate
) -> ApiResponse[SiteSettings]:
    return build_success_response(request, update_site_settings(payload))


@router.get("/articles", tags=["articles"], response_model=ApiResponse[ArticleListResponse])
def read_public_articles(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    category: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    session: Session = Depends(get_db_session),
) -> ApiResponse[ArticleListResponse]:
    items, total = list_articles(
        session,
        public_only=True,
        page=page,
        page_size=page_size,
        category=category,
        tag=tag,
        search=search,
    )
    return build_success_response(
        request,
        ArticleListResponse(items=items, total=total, page=page, page_size=page_size),
    )


@router.get("/articles/manage", tags=["articles"], response_model=ApiResponse[ArticleListResponse])
def read_manage_articles(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    session: Session = Depends(get_db_session),
) -> ApiResponse[ArticleListResponse]:
    items, total = list_articles(
        session,
        public_only=False,
        page=page,
        page_size=page_size,
        category=category,
        tag=tag,
        search=search,
    )
    return build_success_response(
        request,
        ArticleListResponse(items=items, total=total, page=page, page_size=page_size),
    )


@router.get("/articles/{slug}", tags=["articles"], response_model=ApiResponse[ArticleResponse])
def read_public_article(
    request: Request,
    slug: str,
    session: Session = Depends(get_db_session),
) -> ApiResponse[ArticleResponse]:
    article = get_public_article(session, slug)
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    return build_success_response(request, ArticleResponse.model_validate(article))


@router.post("/articles/{slug}/like", tags=["articles"], response_model=ApiResponse[dict[str, int]])
def like_public_article(
    request: Request,
    slug: str,
    session: Session = Depends(get_db_session),
) -> ApiResponse[dict[str, int]]:
    article = like_article(session, slug)
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    return build_success_response(request, {"likes": article.likes}, message="点赞成功")


@router.post("/articles", tags=["articles"], response_model=ApiResponse[ArticleResponse])
def create_manage_article(
    request: Request,
    payload: ArticleCreate,
    session: Session = Depends(get_db_session),
) -> ApiResponse[ArticleResponse]:
    try:
        article = create_article(session, payload)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return build_success_response(request, ArticleResponse.model_validate(article), message="文章创建成功")


@router.put("/articles/{article_id}", tags=["articles"], response_model=ApiResponse[ArticleResponse])
def update_manage_article(
    request: Request,
    article_id: int,
    payload: ArticleUpdate,
    session: Session = Depends(get_db_session),
) -> ApiResponse[ArticleResponse]:
    article = get_article(session, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    try:
        article = update_article(session, article, payload)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return build_success_response(request, ArticleResponse.model_validate(article), message="文章更新成功")


@router.delete("/articles/{article_id}", tags=["articles"], response_model=ApiResponse[dict[str, int]])
def delete_manage_article(
    request: Request,
    article_id: int,
    session: Session = Depends(get_db_session),
) -> ApiResponse[dict[str, int]]:
    article = get_article(session, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    delete_article(session, article)
    return build_success_response(request, {"id": article_id}, message="文章已删除")


@router.post(
    "/media/images",
    tags=["media"],
    response_model=ApiResponse[ImageUploadResult],
)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
) -> ApiResponse[ImageUploadResult]:
    extension = ALLOWED_IMAGE_TYPES.get(file.content_type or "")
    if extension is None:
        raise HTTPException(status_code=415, detail="仅支持 JPG、PNG、WEBP 或 GIF 图片")

    upload_dir = Path("backend/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    destination = upload_dir / filename
    size = 0

    try:
        with destination.open("wb") as target:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_IMAGE_SIZE:
                    destination.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="图片大小不能超过 10 MB")
                target.write(chunk)
    finally:
        await file.close()

    result = ImageUploadResult(
        url=f"{settings.public_base_url.rstrip('/')}/uploads/{filename}",
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
        size=size,
    )
    return build_success_response(request, result, message="图片上传成功")
