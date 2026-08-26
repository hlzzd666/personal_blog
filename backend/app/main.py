from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .api.router import router
from .core.config import settings
from .core.database import get_db_session
from .core.exceptions import register_exception_handlers
from .core.response import build_success_response
from .services.distribution import (
    article_metadata_shell,
    build_robots,
    build_rss,
    build_sitemap,
    generic_metadata_shell,
    note_metadata_shell,
    series_metadata_shell,
)

app = FastAPI(title=settings.app_name, version="0.1.0", debug=settings.debug)

settings.upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_path), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_v1_prefix)
register_exception_handlers(app)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or uuid4().hex
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


@app.get("/", tags=["system"])
def root(request: Request):
    return build_success_response(request, {"message": "Personal Blog API"})


@app.get("/robots.txt", include_in_schema=False)
def robots() -> Response:
    return Response(build_robots(), media_type="text/plain; charset=utf-8")


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap(session: Session = Depends(get_db_session)) -> Response:
    return Response(build_sitemap(session), media_type="application/xml; charset=utf-8")


@app.get("/api/feed.xml", include_in_schema=False)
@app.get("/feed.xml", include_in_schema=False)
def rss_feed(session: Session = Depends(get_db_session)) -> Response:
    return Response(build_rss(session), media_type="application/rss+xml; charset=utf-8")


@app.get("/web/articles/{slug}", include_in_schema=False)
def article_shell(slug: str, session: Session = Depends(get_db_session)) -> HTMLResponse:
    content, exists = article_metadata_shell(session, slug)
    return HTMLResponse(content, status_code=200 if exists else 404)


@app.get("/web/series/{slug}", include_in_schema=False)
def series_shell(slug: str, session: Session = Depends(get_db_session)) -> HTMLResponse:
    content, exists = series_metadata_shell(session, slug)
    return HTMLResponse(content, status_code=200 if exists else 404)


@app.get("/web/notes/{slug}", include_in_schema=False)
def note_shell(slug: str, session: Session = Depends(get_db_session)) -> HTMLResponse:
    content, exists = note_metadata_shell(session, slug)
    return HTMLResponse(content, status_code=200 if exists else 404)


if (settings.web_dist_path / "assets").is_dir():
    app.mount(
        "/web/assets",
        StaticFiles(directory=settings.web_dist_path / "assets"),
        name="web-assets",
    )


@app.get("/web/favicon.jpg", include_in_schema=False)
def web_favicon() -> FileResponse:
    return FileResponse(settings.web_dist_path / "favicon.jpg")


@app.get("/web/{path:path}", include_in_schema=False)
def web_shell(path: str) -> HTMLResponse:
    known_routes = {"", "articles", "series", "notes", "about", "privacy"}
    exists = path.strip("/") in known_routes
    title = "个人博客" if exists else "页面不存在"
    description = "个人博客文章、专题与短动态。" if exists else "没有找到这个页面。"
    return HTMLResponse(
        generic_metadata_shell(title, description, path),
        status_code=200 if exists else 404,
    )
