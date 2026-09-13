"""S01 §7.1 operations publication 四阶段 ABI：OperationsPublicationPipeline。

与 publishing/pipeline.py 对称，公开相同的阶段划分（prepare_intent /
execute_object / finalize_success / finalize_failure），保证 §7.1 强制
"publishing 与 operations 必须共用以下类型、签名、异常和时序"。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.intake import StoredObject
from flow_api.infrastructure.models.publishing import PublicationAttempt
from flow_api.operations.renderers import (
    render_operations_html,
    render_operations_pptx,
    render_operations_xlsx,
)
from flow_api.publishing.objective_freeze import ObjectiveReportSnapshot
from flow_api.publishing.pipeline import (
    PublicationFormatResult,
    PublicationPipelineError,
    PublicationResult,
)


class _OperationsRenderer(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> bytes:
        ...


@dataclass(frozen=True)
class OperationsPreparedPublication:
    snapshot_id: UUID
    enterprise_id: UUID
    actor_id: str
    correlation_id: str
    request_id: str
    formats: tuple[str, ...]
    idempotency_key: tuple[str, ...]
    payload: dict[str, Any]
    sequence: int
    intent_event_id: UUID


class OperationsPublicationPipeline:
    """§7.1 operations publication 四阶段 ABI。"""

    def __init__(self, *, store: Any) -> None:
        self._store = store
        self._renderers: dict[str, _OperationsRenderer] = {
            "html": lambda p: render_operations_html(p).encode("utf-8"),
            "xlsx": render_operations_xlsx,
            "pptx": render_operations_pptx,
        }

    def prepare_intent(
        self,
        session: Session,
        *,
        snapshot_id: UUID,
        actor_id: str,
        correlation_id: str,
        request_id: str,
        formats: tuple[str, ...] = ("pptx", "xlsx", "html", "pdf"),
    ) -> OperationsPreparedPublication:
        snapshot = session.get(ObjectiveReportSnapshot, snapshot_id)
        if snapshot is None:
            raise PublicationPipelineError(
                f"objective report snapshot not found: {snapshot_id}"
            )
        if snapshot.report_type != "operations_overview":
            raise PublicationPipelineError("snapshot report_type must be operations_overview")
        # formats 校验：html/xlsx/pptx 在 _renderers；pdf 走 pdf_printer
        unknown = [f for f in formats if f not in self._renderers and f != "pdf"]
        if unknown:
            raise PublicationPipelineError(f"unsupported operations formats: {sorted(unknown)}")
        sequence = _next_sequence(session, snapshot_id)
        attempt = PublicationAttempt(
            objective_report_snapshot_id=snapshot_id,
            sequence=sequence,
            format=formats[0],
            status="running",
        )
        session.add(attempt)
        session.flush()
        # 提取 payload：snapshot.payload 是 dict
        payload = dict(snapshot.payload) if isinstance(snapshot.payload, dict) else {}
        enterprise_id = getattr(snapshot, "enterprise_id", None)
        if enterprise_id is None:
            raise PublicationPipelineError(
                f"snapshot {snapshot_id} has no enterprise_id"
            )
        return OperationsPreparedPublication(
            snapshot_id=snapshot_id,
            enterprise_id=enterprise_id,
            actor_id=actor_id,
            correlation_id=correlation_id,
            request_id=request_id,
            formats=formats,
            idempotency_key=("operations", str(snapshot_id), str(sequence)),
            payload=payload,
            sequence=sequence,
            intent_event_id=attempt.id,
        )

    def execute_object(
        self,
        prepared: OperationsPreparedPublication,
        *,
        pdf_printer: Any | None = None,
    ) -> PublicationResult:
        """§7.1 execute_object：无 Session，仅副作用。"""
        results: list[PublicationFormatResult] = []
        for fmt in prepared.formats:
            try:
                if fmt in self._renderers:
                    payload = self._renderers[fmt](prepared.payload)
                elif fmt == "pdf":
                    if pdf_printer is None:
                        raise PublicationPipelineError("pdf_printer is None")
                    html_bytes = self._renderers["html"](prepared.payload)
                    payload = pdf_printer(html_bytes)
                else:
                    raise PublicationPipelineError(f"unsupported operations format: {fmt}")
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
            except Exception as error:  # noqa: BLE001
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
        prepared: OperationsPreparedPublication,
        result: PublicationResult,
    ) -> None:
        for fmt_result in result.formats:
            attempt = session.scalar(
                select(PublicationAttempt).where(
                    PublicationAttempt.objective_report_snapshot_id == prepared.snapshot_id,
                    PublicationAttempt.sequence == prepared.sequence,
                    PublicationAttempt.format == fmt_result.format,
                )
            )
            if attempt is None:
                attempt = PublicationAttempt(
                    objective_report_snapshot_id=prepared.snapshot_id,
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
        prepared: OperationsPreparedPublication,
        error: Exception,
    ) -> None:
        for fmt in prepared.formats:
            attempt = session.scalar(
                select(PublicationAttempt).where(
                    PublicationAttempt.objective_report_snapshot_id == prepared.snapshot_id,
                    PublicationAttempt.sequence == prepared.sequence,
                    PublicationAttempt.format == fmt,
                )
            )
            if attempt is None:
                attempt = PublicationAttempt(
                    objective_report_snapshot_id=prepared.snapshot_id,
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


def _next_sequence(session: Session, snapshot_id: UUID) -> int:
    current = session.scalar(
        select(PublicationAttempt.sequence)
        .where(PublicationAttempt.objective_report_snapshot_id == snapshot_id)
        .order_by(PublicationAttempt.sequence.desc())
        .limit(1)
    )
    return int(current or 0) + 1


__all__ = [
    "OperationsPreparedPublication",
    "OperationsPublicationPipeline",
    "PublicationResult",
    "PublicationFormatResult",
    "PublicationPipelineError",
]
