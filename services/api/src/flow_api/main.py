import logging
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from flow_api.api.router import api_router
from flow_api.api.schemas.intake import ErrorDetail
from flow_api.infrastructure.logging import (
    bind_log_context,
    configure_logging,
    log_event,
)
from flow_api.settings import get_settings

configure_logging()
logger = logging.getLogger("flow.api")


def _assert_auth_configured_for_env() -> None:
    """非开发环境必须配置认证凭据，否则启动即失败（S01 安全 fail-fast）。"""

    settings = get_settings()
    if (
        settings.flow_env != "development"
        and not settings.auth_token
        and not settings.principal_tokens
    ):
        raise RuntimeError(
            f"flow_env={settings.flow_env!r} 下必须配置 AUTH_TOKEN 或 PRINCIPAL_TOKENS；"
            "拒绝以无认证状态启动"
        )


def create_app() -> FastAPI:
    _assert_auth_configured_for_env()
    app = FastAPI(title="FLOW API", version="0.1.0")

    @app.middleware("http")
    async def structured_request_logging(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid4())
        started = time.perf_counter()
        bind_log_context(request_id=request_id)
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        response.headers["X-Request-Id"] = request_id
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
