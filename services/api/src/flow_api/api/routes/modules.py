"""S01 Task 7：只读 /api/v1/modules——产品可见模块清单（设计 §5.4 合同）。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from flow_api.modules.registry import MODULES
from flow_api.security.authorization import Action
from flow_api.security.route_policy import LOADERS, require_action

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get(
    "",
    dependencies=[
        Depends(
            require_action(Action.WORKSPACE_METADATA_READ, LOADERS["load_public_module_catalog"])
        )
    ],
)
def list_modules() -> dict[str, Any]:
    """返回产品可见模块清单；shared_core 为内部架构 owner，不在列表中。"""
    return {"modules": MODULES}
