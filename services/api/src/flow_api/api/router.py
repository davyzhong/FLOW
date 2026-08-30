from fastapi import APIRouter

from flow_api.api.routes.health import router as health_router
from flow_api.api.routes.workspace import router as workspace_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(workspace_router)
