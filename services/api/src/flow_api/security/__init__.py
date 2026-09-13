"""S01 Task 2A Bootstrap：安全领域核心包。

本包提供 S01 §2 冻结的类型与 §4 纯 `authorize` 函数、§6 审计 writer 协议。
ORM（RoleBinding、AuditEvent）和 0026 迁移、HTTP route 接线属于 Task 2A 后半段 / Task 2B。
"""
from __future__ import annotations

from flow_api.security.audit import AuditContext, AuditWriter, ModelBoundary
from flow_api.security.authorization import (
    Action,
    Decision,
    ReasonCode,
    ResourceRef,
    authorize,
)
from flow_api.security.principal import (
    LEGACY_BEARER_CUTOFF_UTC,
    Principal,
    ResourceScope,
    Role,
)

__all__ = [
    "Action",
    "AuditContext",
    "AuditWriter",
    "Decision",
    "LEGACY_BEARER_CUTOFF_UTC",
    "ModelBoundary",
    "Principal",
    "ReasonCode",
    "ResourceRef",
    "ResourceScope",
    "Role",
    "authorize",
]
