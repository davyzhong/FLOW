"""O3：从不可变经营快照生成并登记多格式产物。"""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any
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

PdfPrinter = Callable[[bytes], bytes]


class OperationsPublicationError(RuntimeError):
    code = "operations_publication_failed"


def _next_sequence(session: Session, snapshot_id: UUID) -> int:
    current = session.scalar(
        select(PublicationAttempt.sequence)
        .where(PublicationAttempt.objective_report_snapshot_id == snapshot_id)
        .order_by(PublicationAttempt.sequence.desc())
        .limit(1)
    )
    return int(current or 0) + 1


def _default_pdf_printer(html: bytes) -> bytes:
    from flow_api.statements.objective_report_pdf import print_pdf

    with tempfile.TemporaryDirectory() as temporary_directory:
        output = Path(temporary_directory) / "operations.pdf"
        print_pdf(
            html.decode("utf-8"),
            out_path=output,
            footer_left="FLOW 经营分析概览",
        )
        return output.read_bytes()


class OperationsPublicationService:
    """逐格式追加 PublicationAttempt；失败保留，重试不改写历史。"""

    def __init__(
        self,
        *,
        pdf_printer: PdfPrinter | None = None,
        store: Any | None = None,
    ) -> None:
        self._pdf_printer = pdf_printer or _default_pdf_printer
        self._store = store

    def _object_store(self) -> Any:
        if self._store is not None:
            return self._store
        from flow_api.infrastructure.object_store import ObjectStore
        from flow_api.infrastructure.s3_client import build_s3_client
        from flow_api.settings import get_settings

        settings = get_settings()
        return ObjectStore(
            client=build_s3_client(settings),
            bucket=settings.s3_bucket,
        )

    def publish(
        self,
        session: Session,
        snapshot_id: UUID,
        *,
        formats: tuple[str, ...] = ("pptx", "xlsx", "html", "pdf"),
    ) -> dict[str, str]:
        snapshot = session.get(ObjectiveReportSnapshot, snapshot_id)
        if snapshot is None:
            raise OperationsPublicationError(
                f"objective report snapshot does not exist: {snapshot_id}"
            )
        if snapshot.report_type != "operations_overview":
            raise OperationsPublicationError("snapshot report_type must be operations_overview")

        store = self._object_store()
        outcomes: dict[str, str] = {}
        for output_format in formats:
            attempt = PublicationAttempt(
                objective_report_snapshot_id=snapshot.id,
                sequence=_next_sequence(session, snapshot.id),
                format=output_format,
                status="running",
            )
            session.add(attempt)
            session.flush()
            try:
                payload = self._render(output_format, snapshot.payload)
                stored = store.put_immutable(payload, f"operations.{output_format}")
                stored_row = session.scalar(
                    select(StoredObject).where(StoredObject.sha256 == stored.sha256)
                )
                if stored_row is None:
                    stored_row = StoredObject(
                        sha256=stored.sha256,
                        object_key=stored.object_key,
                        size_bytes=stored.size_bytes,
                        content_type=stored.content_type,
                    )
                    session.add(stored_row)
                    session.flush()
                attempt.stored_object_id = stored_row.id
                attempt.status = "succeeded"
                outcomes[output_format] = "succeeded"
            except Exception as error:  # noqa: BLE001 - append-only failure evidence
                attempt.status = "failed"
                attempt.error_message = str(error)[:500]
                outcomes[output_format] = "failed"
            session.flush()
        session.commit()
        return outcomes

    def _render(self, output_format: str, payload: dict[str, Any]) -> bytes:
        if output_format == "pptx":
            return render_operations_pptx(payload)
        if output_format == "xlsx":
            return render_operations_xlsx(payload)
        html = render_operations_html(payload).encode("utf-8")
        if output_format == "html":
            return html
        if output_format == "pdf":
            return self._pdf_printer(html)
        raise OperationsPublicationError(
            f"unsupported operations publication format: {output_format}"
        )


__all__ = [
    "OperationsPublicationError",
    "OperationsPublicationService",
    "PdfPrinter",
]
