from fastapi import APIRouter

from flow_api.api.routes.dashboard import router as dashboard_router
from flow_api.api.routes.health import router as health_router
from flow_api.api.routes.investigations import router as investigations_router
from flow_api.api.routes.intake import router as intake_router
from flow_api.api.routes.workspace import router as workspace_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(workspace_router)
api_router.include_router(intake_router)
api_router.include_router(dashboard_router)
api_router.include_router(investigations_router)
