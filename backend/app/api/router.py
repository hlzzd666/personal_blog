from pathlib import Path
from hashlib import sha256
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.response import build_success_response
from backend.app.core.config import settings
from backend.app.schemas.auth import AdminLoginRequest, AdminSessionResponse
from backend.app.schemas.about_profile import AboutProfileResponse, AboutProfileUpdate
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.site_settings import SiteSettings, SiteSettingsUpdate
from backend.app.services.site_settings import get_site_settings, update_site_settings
from backend.app.schemas.visitor_location import VisitorLocation
from backend.app.services.visitor_location import resolve_visitor_location
from backend.app.core.database import get_db_session
from backend.app.models.article import ArticleLikeRecord
from backend.app.schemas.article import (
    ArticleCreate,
    ArticleLikeResponse,
    ArticleListResponse,
    ArticleResponse,
    ArticleUpdate,
)
from backend.app.schemas.media import MediaCleanupResponse, MediaListResponse
from backend.app.services.articles import (
    create_article,
    delete_article,
    get_article,
    get_article_list_response,
    get_public_article,
    like_article,
    update_article,
)
from backend.app.services.about_profile import (
    get_about_profile,
    serialize_about_profile,
    update_about_profile,
)
from backend.app.services.auth import (
    authenticate_admin,
    create_admin_session,
    delete_admin_session,
    require_admin_session,
)
from backend.app.services.media import cleanup_unreferenced_media_files, list_media_files

router = APIRouter()

MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_RESUME_SIZE = 20 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
ALLOWED_RESUME_TYPES = {
    "application/pdf": ".pdf",
}


class ImageUploadResult(BaseModel):
    url: str
    filename: str
    content_type: str
    size: int


class FileUploadResult(ImageUploadResult):
    original_filename: str


@router.get("/health", tags=["system"], response_model=ApiResponse[dict[str, str]])
def health_check(request: Request) -> ApiResponse[dict[str, str]]:
    return build_success_response(
        request,
        {"status": "ok", "service": "personal-blog-api"},
    )


@router.post("/auth/login", tags=["auth"], response_model=ApiResponse[AdminSessionResponse])
def login_admin(
    request: Request,
    response: Response,
    payload: AdminLoginRequest,
) -> ApiResponse[AdminSessionResponse]:
    authenticate_admin(payload.username, payload.password)
    return build_success_response(
        request,
        create_admin_session(response, payload.username),
        message="登录成功",
    )


@router.get("/auth/me", tags=["auth"], response_model=ApiResponse[AdminSessionResponse])
def read_current_admin(
    request: Request,
    admin_session: AdminSessionResponse = Depends(require_admin_session),
) -> ApiResponse[AdminSessionResponse]:
    return build_success_response(request, admin_session)


@router.post("/auth/logout", tags=["auth"], response_model=ApiResponse[dict[str, bool]])
def logout_admin(
    request: Request,
    response: Response,
    _admin_session: AdminSessionResponse = Depends(require_admin_session),
) -> ApiResponse[dict[str, bool]]:
    delete_admin_session(request, response)
    return build_success_response(request, {"logged_out": True}, message="已退出登录")


def get_client_ip(request: Request) -> str:
    client_ip = request.client.host if request.client else "unknown"
    if client_ip not in settings.trusted_proxy_ip_list:
        return client_ip

    forwarded_for = request.headers.get("X-Forwarded-For")
    if not forwarded_for:
        return client_ip

    return forwarded_for.split(",", maxsplit=1)[0].strip()


def get_article_visitor_hash(request: Request, response: Response) -> str:
    visitor_id = request.cookies.get("article_visitor_id")
    if visitor_id is None or len(visitor_id) != 32:
        visitor_id = uuid4().hex
        response.set_cookie(
            key="article_visitor_id",
            value=visitor_id,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            samesite="lax",
        )
    identity = f"{settings.article_visitor_identity_secret}:{visitor_id}"
    return sha256(identity.encode("utf-8")).hexdigest()


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
    request: Request,
    payload: SiteSettingsUpdate,
    _admin_session: AdminSessionResponse = Depends(require_admin_session),
) -> ApiResponse[SiteSettings]:
    return build_success_response(request, update_site_settings(payload))


@router.get("/about-profile", tags=["about"], response_model=ApiResponse[AboutProfileResponse])
def read_about_profile(
    request: Request,
    session: Session = Depends(get_db_session),
) -> ApiResponse[AboutProfileResponse]:
    return build_success_response(request, serialize_about_profile(get_about_profile(session)))


@router.put("/about-profile", tags=["about"], response_model=ApiResponse[AboutProfileResponse])
def write_about_profile(
    request: Request,
    payload: AboutProfileUpdate,
    _admin_session: AdminSessionResponse = Depends(require_admin_session),
    session: Session = Depends(get_db_session),
) -> ApiResponse[AboutProfileResponse]:
    profile = update_about_profile(session, payload)
    return build_success_response(request, serialize_about_profile(profile), message="关于我资料已保存")


@router.get("/media/resumes/{filename}", tags=["media"])
def download_resume(
    filename: str,
    session: Session = Depends(get_db_session),
) -> FileResponse:
    if Path(filename).name != filename:
        raise HTTPException(status_code=404, detail="简历不存在")

    profile = get_about_profile(session)
    expected_suffix = f"/uploads/resumes/{filename}"
    if not profile.resume_url or not profile.resume_url.endswith(expected_suffix):
        raise HTTPException(status_code=404, detail="简历不存在")

    resume_path = settings.upload_path / "resumes" / filename
    if not resume_path.is_file():
        raise HTTPException(status_code=404, detail="简历不存在")

    return FileResponse(
        resume_path,
        media_type="application/pdf",
        filename=profile.resume_filename or "resume.pdf",
    )


