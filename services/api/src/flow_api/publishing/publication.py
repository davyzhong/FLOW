"""Publication attempts: render, persist, and retry without re-freezing."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.publishing import (
    PublicationAttempt,
    ReportSnapshot,
)
from flow_api.publishing.renderers import RENDERERS
from flow_api.publishing.service import build_report_view

PdfPrinter = Callable[[bytes], bytes]


class PublicationError(RuntimeError):
    code = "publication_failed"


def _next_sequence(session: Session, report_snapshot_id: Any) -> int:
    current = session.scalar(
        select(PublicationAttempt.sequence)
        .where(PublicationAttempt.report_snapshot_id == report_snapshot_id)
        .order_by(PublicationAttempt.sequence.desc())
        .limit(1)
    )
    return int(current or 0) + 1


class PublicationService:
    def __init__(
        self,
        pdf_printer: PdfPrinter | None = None,
        store: Any | None = None,
    ) -> None:
        self._pdf_printer = pdf_printer
        self._store = store

    def _object_store(self) -> Any:
        if self._store is not None:
            return self._store
        from flow_api.infrastructure.object_store import ObjectStore
        from flow_api.settings import get_settings

        settings = get_settings()
        return ObjectStore(
            client=_store_client(settings),
            bucket=settings.s3_bucket,
        )

    def publish(
        self,
        session: Session,
        report_snapshot_id: UUID,
        formats: tuple[str, ...] = ("pptx", "xlsx", "html", "pdf"),
    ) -> dict[str, str]:
        report = session.get(ReportSnapshot, report_snapshot_id)
        if report is None:
            raise PublicationError(f"report snapshot does not exist: {report_snapshot_id}")
        view = build_report_view(session, report)
        store = self._object_store()
        outcomes: dict[str, str] = {}
        for fmt in formats:
            sequence = _next_sequence(session, report.id)
            attempt = PublicationAttempt(
                report_snapshot_id=report.id,
                sequence=sequence,
                format=fmt,
                status="running",
            )
            session.add(attempt)
            session.flush()
            try:
                if fmt in RENDERERS:
                    payload = RENDERERS[fmt](view)
                elif fmt == "pdf":
                    if self._pdf_printer is None:
                        raise PublicationError(
                            "pdf printer is unavailable; provide a pinned-Chromium printer"
                        )
                    payload = self._pdf_printer(RENDERERS["html"](view))
                else:
                    raise PublicationError(f"unsupported publication format: {fmt}")
                stored = store.put_immutable(payload, f"report.{fmt}")
                attempt.stored_object_id = stored.id
                attempt.status = "succeeded"
                outcomes[fmt] = "succeeded"
            except Exception as error:  # noqa: BLE001 - attempt history must persist
                attempt.status = "failed"
                attempt.error_message = str(error)[:500]
                outcomes[fmt] = "failed"
            session.flush()
        session.commit()
        return outcomes


def _store_client(settings: Any) -> Any:
    import boto3  # type: ignore[import-untyped]

    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key.get_secret_value(),
        aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
    )


__all__ = ["PublicationError", "PublicationService", "PdfPrinter"]
