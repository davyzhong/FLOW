"""Principal：请求主体身份（S01 安全 ABI 最小实现）。

规格：docs/40_specs/security/internal-workbench-rbac-audit-v1.md §3。

身份只来自凭据解析（见 api/auth.py 的 resolve_principal），
请求体中的 actor/operator/reviewer 字段一律不得作为授权身份。
持久化角色绑定（0026 迁移）落地前，本模块的类型即后续车道的对接面。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    FINANCE_BP = "finance_bp"
    ANALYST = "analyst"  # 经分专员
    RULE_OWNER = "rule_owner"  # 财务规则负责人
    AI_ANALYST = "ai_analyst"
    AI_CFO = "ai_cfo"
    SERVICE_ACCOUNT = "service_account"
    DEVELOPMENT = "development"  # 仅本机开发模式


@dataclass(frozen=True)
class Principal:
    actor_id: str
    role: Role
    enterprise_id: UUID | None
    is_service_account: bool


__all__ = ["Principal", "Role"]
