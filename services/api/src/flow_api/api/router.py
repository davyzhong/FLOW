from fastapi import APIRouter, Depends

from flow_api.api.auth import require_bearer_auth
from flow_api.api.routes.copilot import router as copilot_router
from flow_api.api.routes.dashboard import router as dashboard_router
from flow_api.api.routes.health import router as health_router
from flow_api.api.routes.intake import router as intake_router
from flow_api.api.routes.investigations import router as investigations_router
from flow_api.api.routes.publishing import router as publishing_router
from flow_api.api.routes.workspace import router as workspace_router

api_router = APIRouter(prefix="/api/v1")

# 认证边界：配置 auth_token 后除 health 外全部强制 Bearer 认证（dev 模式开放）。
api_router.include_router(health_router)
api_router.include_router(workspace_router, dependencies=[Depends(require_bearer_auth)])
api_router.include_router(intake_router, dependencies=[Depends(require_bearer_auth)])
api_router.include_router(dashboard_router, dependencies=[Depends(require_bearer_auth)])
api_router.include_router(investigations_router, dependencies=[Depends(require_bearer_auth)])
api_router.include_router(copilot_router, dependencies=[Depends(require_bearer_auth)])
api_router.include_router(publishing_router, dependencies=[Depends(require_bearer_auth)])
