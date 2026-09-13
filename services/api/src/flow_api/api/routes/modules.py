"""S01 Task 7：只读 /api/v1/modules——产品可见模块清单（设计 §5.4 合同）。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from flow_api.modules.registry import MODULES

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("")
def list_modules() -> dict[str, Any]:
    """返回产品可见模块清单；shared_core 为内部架构 owner，不在列表中。"""
    return {"modules": MODULES}
