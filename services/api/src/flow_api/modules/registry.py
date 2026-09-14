"""S01 Task 7：模块 registry——产品可见模块的唯一清单（设计 §5.4 合同 fixture）。

shared_core 是内部架构 owner（composition root 单独登记），不出现在产品可见列表。
"""

from __future__ import annotations

from typing import Any, Literal

ModuleLayer = Literal["product", "governance"]
ModuleStatus = Literal["implemented", "designed"]


class ModuleDescriptor(dict[str, Any]):
    """模块描述（dict 子类保持 JSON 序列化行为与设计 fixture 同构）。"""


MODULES: list[dict[str, Any]] = [
    {
        "id": "public_analysis",
        "name": "公开财报分析",
        "layer": "product",
        "status": "implemented",
    },
    {
        "id": "internal_workbench",
        "name": "企业内部分析工作台",
        "layer": "product",
        "status": "designed",
    },
    {
        "id": "professional_governance",
        "name": "专业治理底座",
        "layer": "governance",
        "status": "designed",
    },
]

MODULE_IDS: frozenset[str] = frozenset(m["id"] for m in MODULES)
