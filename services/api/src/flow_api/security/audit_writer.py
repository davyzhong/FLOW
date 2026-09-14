"""S01 §6/§8 durable AuditWriter 实现：独立短事务写 AuditEvent。

- 每次写入新建 Session（不复用业务 Session，§6 step 4）；commit 失败或不确定
  一律抛 AuditUnavailable → 上层 503 fail closed；
- 401/403/allow 共用同一写入路径；认证拒绝事件 actor/role/enterprise 全 NULL；
- retention：`retention_class="security_default"`、
  `retain_until = created_at + FLOW_AUDIT_RETENTION_DAYS`（§8.2）；
- trigger（0026）拒绝 UPDATE/DELETE；本实现只 INSERT；
- `mark_archive_eligible`（§8.2）：到期扫描只追加 marker 事件，不改既有行。
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from flow_api.security.audit import AuditContext, AuditUnavailable
from flow_api.security.models import AuditEvent

_EVENT_TYPE_DECISION = "authz.decision"
_EVENT_TYPE_INTENT = "publication.intent"
_EVENT_TYPE_OUTCOME = "publication.outcome"
_EVENT_TYPE_ARCHIVE_MARK = "audit.archive_eligibility_marked"


class DurableAuditWriter:
    """§6 AuditWriter Protocol 的 durable 实现。

    `session_factory` 每次调用返回新 Session；`retention_days` 来自
    `FLOW_AUDIT_RETENTION_DAYS`（启动校验 365..36500）。
    """

    def __init__(self, session_factory: Any, retention_days: int) -> None:
        self._factory = session_factory
        self._retention_days = retention_days

    # -- 内部 ---------------------------------------------------------------

    def _persist(self, event: AuditEvent) -> None:
        try:
            session: Session = self._factory()
        except Exception as error:  # noqa: BLE001 - 连接失败=审计不可用
            raise AuditUnavailable(f"audit session 不可用: {error}") from error
        try:
            session.add(event)
            session.commit()
        except Exception as error:  # noqa: BLE001 - commit 失败/不确定 → fail closed
            session.rollback()
            raise AuditUnavailable(f"audit commit 失败: {error}") from error
        finally:
            session.close()

    def _base_event(
        self,
        audit_context: AuditContext,
        decision: str,
        reason_code: str,
        request_id: str,
        *,
        event_type: str,
        resource_id: str | None = None,
        redacted_metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        created = datetime.now(tz=UTC)
        return AuditEvent(
            event_type=event_type,
            actor_id=audit_context.actor_id,
            actor_role=audit_context.role.value if audit_context.role else None,
            enterprise_id=audit_context.enterprise_id,
            resource_scope=audit_context.resource_scope,
            resource_type=audit_context.resource_type,
            resource_id=resource_id or audit_context.resource_id,
            action=audit_context.action.value if audit_context.action else None,
            decision=decision,
            reason_code=reason_code,
            correlation_id=audit_context.correlation_id or "-",
            request_id=request_id or "-",
            model_boundary=None,
            artifact_refs=[],
            redacted_metadata=redacted_metadata
            or (
                {"identity_field_present": True}
                if audit_context.identity_field_present
                else {}
            ),
            created_at=created,
            retention_class="security_default",
            retain_until=created + timedelta(days=self._retention_days),
        )

    # -- §6 AuditWriter Protocol -------------------------------------------

    def write_decision(
        self,
        *,
        audit_context: AuditContext,
        decision: Any,
        request_id: str,
    ) -> None:
        self._persist(
            self._base_event(
                audit_context,
                "allow" if decision.allowed else "deny",
                decision.reason_code.value
                if hasattr(decision.reason_code, "value")
                else str(decision.reason_code),
                request_id,
                event_type=_EVENT_TYPE_DECISION,
            )
        )

    def write_intent(
        self,
        *,
        audit_context: AuditContext,
        intent_event_id: UUID,
    ) -> None:
        self._persist(
            self._base_event(
                audit_context,
                "allow",
                "allow",
                "-",
                event_type=_EVENT_TYPE_INTENT,
                resource_id=str(intent_event_id),
            )
        )

    def write_outcome(
        self,
        *,
        audit_context: AuditContext,
        intent_event_id: UUID,
        outcome: Any,
        error_code: str | None,
    ) -> None:
        allowed = getattr(outcome, "allowed", True)
        self._persist(
            self._base_event(
                audit_context,
                "allow" if allowed else "error",
                error_code or "allow",
                "-",
                event_type=_EVENT_TYPE_OUTCOME,
                resource_id=str(intent_event_id),
            )
        )

    # -- §8.2 到期扫描（只追加 marker，不删不改） ----------------------------

    def mark_archive_eligible(
        self,
        target_event_id: UUID,
        target_retain_until: datetime,
        policy_days: int,
        *,
        trusted_now: datetime | None = None,
    ) -> bool:
        """三项机器谓词全满足才写 marker（§8.2）：

        1. `retain_until <= trusted_now`；
        2. 尚无既有 eligibility marker；
        3. 按 `(created_at, id)` 排序后不存在未被更晚 legal_hold_released
           配对解除的 legal_hold_placed。

        S01 无物理归档/删除；marker 只表明「可被未来归档规格选择」。
        """
        now = trusted_now or datetime.now(tz=UTC)
        if target_retain_until > now:
            return False
        try:
            session: Session = self._factory()
            try:
                target_id = str(target_event_id)
                events = (
                    session.query(AuditEvent)
                    .filter(AuditEvent.resource_id == target_id)
                    .order_by(AuditEvent.created_at, AuditEvent.id)
                    .all()
                )
                markers = [
                    e
                    for e in events
                    if e.event_type == _EVENT_TYPE_ARCHIVE_MARK
                    and e.resource_type == "audit_event"
                ]
                if markers:
                    return False
                # legal hold 配对：未解除的 placed 阻止 marker
                outstanding = 0
                for e in events:
                    if e.event_type == "audit.legal_hold_placed":
                        outstanding += 1
                    elif e.event_type == "audit.legal_hold_released" and outstanding:
                        outstanding -= 1
                if outstanding:
                    return False
                session.add(
                    AuditEvent(
                        event_type=_EVENT_TYPE_ARCHIVE_MARK,
                        actor_id=None,
                        actor_role=None,
                        enterprise_id=None,
                        resource_scope="public",
                        resource_type="audit_event",
                        resource_id=target_id,
                        action=None,
                        decision="allow",
                        reason_code="archive_eligible",
                        correlation_id="-",
                        request_id="-",
                        model_boundary=None,
                        artifact_refs=[],
                        redacted_metadata={
                            "target_retain_until": target_retain_until.isoformat(),
                            "policy_days": policy_days,
                        },
                        created_at=now,
                        retention_class="security_default",
                        retain_until=now + timedelta(days=self._retention_days),
                    )
                )
                session.commit()
                return True
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        except Exception as error:  # noqa: BLE001 - 写 marker 失败不阻塞业务
            raise AuditUnavailable(f"archive marker 写入失败: {error}") from error


__all__ = ["DurableAuditWriter"]
