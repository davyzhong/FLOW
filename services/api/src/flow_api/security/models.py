"""S01 §3.1 + §8.1 ORM：RoleBinding + AuditEvent。

字段约束（§3.1 / §8.1）：
- RoleBinding：id/actor_id/role/enterprise_id/is_service_account/active/created_at/revoked_at
  partial unique：每个 actor 最多一条 active
- AuditEvent：event_type/actor_id/actor_role/enterprise_id/resource_scope/resource_type/
  resource_id/action/decision/reason_code/correlation_id/request_id/model_boundary/
  artifact_refs/redacted_metadata/created_at/retention_class/retain_until
  数据库 trigger 拒 UPDATE/DELETE（migration 0026）

不变量由类型层 + CHECK + partial unique 共同保证；应用层只写，不修改既有事件。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from flow_api.infrastructure.models.base import Base


class RoleBinding(Base):
    __tablename__ = "role_binding"
    __table_args__ = (
        CheckConstraint(
            "role IN ('finance_bp','analyst','rule_owner','ai_analyst','ai_cfo','service_account')",
            name="ck_role_binding_role_enum",
        ),
        CheckConstraint(
            "active = true AND revoked_at IS NULL OR active = false AND revoked_at IS NOT NULL",
            name="ck_role_binding_active_revoke_consistency",
        ),
        Index("ix_role_binding_enterprise_id", "enterprise_id"),
        Index("ix_role_binding_role", "role"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    enterprise_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    is_service_account: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditEvent(Base):
    """§8.1 追加式审计事件。

    数据库 trigger（migration 0026）拒绝 UPDATE/DELETE；
    应用层也不得调用 .update() / session.delete()。
"""

    __tablename__ = "audit_event"
    __table_args__ = (
        CheckConstraint(
            "decision IN ('allow','deny','error')",
            name="ck_audit_event_decision_enum",
        ),
        CheckConstraint(
            "resource_scope IN ('public','enterprise')", name="ck_audit_event_resource_scope_enum"
        ),
        Index("ix_audit_event_actor_id", "actor_id"),
        Index("ix_audit_event_enterprise_id", "enterprise_id"),
        Index("ix_audit_event_correlation_id", "correlation_id"),
        Index("ix_audit_event_resource", "resource_type", "resource_id"),
        Index("ix_audit_event_retain_until", "retain_until"),
        Index("ix_audit_event_created_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    enterprise_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    resource_scope: Mapped[str] = mapped_column(String(16), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False)
    model_boundary: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    artifact_refs: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    redacted_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    retention_class: Mapped[str] = mapped_column(String(32), nullable=False)
    retain_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


__all__ = ["RoleBinding", "AuditEvent"]