@router.get("/media/files", tags=["media"], response_model=ApiResponse[MediaListResponse])
def read_media_files(
    request: Request,
    _admin_session: AdminSessionResponse = Depends(require_admin_session),
    session: Session = Depends(get_db_session),
) -> ApiResponse[MediaListResponse]:
    return build_success_response(request, list_media_files(session))


@router.delete(
    "/media/files/unreferenced",
    tags=["media"],
    response_model=ApiResponse[MediaCleanupResponse],
)
def delete_unreferenced_media_files(
    request: Request,
    _admin_session: AdminSessionResponse = Depends(require_admin_session),
    session: Session = Depends(get_db_session),
) -> ApiResponse[MediaCleanupResponse]:
    cleanup_result = cleanup_unreferenced_media_files(session)
    return build_success_response(request, cleanup_result, message="未引用文件已清理")


@router.get("/articles", tags=["articles"], response_model=ApiResponse[ArticleListResponse])
def read_public_articles(
    request: Request,
    response: Response,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    category: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    session: Session = Depends(get_db_session),
) -> ApiResponse[ArticleListResponse]:
    article_list, cache_status = get_article_list_response(
        session,
        public_only=True,
        page=page,
        page_size=page_size,
        category=category,
        tag=tag,
        search=search,
    )
    response.headers["X-Cache-Status"] = cache_status
    return build_success_response(
        request,
        article_list,
    )


@router.get("/articles/manage", tags=["articles"], response_model=ApiResponse[ArticleListResponse])
def read_manage_articles(
    request: Request,
    response: Response,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    _admin_session: AdminSessionResponse = Depends(require_admin_session),
    session: Session = Depends(get_db_session),
) -> ApiResponse[ArticleListResponse]:
    article_list, cache_status = get_article_list_response(
        session,
        public_only=False,
        page=page,
        page_size=page_size,
        category=category,
        tag=tag,
        search=search,
    )
    response.headers["X-Cache-Status"] = cache_status
    return build_success_response(
        request,
        article_list,
    )


@router.get("/articles/{slug}", tags=["articles"], response_model=ApiResponse[ArticleResponse])
def read_public_article(
    request: Request,
    response: Response,
    slug: str,
    session: Session = Depends(get_db_session),
) -> ApiResponse[ArticleResponse]:
    visitor_hash = get_article_visitor_hash(request, response)
    article = get_public_article(session, slug)
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    liked_by_current_visitor = session.scalar(
        select(ArticleLikeRecord.id).where(
            ArticleLikeRecord.article_id == article.id,
            ArticleLikeRecord.visitor_hash == visitor_hash,
        )
    ) is not None
    response_data = ArticleResponse.model_validate(article).model_copy(
        update={"liked_by_current_visitor": liked_by_current_visitor}
    )
    return build_success_response(request, response_data)


@router.post("/articles/{slug}/like", tags=["articles"], response_model=ApiResponse[ArticleLikeResponse])
def like_public_article(
    request: Request,
    response: Response,
    slug: str,
    session: Session = Depends(get_db_session),
) -> ApiResponse[ArticleLikeResponse]:
    visitor_hash = get_article_visitor_hash(request, response)
    article, liked_by_current_visitor = like_article(session, slug, visitor_hash)
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    return build_success_response(
        request,
        ArticleLikeResponse(likes=article.likes, liked_by_current_visitor=liked_by_current_visitor),
        message="点赞成功" if liked_by_current_visitor else "点赞状态异常",
    )


@router.post("/articles", tags=["articles"], response_model=ApiResponse[ArticleResponse])
def create_manage_article(
    request: Request,
    payload: ArticleCreate,
    _admin_session: AdminSessionResponse = Depends(require_admin_session),
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
    _admin_session: AdminSessionResponse = Depends(require_admin_session),
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
    _admin_session: AdminSessionResponse = Depends(require_admin_session),
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
    _admin_session: AdminSessionResponse = Depends(require_admin_session),
    file: UploadFile = File(...),
) -> ApiResponse[ImageUploadResult]:
    extension = ALLOWED_IMAGE_TYPES.get(file.content_type or "")
    if extension is None:
        raise HTTPException(status_code=415, detail="仅支持 JPG、PNG、WEBP 或 GIF 图片")

    upload_dir = settings.upload_path
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


@router.post(
    "/media/resumes",
    tags=["media"],
    response_model=ApiResponse[FileUploadResult],
)
async def upload_resume(
    request: Request,
    _admin_session: AdminSessionResponse = Depends(require_admin_session),
    file: UploadFile = File(...),
) -> ApiResponse[FileUploadResult]:
    filename_lower = (file.filename or "").lower()
    extension = ALLOWED_RESUME_TYPES.get(file.content_type or "")
    if extension is None and filename_lower.endswith(".pdf"):
        extension = ".pdf"
    if extension is None:
        raise HTTPException(status_code=415, detail="仅支持 PDF 简历")

    upload_dir = settings.upload_path / "resumes"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    destination = upload_dir / filename
    size = 0

    try:
        with destination.open("wb") as target:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_RESUME_SIZE:
                    destination.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="简历大小不能超过 20 MB")
                target.write(chunk)
    finally:
        await file.close()

    result = FileUploadResult(
        url=f"{settings.public_base_url.rstrip('/')}/uploads/resumes/{filename}",
        filename=filename,
        original_filename=file.filename or "resume.pdf",
        content_type="application/pdf",
        size=size,
    )
    return build_success_response(request, result, message="简历上传成功")
