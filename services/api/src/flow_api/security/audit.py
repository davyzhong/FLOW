"""S01 §6 + §7.1 + §8.1 审计协议：AuditContext / ModelBoundary + AuditWriter Protocol。

Bootstrap 阶段不实现 ORM（Task 2A 后半段 / 0026 迁移），
只冻结：
- `AuditContext` 字段（用于决策审计 + 业务 outcome 审计）
- `ModelBoundary` 字段（§7.1）
- `AuditWriter` Protocol（接口签名 + 不可变约束 + 独立 Session 语义）

不允许新增字段、不得放宽类型、不得跳过审计；不写代码约定。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from flow_api.security.authorization import Action, Decision
from flow_api.security.principal import Role


@dataclass(frozen=True)
class ModelBoundary:
    """§7.1 冻结字段：不含 prompt/output 原文。"""

    provider: str
    model: str
    purpose: str
    input_artifact_ids: tuple[str, ...]
    input_sha256: tuple[str, ...]
    output_artifact_ids: tuple[str, ...]
    output_sha256: tuple[str, ...]


@dataclass(frozen=True)
class AuditContext:
    """§6 决策审计与 §7 发布 intent 审计共用的不可变上下文。

    `actor_id` / `actor_role` / `enterprise_id` 只复制自 Principal；
    认证拒绝（401）事件三者必须为 None（§6 step 2）。
    `correlation_id` 从 request.state 读取（§9），保证五处一致。
    `resource_scope` 来自 ResourceRef（public/enterprise）；认证拒绝用 "public"。
    `identity_field_present`：§3.3 body 身份字段存在（即使值相同）只记标记，
    值本身不进审计。
    """

    actor_id: str | None
    role: Role | None
    enterprise_id: UUID | None
    correlation_id: str
    action: Action | None
    resource_scope: str
    resource_type: str
    resource_id: str
    model_boundary: ModelBoundary | None
    identity_field_present: bool = False


class AuditWriter(Protocol):
    """§6 独立 durable 审计 writer 接口（Protocol）。

    实现侧必须：
    - 用新建 Session 开启独立短事务，commit/rollback 不复用业务 Session（§6 step 4）；
    - 不得修改既有 AuditEvent（§8.1 不可变 + trigger）；
    - 失败返回 `AuditUnavailable`，不得"尽力"保存原文（§8.3）。
    """

    def write_decision(
        self,
        *,
        audit_context: AuditContext,
        decision: Decision,
        request_id: str,
    ) -> None:
        ...

    def write_intent(
        self,
        *,
        audit_context: AuditContext,
        intent_event_id: UUID,
    ) -> None:
        ...

    def write_outcome(
        self,
        *,
        audit_context: AuditContext,
        intent_event_id: UUID,
        outcome: Decision,
        error_code: str | None,
    ) -> None:
        ...


# ---------------------------------------------------------------------------
# §6 全局 AuditWriter 注册点（durable 实现由应用启动时注册；默认 fail closed）
# ---------------------------------------------------------------------------


class AuditUnavailable(RuntimeError):
    """audit writer 未注册或持久化失败 → 503 audit_unavailable（§6 step 5）。"""


class _UnwiredAuditWriter:
    """durable writer 注册前的默认：fail closed，不静默放行。"""

    def write_decision(self, **kwargs: Any) -> None:
        raise AuditUnavailable("durable AuditWriter 未注册")

    def write_intent(self, **kwargs: Any) -> None:
        raise AuditUnavailable("durable AuditWriter 未注册")

    def write_outcome(self, **kwargs: Any) -> None:
        raise AuditUnavailable("durable AuditWriter 未注册")


_audit_writer: AuditWriter = _UnwiredAuditWriter()


def register_audit_writer(writer: AuditWriter) -> None:
    """应用启动时注册 durable writer（单点替换，路由不感知）。"""

    global _audit_writer
    _audit_writer = writer


def get_audit_writer() -> AuditWriter:
    """FastAPI Depends 注入点；测试经 dependency_overrides 替换。"""

    return _audit_writer
