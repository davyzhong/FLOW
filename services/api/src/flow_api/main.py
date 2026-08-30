from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from flow_api.api.router import api_router
from flow_api.api.schemas.intake import ErrorDetail


def create_app() -> FastAPI:
    app = FastAPI(title="FLOW API", version="0.1.0")

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
