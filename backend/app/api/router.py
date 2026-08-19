from fastapi import APIRouter, Request

from backend.app.core.response import build_success_response
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.site_settings import SiteSettings, SiteSettingsUpdate
from backend.app.services.site_settings import get_site_settings, update_site_settings

router = APIRouter()


@router.get("/health", tags=["system"], response_model=ApiResponse[dict[str, str]])
def health_check(request: Request) -> ApiResponse[dict[str, str]]:
    return build_success_response(
        request,
        {"status": "ok", "service": "personal-blog-api"},
    )


@router.get("/site-settings", tags=["site"], response_model=ApiResponse[SiteSettings])
def read_site_settings(request: Request) -> ApiResponse[SiteSettings]:
    return build_success_response(request, get_site_settings())


@router.put("/site-settings", tags=["site"], response_model=ApiResponse[SiteSettings])
def write_site_settings(
    request: Request, payload: SiteSettingsUpdate
) -> ApiResponse[SiteSettings]:
    return build_success_response(request, update_site_settings(payload))
