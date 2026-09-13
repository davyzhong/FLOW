"""S01 §2 身份与资源类型：Role / Principal / ResourceScope。

构造时硬约束（§2.1、§3.1.4）：
- `role == SERVICE_ACCOUNT` 当且仅当 `is_service_account is True`；
- 人类/AI 角色必须 `is_service_account=False`；
- 所有角色（人/AI/服务账号）必须 `enterprise_id` 非空（service_account 也受 §3.1.4 约束）。
- `ResourceScope.PUBLIC` 资源必须 `enterprise_id=None`；
- `ResourceScope.ENTERPRISE` 资源必须 `enterprise_id` 非空。

旧 Bearer 截止（§3.2）：`2026-10-31T23:59:59+08:00`（= `2026-10-31T15:59:59Z`）。
解析端在 `flow_api.api.auth` 中实现并强制 fail-fast；本模块只冻结常量。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID


class Role(StrEnum):
    FINANCE_BP = "finance_bp"
    ANALYST = "analyst"
    RULE_OWNER = "rule_owner"
    AI_ANALYST = "ai_analyst"
    AI_CFO = "ai_cfo"
    SERVICE_ACCOUNT = "service_account"


# 所有角色在 §3.1.4 都有 enterprise_id；service_account 同样受约束。
_HUMAN_OR_AI_ROLES = frozenset(
    {Role.FINANCE_BP, Role.ANALYST, Role.RULE_OWNER, Role.AI_ANALYST, Role.AI_CFO}
)


ResourceScope = Literal["public", "enterprise"]


@dataclass(frozen=True)
class Principal:
    actor_id: str
    role: Role
    enterprise_id: UUID | None
    is_service_account: bool

    def __post_init__(self) -> None:
        if not self.actor_id or not isinstance(self.actor_id, str):
            raise ValueError("Principal.actor_id 必须是非空 str")
        if not isinstance(self.role, Role):
            raise ValueError("Principal.role 必须是 Role 枚举")
        # role == SERVICE_ACCOUNT ⇔ is_service_account is True
        if self.role is Role.SERVICE_ACCOUNT and not self.is_service_account:
            raise ValueError("role=SERVICE_ACCOUNT 必须 is_service_account=True")
        if self.role is not Role.SERVICE_ACCOUNT and self.is_service_account:
            raise ValueError("is_service_account=True 仅允许 role=SERVICE_ACCOUNT")
        # 人类/AI 角色必须 is_service_account=False（已由上面隐含），service flag 不得冒充 AI/人类
        if self.role in _HUMAN_OR_AI_ROLES and self.is_service_account:
            raise ValueError("人类/AI 角色必须 is_service_account=False")
        # §3.1.4 所有角色都必须有 enterprise_id
        if self.enterprise_id is None:
            raise ValueError("Principal.enterprise_id 必须非空（§3.1.4）")
        if not isinstance(self.enterprise_id, UUID):
            raise ValueError("Principal.enterprise_id 必须是 UUID")


@dataclass(frozen=True)
class ResourceRef:
    scope: ResourceScope
    resource_type: str
    resource_id: str
    enterprise_id: UUID | None
    owner_actor_id: str | None
    proposed_by_actor_id: str | None

    def __post_init__(self) -> None:
        if self.scope not in ("public", "enterprise"):
            raise ValueError("ResourceRef.scope 必须是 'public' 或 'enterprise'")
        if not self.resource_type or not isinstance(self.resource_type, str):
            raise ValueError("ResourceRef.resource_type 必须是非空 str")
        if not self.resource_id or not isinstance(self.resource_id, str):
            raise ValueError("ResourceRef.resource_id 必须是非空 str")
        if self.scope == "public":
            if self.enterprise_id is not None:
                raise ValueError("public 资源必须 enterprise_id=None（§4.1）")
        else:  # enterprise
            if self.enterprise_id is None:
                raise ValueError("enterprise 资源必须 enterprise_id 非空（§4.1）")
        # owner_actor_id / proposed_by_actor_id 只能是 None 或非空 str
        for name in ("owner_actor_id", "proposed_by_actor_id"):
            v = getattr(self, name)
            if v is not None and (not isinstance(v, str) or not v):
                raise ValueError(f"ResourceRef.{name} 必须是 None 或非空 str")


# §3.2 旧 Bearer 无条件截止
# 2026-10-31T23:59:59+08:00 = 2026-10-31T15:59:59Z
LEGACY_BEARER_CUTOFF_UTC: datetime = datetime(2026, 10, 31, 15, 59, 59, tzinfo=UTC)
