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
    # §3.1 identity JSON：每项必须含 token_sha256/actor_id/role/enterprise_id/is_service_account；
    # 留空（非 development）= 启动失败。development 仅当显式配置 dev_actor_id 时启用。
    flow_identity_bindings_json: str | None = None
    flow_dev_actor_id: str | None = None
    # §3.2 旧 Bearer 截止（默认规格 §3.2 2026-10-31T15:59:59Z）
    flow_legacy_bearer_cutoff: str = "2026-10-31T15:59:59+00:00"
    # §3.2 legacy 身份冻结：AUTH_TOKEN 配置时必须同时配置，DB 须有完全匹配的
    # active service_account RoleBinding
    flow_legacy_actor_id: str | None = None
    flow_legacy_enterprise_id: str | None = None
    # §8.2 audit retention days，默认 365，365 <= value <= 36500
    flow_audit_retention_days: int = 365


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
