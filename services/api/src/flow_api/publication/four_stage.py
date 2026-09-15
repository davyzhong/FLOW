"""S01 §7.1–§7.5 四阶段发布 ABI：publishing 与 operations 的唯一共用实现。

固定四阶段（§7.3）：
  1. prepare_intent(session, request, audit_context)：验证冻结资源、幂等、
     每 format 写 PENDING attempt，追加 intent 审计事件，flush。不 render。
  2. caller commit：路由显式 commit 使 intent durable；失败 → 503 且 0 对象写。
  3. execute_object(prepared, renderers, object_store)：无 Session，逐 format
     render → sha/size/content-type → immutable 写；render/store 失败写失败
     ObjectOutcome 并继续其余 format（partial outcome 不丢）。
  4. finalize_success / finalize_failure(session, ...)：逐项 outcome flush；
     仅全成功置 published；路由再显式 commit。

Session 归属（§7.2）：prepare/finalize 只用路由传入的同一业务 Session，只
flush 不 commit/rollback；execute_object 无 Session、禁开连接；audit writer
独立短事务（§6）。

幂等与重试（§7.4）：identity = (resource_type, resource_id, sorted_formats,
idempotency_key)；同 key 同参数复用既有状态；同 key 异参数 409；已 succeeded
format 经 write_if_absent 校验内容后复用，只为未成功 format 追加 sequence
attempt。
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.domain.ids import new_uuid7
from flow_api.security.audit import AuditContext, ModelBoundary, get_audit_writer
from flow_api.security.redaction import redact_audit_text

__all__ = [
    "AuditContext",
    "FinalizedPublication",
    "ModelBoundary",
    "ObjectBatchOutcome",
    "ObjectOutcome",
    "ObjectPlan",
    "PreparedPublication",
    "PublicationAttemptStatus",
    "PublicationErrorCode",
    "PublicationFormat",
    "PublicationFailure",
    "PublicationFreezeConflict",
    "PublicationIdempotencyConflict",
    "PublicationIntegrityFailure",
    "PublicationIntentNotDurable",
    "PublicationNotFound",
    "PublicationObjectStore",
    "PublicationObjectStoreFailure",
    "PublicationOutcomeNotDurable",
    "PublicationRenderFailure",
    "PublicationScopeConflict",
    "RendererRegistry",
    "ResourceVerifier",
    "VerifiedResource",
    "canonical_source_sha256",
    "execute_object",
    "finalize_failure",
    "finalize_success",
    "prepare_intent",
    "register_resource_verifier",
]


# ---------------------------------------------------------------------------
# §7.1 类型
# ---------------------------------------------------------------------------


class PublicationFormat(StrEnum):
    HTML = "html"
    XLSX = "xlsx"
    PPTX = "pptx"
    PDF = "pdf"


class PublicationAttemptStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    RENDER_FAILED = "render_failed"
    STORE_FAILED = "store_failed"


class PublicationErrorCode(StrEnum):
    NOT_FOUND = "publication_not_found"
    SCOPE_CONFLICT = "publication_scope_conflict"
    FREEZE_CONFLICT = "publication_freeze_conflict"
    IDEMPOTENCY_CONFLICT = "publication_idempotency_conflict"
    RENDER_FAILURE = "publication_render_failure"
    OBJECT_STORE_FAILURE = "publication_object_store_failure"
    INTEGRITY_FAILURE = "publication_integrity_failure"
    INTENT_NOT_DURABLE = "publication_intent_not_durable"
    OUTCOME_NOT_DURABLE = "publication_outcome_not_durable"
    AUDIT_UNAVAILABLE = "audit_unavailable"


class PublicationError(RuntimeError):
    """§7.5 错误类型基类。"""

    http_status: int = 500
    error_code: PublicationErrorCode


class PublicationNotFound(PublicationError):
    http_status = 404
    error_code = PublicationErrorCode.NOT_FOUND


class PublicationScopeConflict(PublicationError):
    http_status = 403
    error_code = PublicationErrorCode.SCOPE_CONFLICT


class PublicationFreezeConflict(PublicationError):
    http_status = 409
    error_code = PublicationErrorCode.FREEZE_CONFLICT


class PublicationIdempotencyConflict(PublicationError):
    http_status = 409
    error_code = PublicationErrorCode.IDEMPOTENCY_CONFLICT


class PublicationRenderFailure(PublicationError):
    http_status = 503
    error_code = PublicationErrorCode.RENDER_FAILURE


class PublicationObjectStoreFailure(PublicationError):
    http_status = 503
    error_code = PublicationErrorCode.OBJECT_STORE_FAILURE


class PublicationIntegrityFailure(PublicationError):
    http_status = 503
    error_code = PublicationErrorCode.INTEGRITY_FAILURE


class PublicationIntentNotDurable(PublicationError):
    http_status = 503
    error_code = PublicationErrorCode.INTENT_NOT_DURABLE


class PublicationOutcomeNotDurable(PublicationError):
    http_status = 503
    error_code = PublicationErrorCode.OUTCOME_NOT_DURABLE


@dataclass(frozen=True)
class PublicationRequest:
    publication_id: UUID | None
    idempotency_key: str
    resource_type: str
    resource_id: str
    enterprise_id: UUID | None
    source_payload_sha256: str
    formats: tuple[PublicationFormat, ...]

    def __post_init__(self) -> None:
        if not self.formats:
            raise ValueError("formats 不能为空")
        ordered = tuple(sorted(self.formats, key=lambda f: f.value))
        if ordered != self.formats:
            raise ValueError("formats 必须按枚举值排序")
        if len(set(self.formats)) != len(self.formats):
            raise ValueError("formats 不得重复")
        key = self.idempotency_key
        if not (1 <= len(key.encode("utf-8")) <= 128):
            raise ValueError("Idempotency-Key 必须是 1–128 字节")
        if any(not (0x20 <= b <= 0x7E) for b in key.encode("utf-8")):
            raise ValueError("Idempotency-Key 必须是可打印 ASCII")
        if (
            not isinstance(self.source_payload_sha256, str)
            or len(self.source_payload_sha256) != 64
            or any(c not in "0123456789abcdef" for c in self.source_payload_sha256)
        ):
            raise ValueError("source_payload_sha256 必须是 64 位小写 hex")


@dataclass(frozen=True)
class ObjectPlan:
    attempt_id: UUID
    format: PublicationFormat
    object_key: str


@dataclass(frozen=True)
class PreparedPublication:
    publication_id: UUID
    idempotency_key: str
    resource_type: str
    resource_id: str
    enterprise_id: UUID | None
    source_payload_sha256: str
    formats: tuple[PublicationFormat, ...]
    object_plans: tuple[ObjectPlan, ...]
    intent_event_id: UUID


@dataclass(frozen=True)
class ObjectOutcome:
    attempt_id: UUID
    format: PublicationFormat
    status: PublicationAttemptStatus
    object_key: str
    content_type: str | None
    content_sha256: str | None
    size_bytes: int | None
    stored_object_id: UUID | None
    error_type: PublicationErrorCode | None
    error_message: str | None


@dataclass(frozen=True)
class ObjectBatchOutcome:
    publication_id: UUID
    outcomes: tuple[ObjectOutcome, ...]


@dataclass(frozen=True)
class PublicationFailure:
    error_code: PublicationErrorCode
    failed_attempt_ids: tuple[UUID, ...]
    retryable: bool
    http_status: int
    message: str


@dataclass(frozen=True)
class StoredObjectRef:
    stored_object_id: UUID
    object_key: str
    content_type: str
    content_sha256: str
    size_bytes: int


@dataclass(frozen=True)
class FinalizedPublication:
    publication_id: UUID
    status: str  # "published" | "failed"
    outcomes: tuple[ObjectOutcome, ...]


RendererRegistry = Mapping[PublicationFormat, Callable[[PreparedPublication, ObjectPlan], bytes]]


class PublicationObjectStore(Protocol):
    def write_if_absent(
        self,
        *,
        object_key: str,
        content: bytes,
        content_type: str,
        content_sha256: str,
    ) -> StoredObjectRef: ...


# ---------------------------------------------------------------------------
# 冻结资源校验器注册表（publishing/operations 各自注册；本模块不反向依赖）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VerifiedResource:
    """prepare_intent 资源校验结果：canonical 载荷 + 作用域。"""

    canonical_payload: dict[str, Any]
    scope: str  # "public" | "enterprise"
    enterprise_id: UUID | None


ResourceVerifier = Callable[[Session, UUID], VerifiedResource]

_RESOURCE_VERIFIERS: dict[str, ResourceVerifier] = {}


def register_resource_verifier(resource_type: str, verifier: ResourceVerifier) -> None:
    """publishing/operations 模块加载时注册自己的冻结资源校验器。"""

    _RESOURCE_VERIFIERS[resource_type] = verifier


def canonical_source_sha256(payload: Mapping[str, Any]) -> str:
    """冻结输入 hash：canonical JSON（sort_keys、紧凑分隔符、UTF-8）。"""

    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


_CONTENT_TYPES: dict[PublicationFormat, str] = {
    PublicationFormat.HTML: "text/html; charset=utf-8",
    PublicationFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    PublicationFormat.PPTX: (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ),
    PublicationFormat.PDF: "application/pdf",
}


# ---------------------------------------------------------------------------
# 阶段 1：prepare_intent（只 flush，不 commit；不 render、不写对象）
# ---------------------------------------------------------------------------


def prepare_intent(
    session: Session,
    request: PublicationRequest,
    audit_context: AuditContext,
) -> PreparedPublication:
    from flow_api.infrastructure.models.publishing import PublicationAttempt

    verifier = _RESOURCE_VERIFIERS.get(request.resource_type)
    if verifier is None:
        raise ValueError(f"未知 resource_type：{request.resource_type}")
    resource_id = UUID(request.resource_id)

    verified = verifier(session, resource_id)
    if verified.enterprise_id != request.enterprise_id:
        raise PublicationScopeConflict(f"resource {request.resource_id} 与请求企业作用域不一致")
    actual_hash = canonical_source_sha256(verified.canonical_payload)
    if actual_hash != request.source_payload_sha256:
        raise PublicationFreezeConflict(
            f"冻结输入 hash 不一致：资源当前 {actual_hash[:12]}…"
            f"，请求 {request.source_payload_sha256[:12]}…"
        )

    parent_column = _PARENT_COLUMN[request.resource_type]
    existing = session.scalars(
        select(PublicationAttempt).where(
            getattr(PublicationAttempt, parent_column) == resource_id,
            PublicationAttempt.idempotency_key == request.idempotency_key,
        )
    ).all()
    if existing:
        first = existing[0]
        if first.publication_id is None:  # pragma: no cover - 0028 后必非空
            raise PublicationIdempotencyConflict("既有 attempt 缺 publication_id")
        existing_formats = {
            PublicationFormat(row.format) for row in existing if row.format is not None
        }
        existing_hash = first.source_payload_sha256
        if (
            existing_formats != set(request.formats)
            or existing_hash != request.source_payload_sha256
        ):
            raise PublicationIdempotencyConflict(
                "同 Idempotency-Key 但 resource/formats/source hash 不同（§7.4）"
            )
        publication_id = first.publication_id
        succeeded = {
            row.format for row in existing if row.status == PublicationAttemptStatus.SUCCEEDED.value
        }
    else:
        publication_id = request.publication_id or new_uuid7()
        succeeded = set()

    max_sequence = session.scalar(
        select(PublicationAttempt.sequence)
        .where(getattr(PublicationAttempt, parent_column) == resource_id)
        .order_by(PublicationAttempt.sequence.desc())
        .limit(1)
    )
    sequence = int(max_sequence or 0) + 1

    attempts: dict[PublicationFormat, UUID] = {}
    for row in existing:
        if (
            row.format is not None
            and row.format in succeeded
            and PublicationFormat(row.format) in request.formats
        ):
            attempts[PublicationFormat(row.format)] = row.id
    for fmt in request.formats:
        if fmt in attempts:
            continue
        attempt = PublicationAttempt(
            **{
                parent_column: resource_id,
                "sequence": sequence,
                "format": fmt.value,
                "status": PublicationAttemptStatus.PENDING.value,
                "publication_id": publication_id,
                "idempotency_key": request.idempotency_key,
                "source_payload_sha256": request.source_payload_sha256,
            }
        )
        session.add(attempt)
        session.flush()
        attempts[fmt] = attempt.id

    intent_event_id = publication_id
    get_audit_writer().write_intent(audit_context=audit_context, intent_event_id=intent_event_id)

    object_plans = tuple(
        ObjectPlan(
            attempt_id=attempts[fmt],
            format=fmt,
            object_key=(
                f"{request.resource_type}/{request.resource_id}/{publication_id}"
                f"/{fmt.value}/{request.source_payload_sha256}"
            ),
        )
        for fmt in request.formats
    )
    return PreparedPublication(
        publication_id=publication_id,
        idempotency_key=request.idempotency_key,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        enterprise_id=request.enterprise_id,
        source_payload_sha256=request.source_payload_sha256,
        formats=tuple(request.formats),
        object_plans=object_plans,
        intent_event_id=intent_event_id,
    )


_PARENT_COLUMN: dict[str, str] = {
    "report_snapshot": "report_snapshot_id",
    "operations_snapshot": "objective_report_snapshot_id",
}


# ---------------------------------------------------------------------------
# 阶段 3：execute_object（无 Session）
# ---------------------------------------------------------------------------


def execute_object(
    prepared: PreparedPublication,
    renderers: RendererRegistry,
    object_store: PublicationObjectStore,
) -> ObjectBatchOutcome:
    outcomes: list[ObjectOutcome] = []
    for plan in prepared.object_plans:
        renderer = renderers.get(plan.format)
        if renderer is None:
            outcomes.append(
                ObjectOutcome(
                    attempt_id=plan.attempt_id,
                    format=plan.format,
                    status=PublicationAttemptStatus.RENDER_FAILED,
                    object_key=plan.object_key,
                    content_type=None,
                    content_sha256=None,
                    size_bytes=None,
                    stored_object_id=None,
                    error_type=PublicationErrorCode.RENDER_FAILURE,
                    error_message=redact_audit_text(
                        f"format {plan.format.value} 无可用 renderer"
                    ).text,
                )
            )
            continue
        try:
            payload = renderer(prepared, plan)
            if not isinstance(payload, bytes):
                raise PublicationRenderFailure("renderer 必须返回 bytes")
            content_sha256 = hashlib.sha256(payload).hexdigest()
            stored = object_store.write_if_absent(
                object_key=plan.object_key,
                content=payload,
                content_type=_CONTENT_TYPES[plan.format],
                content_sha256=content_sha256,
            )
        except PublicationRenderFailure as error:
            outcomes.append(
                ObjectOutcome(
                    attempt_id=plan.attempt_id,
                    format=plan.format,
                    status=PublicationAttemptStatus.RENDER_FAILED,
                    object_key=plan.object_key,
                    content_type=None,
                    content_sha256=None,
                    size_bytes=None,
                    stored_object_id=None,
                    error_type=PublicationErrorCode.RENDER_FAILURE,
                    error_message=redact_audit_text(str(error)).text,
                )
            )
            continue
        except Exception as error:  # noqa: BLE001 - store/完整性错误统一收敛
            is_integrity = "integrity" in str(error).lower() or "conflict" in str(error).lower()
            outcomes.append(
                ObjectOutcome(
                    attempt_id=plan.attempt_id,
                    format=plan.format,
                    status=PublicationAttemptStatus.STORE_FAILED,
                    object_key=plan.object_key,
                    content_type=None,
                    content_sha256=None,
                    size_bytes=None,
                    stored_object_id=None,
                    error_type=(
                        PublicationErrorCode.INTEGRITY_FAILURE
                        if is_integrity
                        else PublicationErrorCode.OBJECT_STORE_FAILURE
                    ),
                    error_message=redact_audit_text(str(error)).text,
                )
            )
            continue
        outcomes.append(
            ObjectOutcome(
                attempt_id=plan.attempt_id,
                format=plan.format,
                status=PublicationAttemptStatus.SUCCEEDED,
                object_key=stored.object_key,
                content_type=stored.content_type,
                content_sha256=stored.content_sha256,
                size_bytes=stored.size_bytes,
                stored_object_id=stored.stored_object_id,
                error_type=None,
                error_message=None,
            )
        )
    return ObjectBatchOutcome(publication_id=prepared.publication_id, outcomes=tuple(outcomes))


def build_publication_failure(outcome: ObjectBatchOutcome) -> PublicationFailure | None:
    """任一 format 未成功 → 构造 PublicationFailure（all-or-failed，§7.3-4）。"""

    failed = [oc for oc in outcome.outcomes if oc.status is not PublicationAttemptStatus.SUCCEEDED]
    if not failed:
        return None
    first = failed[0]
    return PublicationFailure(
        error_code=first.error_type or PublicationErrorCode.RENDER_FAILURE,
        failed_attempt_ids=tuple(oc.attempt_id for oc in failed),
        retryable=True,
        http_status=503,
        message=(
            first.error_message
            or (first.error_type.value if first.error_type else "publication failed")
        ),
    )


# ---------------------------------------------------------------------------
# 阶段 4：finalize（只 flush；outcome 审计独立短事务）
# ---------------------------------------------------------------------------


def _persist_outcomes(
    session: Session,
    outcome: ObjectBatchOutcome,
) -> None:
    from flow_api.infrastructure.models.intake import StoredObject
    from flow_api.infrastructure.models.publishing import PublicationAttempt

    for oc in outcome.outcomes:
        attempt = session.get(PublicationAttempt, oc.attempt_id)
        if attempt is None:  # pragma: no cover - attempt 由 prepare 落库
            raise PublicationOutcomeNotDurable(f"attempt 不存在: {oc.attempt_id}")
        attempt.status = oc.status.value
        attempt.object_key = oc.object_key
        attempt.error_code = oc.error_type.value if oc.error_type else None
        attempt.error_message = oc.error_message
        if oc.status is PublicationAttemptStatus.SUCCEEDED:
            assert oc.content_sha256 is not None and oc.size_bytes is not None
            stored = session.scalar(
                select(StoredObject).where(StoredObject.sha256 == oc.content_sha256)
            )
            if stored is None:
                stored = StoredObject(
                    sha256=oc.content_sha256,
                    object_key=oc.object_key,
                    size_bytes=oc.size_bytes,
                    content_type=oc.content_type or "application/octet-stream",
                )
                session.add(stored)
                session.flush()
            attempt.stored_object_id = stored.id
            attempt.content_sha256 = oc.content_sha256
            attempt.size_bytes = oc.size_bytes
            attempt.content_type = oc.content_type


def finalize_success(
    session: Session,
    prepared: PreparedPublication,
    outcome: ObjectBatchOutcome,
    audit_context: AuditContext,
) -> FinalizedPublication:
    _persist_outcomes(session, outcome)
    from flow_api.security.authorization import Decision, ReasonCode

    get_audit_writer().write_outcome(
        audit_context=audit_context,
        intent_event_id=prepared.intent_event_id,
        outcome=Decision(allowed=True, reason_code=ReasonCode.ALLOW),
        error_code=None,
    )
    session.flush()
    return FinalizedPublication(
        publication_id=prepared.publication_id,
        status="published",
        outcomes=outcome.outcomes,
    )


def finalize_failure(
    session: Session,
    prepared: PreparedPublication,
    outcome: ObjectBatchOutcome,
    failure: PublicationFailure,
    audit_context: AuditContext,
) -> FinalizedPublication:
    _persist_outcomes(session, outcome)
    from flow_api.security.authorization import Decision, ReasonCode

    get_audit_writer().write_outcome(
        audit_context=audit_context,
        intent_event_id=prepared.intent_event_id,
        outcome=Decision(allowed=False, reason_code=ReasonCode.ALLOW),
        error_code=failure.error_code.value,
    )
    session.flush()
    return FinalizedPublication(
        publication_id=prepared.publication_id,
        status="failed",
        outcomes=outcome.outcomes,
    )
