from fastapi import APIRouter, Depends

from flow_api.api.schemas.workspace import WorkspaceResponse
from flow_api.security.authorization import Action
from flow_api.security.route_policy import LOADERS, require_action
from flow_api.settings import get_settings

router = APIRouter(tags=["workspace"])


@router.get(
    "/workspace",
    response_model=WorkspaceResponse,
    dependencies=[
        Depends(
            require_action(
                Action.WORKSPACE_METADATA_READ, LOADERS["load_public_workspace_metadata"]
            )
        )
    ],
)
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
