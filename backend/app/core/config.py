from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "Personal Blog API"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str
    sql_echo: bool = False
    cors_origins: str = ""
    trusted_proxy_ips: str = ""
    public_base_url: str = "http://127.0.0.1:8000"
    site_url: str = "http://127.0.0.1:5173"
    web_base_path: str = "/web"
    web_dist_dir: str = "web/dist"
    upload_dir: str = "backend/uploads"
    redis_url: str = "redis://127.0.0.1:6379/0"
    article_list_cache_ttl: int = 300
    article_visitor_identity_secret: str = "change-this-development-visitor-identity-secret"
    admin_username: str = "admin"
    admin_password_hash: str = ""
    admin_session_ttl_seconds: int = 60 * 60 * 8
    admin_session_cookie_name: str = "personal_blog_admin_session"
    admin_csrf_cookie_name: str = "personal_blog_admin_csrf"
    cookie_secure: bool = False

    model_config = SettingsConfigDict(env_file="backend/.env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def trusted_proxy_ip_list(self) -> list[str]:
        return [ip.strip() for ip in self.trusted_proxy_ips.split(",") if ip.strip()]

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir).expanduser()
        if path.is_absolute():
            return path
        return (PROJECT_ROOT / path).resolve()

    @property
    def web_dist_path(self) -> Path:
        path = Path(self.web_dist_dir).expanduser()
        if path.is_absolute():
            return path
        return (PROJECT_ROOT / path).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
