"""审计协议与事件输入模型（S01 安全 ABI；不含 ORM）。

规格：docs/40_specs/security/internal-workbench-rbac-audit-v1.md §3/§5。

本模块只定义写入协议与事件载荷；追加式持久化（0026 迁移 + 拒 UPDATE/DELETE
trigger）由后续车道实现 `AuditWriter` 协议接入，路由侧不感知存储细节。
敏感输入只记哈希/摘要，禁止明文进入事件。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class AuditEventInput:
    """一条待追加审计事件的完整输入；敏感输入必须先哈希化再进入本对象。"""

    event_type: str  # 如 authz.decision / data.upload / mapping.confirm / report.publish
    actor_id: str
    role: str
    enterprise_id: UUID | None
    action: str
    resource_kind: str
    resource_id: str | None
    decision: str  # allow / deny / outcome
    reason: str
    correlation_id: str
    model_boundary: str | None  # 模型/用途/输入边界/输出摘要（涉模型调用时）
    created_at: datetime


class AuditWriter(Protocol):
    """追加式审计写入协议；实现者保证只追加、不更新、不删除。"""

    def record(self, event: AuditEventInput) -> None: ...


class NullAuditWriter:
    """持久化落地前的占位 writer：丢弃事件但保留协议形状。"""

    def record(self, event: AuditEventInput) -> None:
        return None


def get_audit_writer() -> AuditWriter:
    """FastAPI 依赖注入点；0026 落地后替换为数据库 writer（集中替换，不改路由）。"""

    return NullAuditWriter()


__all__ = ["AuditEventInput", "AuditWriter", "NullAuditWriter", "get_audit_writer"]
