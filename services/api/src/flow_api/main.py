import logging
import sys
import time
from collections.abc import Awaitable, Callable
from datetime import datetime
from uuid import uuid4

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from flow_api.api.router import api_router
from flow_api.api.schemas.intake import ErrorDetail
from flow_api.infrastructure.db import get_session_factory
from flow_api.infrastructure.logging import (
    bind_log_context,
    configure_logging,
    log_event,
)
from flow_api.security.audit import register_audit_writer
from flow_api.security.audit_writer import DurableAuditWriter
from flow_api.settings import get_settings

configure_logging()
logger = logging.getLogger("flow.api")


def _validate_security_startup() -> None:
    """S01 §3.1 / §3.2 / §8.2 启动 fail-fast 校验。

    校验项：
    - 旧 Bearer 截止时间可解析且未过期（过期则配置无效，启动失败）
    - identity bindings JSON 可解析且 token_sha256 不重复（生产环境必须）
    - audit retention days 在 [365, 36500] 范围内

    development 模式：identity bindings 留空时仅允许 flow_dev_actor_id 单点回退。
    """
    settings = get_settings()
    # §3.2 旧 Bearer 截止：仅当 legacy 凭据真实配置（AUTH_TOKEN）时到期才拒绝启动；
    # 未配置 AUTH_TOKEN 的环境（dev principal 模式）不使用 legacy token，
    # 到期只影响运行期 401，不阻断启动（§3.2「配置了 FLOW_AUTH_TOKEN 则启动失败」）。
    try:
        cutoff = datetime.fromisoformat(settings.flow_legacy_bearer_cutoff)
    except ValueError as error:
        print(
            f"[security] FATAL: flow_legacy_bearer_cutoff 不可解析: {error}",
            file=sys.stderr,
        )
        raise SystemExit(2) from error
    now = datetime.now(tz=cutoff.tzinfo)
    if now > cutoff:
        if settings.auth_token:
            print(
                f"[security] FATAL: 旧 Bearer 截止 {cutoff.isoformat()} 已过"
                "且 AUTH_TOKEN 仍配置（§3.2 启动 fail-fast）",
                file=sys.stderr,
            )
            raise SystemExit(2)
        print(
            f"[security] WARN: 旧 Bearer 截止 {cutoff.isoformat()} 已过"
            "（未配置 AUTH_TOKEN，legacy 路径已不可用）",
            file=sys.stderr,
        )
    # §3.2 legacy 身份冻结：AUTH_TOKEN 配置时 FLOW_LEGACY_ACTOR_ID/ENTERPRISE_ID 必填
    if settings.auth_token and (
        not settings.flow_legacy_actor_id or not settings.flow_legacy_enterprise_id
    ):
        print(
            "[security] FATAL: AUTH_TOKEN 已配置但缺少 FLOW_LEGACY_ACTOR_ID/"
            "FLOW_LEGACY_ENTERPRISE_ID（§3.2 冻结身份）",
            file=sys.stderr,
        )
        raise SystemExit(2)
    # §3.1 identity bindings（生产环境必须）
    if settings.flow_env != "development":
        if not settings.flow_identity_bindings_json:
            print(
                "[security] FATAL: flow_identity_bindings_json 未配置（非 development 环境必须）",
                file=sys.stderr,
            )
            raise SystemExit(2)
        try:
            from flow_api.api.auth import _load_identity_bindings

            _load_identity_bindings(_SettingsLikeProxy(settings))  # type: ignore[arg-type]
        except Exception as error:
            print(
                f"[security] FATAL: flow_identity_bindings_json 解析失败: {error}",
                file=sys.stderr,
            )
            raise SystemExit(2) from error
    # §8.2 retention range
    if not (365 <= settings.flow_audit_retention_days <= 36500):
        print(
            f"[security] FATAL: flow_audit_retention_days={settings.flow_audit_retention_days} "
            "不在 [365, 36500] 范围（§8.2）",
            file=sys.stderr,
        )
        raise SystemExit(2)


class _SettingsLikeProxy:
    """最小代理，仅暴露 _load_identity_bindings 需要的字段。"""

    def __init__(self, settings: object) -> None:
        self._settings = settings

    @property
    def auth_token(self) -> str | None:
        return getattr(self._settings, "auth_token", None)

    @property
    def flow_env(self) -> str:
        return getattr(self._settings, "flow_env", "production")

    @property
    def flow_identity_bindings_json(self) -> str | None:
        return getattr(self._settings, "flow_identity_bindings_json", None)

    @property
    def flow_dev_actor_id(self) -> str | None:
        return getattr(self._settings, "flow_dev_actor_id", None)

    @property
    def flow_legacy_bearer_cutoff(self) -> str:
        return getattr(
            self._settings, "flow_legacy_bearer_cutoff", "2026-10-31T15:59:59+00:00"
        )


def create_app() -> FastAPI:
    _validate_security_startup()
    # §6：durable AuditWriter 单点注册（审计写入失败 → 503 fail closed）
    from flow_api.settings import get_settings

    settings = get_settings()
    register_audit_writer(
        DurableAuditWriter(get_session_factory(), settings.flow_audit_retention_days)
    )
    app = FastAPI(title="FLOW API", version="0.1.0")

    @app.middleware("http")
    async def structured_request_logging(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid4())
        # §9 correlation：外部传入则透传（五处一致），否则生成
        correlation_id = request.headers.get("X-Correlation-Id") or str(uuid4())
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        started = time.perf_counter()
        bind_log_context(request_id=request_id, correlation_id=correlation_id)
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Correlation-Id"] = correlation_id
        log_event(
            logger,
            logging.INFO,
            "request.completed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(
        _request: object, error: RequestValidationError
    ) -> JSONResponse:
        payload = ErrorDetail(
            code="request_validation_failed",
            message="请求参数校验失败",
            details={"errors": error.errors()},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": payload.model_dump(mode="json")},
        )

    app.include_router(api_router)
    return app


app = create_app()
