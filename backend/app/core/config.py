from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(env_file="backend/.env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def trusted_proxy_ip_list(self) -> list[str]:
        return [ip.strip() for ip in self.trusted_proxy_ips.split(",") if ip.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
