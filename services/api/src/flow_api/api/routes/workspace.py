from fastapi import APIRouter

from flow_api.api.schemas.workspace import WorkspaceResponse
from flow_api.settings import get_settings

router = APIRouter(tags=["workspace"])


@router.get("/workspace", response_model=WorkspaceResponse)
def get_workspace() -> WorkspaceResponse:
    settings = get_settings()
    return WorkspaceResponse(
        workspace_id="flow-v1",
        name="FLOW",
        primary_role="finance_bp",
        industry="logistics_supply_chain",
        timezone=settings.flow_timezone,
        currency="CNY",
    )
