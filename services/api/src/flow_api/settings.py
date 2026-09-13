from datetime import date
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    flow_env: str = "development"
    flow_timezone: str = "Asia/Shanghai"
    database_url: str
    redis_url: str
    s3_endpoint_url: str
    s3_bucket: str
    s3_access_key: SecretStr
    s3_secret_key: SecretStr
    intake_max_upload_bytes: int = 25 * 1024 * 1024
    statement_max_upload_bytes: int = 80 * 1024 * 1024
    s3_use_system_proxy: bool = False
    auth_token: str | None = None  # 配置后启用 Bearer 认证边界；留空 = 开发模式
    # S01 Task 2B：登记主体凭据（env PRINCIPAL_TOKENS，JSON：
    # {"<token>": {"actor_id": "...", "role": "analyst", "enterprise_id": "<uuid>|null"}}）
    principal_tokens: dict[str, dict[str, str | None]] = {}
    # 旧 auth_token 兼容期截止日（env LEGACY_BEARER_UNTIL，ISO 日期）；过期后旧凭据 401
    legacy_bearer_until: date | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
