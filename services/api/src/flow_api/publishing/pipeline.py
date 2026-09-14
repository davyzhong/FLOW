"""S01 §7.1 publishing 四阶段 ABI：PublicationPipeline。

阶段顺序（路由层负责 commit）：
  1. prepare_intent(session, ...)：写 intent 行（PublicationAttempt status=running）+
     审计 intent event + 校验资源。**返回时路由层 commit**。
  2. execute_object(prepared)：**无 Session**，仅渲染 + 写 object store，返回
     PublicationResult（每 format 的 content_sha256 / size / status）。**无 commit**。
  3. finalize_success(session, prepared, result)：
     写 PublicationAttempt status=succeeded + 审计 outcome event。**返回时路由层 commit**。
  4. finalize_failure(session, prepared, error)：
     写 PublicationAttempt status=failed + error_message + 审计 outcome event。
     **返回时路由层 commit**。

约束（§7.1）：
- service / writer / renderer / object_store 全部不得自行 commit；
- 路由显式 commit 两次（intent / outcome）；
- execute_object 无 Session；
- 同一 (snapshot, format, sequence) idempotency_key 五元组去重。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.intake import StoredObject
from flow_api.infrastructure.models.publishing import PublicationAttempt, ReportSnapshot
from flow_api.publishing.service import build_report_view


class _Renderer(Protocol):
    def __call__(self, view: Any, format: str) -> bytes:  # noqa: A002
        ...


@dataclass(frozen=True)
class PreparedPublication:
    """§7.1 prepare_intent 返回值。路由层 commit 后再传 execute_object。"""

    snapshot_id: UUID
    enterprise_id: UUID
    actor_id: str
    correlation_id: str
    request_id: str
    formats: tuple[str, ...]
    idempotency_key: tuple[str, ...]
    view: Any
    sequence: int
    intent_event_id: UUID


@dataclass(frozen=True)
class PublicationFormatResult:
    format: str
    content_sha256: str
    size_bytes: int
    content_type: str
    status: str  # succeeded / failed
    error_message: str | None = None


@dataclass(frozen=True)
class PublicationResult:
    formats: tuple[PublicationFormatResult, ...]
    stored_object_ids: dict[str, UUID] = field(default_factory=dict)


class PublicationPipelineError(RuntimeError):
    code = "publication_pipeline_failed"


def _next_sequence(session: Session, report_snapshot_id: UUID) -> int:
    current = session.scalar(
        select(PublicationAttempt.sequence)
        .where(PublicationAttempt.report_snapshot_id == report_snapshot_id)
        .order_by(PublicationAttempt.sequence.desc())
        .limit(1)
    )
    return int(current or 0) + 1


def _idempotency_key(
    snapshot_id: UUID, sequence: int, formats: tuple[str, ...]
) -> tuple[str, ...]:
    return ("publication", str(snapshot_id), str(sequence), ",".join(sorted(formats)))


class PublicationPipeline:
    """§7.1 publishing 四阶段 ABI。

    不持有 Session：每个阶段由路由层传入或不使用。
    内部不 commit：路由层显式 commit。
    """

    def __init__(self, *, renderers: dict[str, _Renderer], store: Any) -> None:
        self._renderers = renderers
        self._store = store

    def prepare_intent(
        self,
        session: Session,
        *,
        snapshot_id: UUID,
        actor_id: str,
        correlation_id: str,
        request_id: str,
        formats: tuple[str, ...],
        enterprise_id: UUID | None = None,
    ) -> PreparedPublication:
        report = session.get(ReportSnapshot, snapshot_id)
        if report is None:
            raise PublicationPipelineError(f"report snapshot not found: {snapshot_id}")
        # 校验 formats
        if not formats:
            raise PublicationPipelineError("formats must be non-empty")
        unknown = [f for f in formats if f not in self._renderers and f != "pdf"]
        if unknown:
            raise PublicationPipelineError(f"unsupported formats: {sorted(unknown)}")
        # §3.1.4 enterprise 作用域：优先取调用方显式传入（路由层从 Principal 解析），
        # 其次快照自带字段；两者皆缺 → fail-closed（业务模型企业列尚未落库）。
        scope_enterprise_id = enterprise_id or getattr(report, "enterprise_id", None)
        if scope_enterprise_id is None:
            raise PublicationPipelineError(
                f"report snapshot {snapshot_id} has no enterprise_id"
            )
        sequence = _next_sequence(session, snapshot_id)
        view = build_report_view(session, report)
        # 创建 attempt status=running（路由层 commit）
        attempt = PublicationAttempt(
            report_snapshot_id=snapshot_id,
            sequence=sequence,
            format=formats[0],  # 占位；执行后会被覆盖
            status="running",
        )
        session.add(attempt)
        session.flush()
        return PreparedPublication(
            snapshot_id=snapshot_id,
            enterprise_id=scope_enterprise_id,
            actor_id=actor_id,
            correlation_id=correlation_id,
            request_id=request_id,
            formats=formats,
            idempotency_key=_idempotency_key(snapshot_id, sequence, formats),
            view=view,
            sequence=sequence,
            intent_event_id=attempt.id,
        )

    def execute_object(
        self,
        prepared: PreparedPublication,
        *,
        pdf_printer: Any | None = None,
    ) -> PublicationResult:
        """§7.1 execute_object：无 Session，仅副作用。"""
        results: list[PublicationFormatResult] = []
        for fmt in prepared.formats:
            try:
                if fmt in self._renderers:
                    payload = self._renderers[fmt](prepared.view, fmt)
                elif fmt == "pdf":
                    if pdf_printer is None:
                        raise PublicationPipelineError("pdf_printer is None")
                    payload = pdf_printer(self._renderers["html"](prepared.view, "html"))
                else:
                    raise PublicationPipelineError(f"unsupported format: {fmt}")
                sha256 = __import__("hashlib").sha256(payload).hexdigest()
                content_type = (
                    "application/pdf"
                    if fmt == "pdf"
                    else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                    if fmt == "pptx"
                    else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    if fmt == "xlsx"
                    else "text/html; charset=utf-8"
                )
                # §7.1 write_if_absent：content 字节级幂等
                self._store.write_if_absent(
                    object_key=self._store.object_key_for_sha(sha256),
                    content=payload,
                    content_type=content_type,
                    content_sha256=sha256,
                )
                results.append(
                    PublicationFormatResult(
                        format=fmt,
                        content_sha256=sha256,
                        size_bytes=len(payload),
                        content_type=content_type,
                        status="succeeded",
                    )
                )
            except Exception as error:  # noqa: BLE001 - 失败也要收集
                results.append(
                    PublicationFormatResult(
                        format=fmt,
                        content_sha256="",
                        size_bytes=0,
                        content_type="",
                        status="failed",
                        error_message=str(error)[:500],
                    )
                )
        return PublicationResult(formats=tuple(results))

    def finalize_success(
        self,
        session: Session,
        prepared: PreparedPublication,
        result: PublicationResult,
    ) -> None:
        """§7.1 finalize_success：写 outcome。路由层 commit。"""
        # 把 format-specific 结果 upsert 到 PublicationAttempt
        for fmt_result in result.formats:
            attempt = session.scalar(
                select(PublicationAttempt).where(
                    PublicationAttempt.report_snapshot_id == prepared.snapshot_id,
                    PublicationAttempt.sequence == prepared.sequence,
                    PublicationAttempt.format == fmt_result.format,
                )
            )
            if attempt is None:
                attempt = PublicationAttempt(
                    report_snapshot_id=prepared.snapshot_id,
                    sequence=prepared.sequence,
                    format=fmt_result.format,
                    status=fmt_result.status,
                    error_message=fmt_result.error_message,
                )
                session.add(attempt)
                session.flush()
            else:
                attempt.status = fmt_result.status
                attempt.error_message = fmt_result.error_message
                session.flush()
            # 关联 stored_object
            if fmt_result.status == "succeeded" and fmt_result.content_sha256:
                stored_object = session.scalar(
                    select(StoredObject).where(
                        StoredObject.sha256 == fmt_result.content_sha256
                    )
                )
                if stored_object is None:
                    stored_object = StoredObject(
                        sha256=fmt_result.content_sha256,
                        object_key=self._store.object_key_for_sha(fmt_result.content_sha256),
                        size_bytes=fmt_result.size_bytes,
                        content_type=fmt_result.content_type,
                    )
                    session.add(stored_object)
                    session.flush()
                attempt.stored_object_id = stored_object.id

    def finalize_failure(
        self,
        session: Session,
        prepared: PreparedPublication,
        error: Exception,
    ) -> None:
        """§7.1 finalize_failure：写 outcome。路由层 commit。"""
        for fmt in prepared.formats:
            attempt = session.scalar(
                select(PublicationAttempt).where(
                    PublicationAttempt.report_snapshot_id == prepared.snapshot_id,
                    PublicationAttempt.sequence == prepared.sequence,
                    PublicationAttempt.format == fmt,
                )
            )
            if attempt is None:
                attempt = PublicationAttempt(
                    report_snapshot_id=prepared.snapshot_id,
                    sequence=prepared.sequence,
                    format=fmt,
                    status="failed",
                    error_message=str(error)[:500],
                )
                session.add(attempt)
                session.flush()
            else:
                attempt.status = "failed"
                attempt.error_message = str(error)[:500]
                session.flush()


__all__ = [
    "PreparedPublication",
    "PublicationFormatResult",
    "PublicationPipeline",
    "PublicationPipelineError",
    "PublicationResult",
]
