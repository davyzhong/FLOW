from __future__ import annotations

from io import BytesIO

import pytest
from integration.analysis_run_support import (
    analysis_session_fixture as analysis_session,  # noqa: F401
)
from integration.intake_service_support import (
    intake_session_fixture as intake_session_fixture,  # noqa: F401
)
from integration.metric_snapshot_support import (
    metric_session_fixture as metric_session_fixture,  # noqa: F401
)
from openpyxl import load_workbook
from pptx import Presentation
from publishing.publishing_support import publish_analysis_run
from publishing.publishing_support import (
    publishing_session_fixture as _publishing_session_fixture,  # noqa: F401
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.analytics import Conclusion, Evidence, Finding
from flow_api.infrastructure.models.publishing import PublicationAttempt
from flow_api.investigation.state_machines import apply_finding_decision
from flow_api.publishing.publication import PublicationService
from flow_api.publishing.renderers import render_html, render_pptx, render_xlsx
from flow_api.publishing.service import (
    PublishingFreezeError,
    freeze_report_snapshot,
)


def _approve_top_findings(session: Session, count: int = 1) -> None:
    findings = session.scalars(select(Finding).order_by(Finding.total_score.desc())).all()
    assert findings
    for finding in findings[:count]:
        evidence = session.scalars(
            select(Evidence).where(Evidence.finding_id == finding.id)
        ).all()
        assert all(item.status == "verified" for item in evidence)
        session.add(
            Conclusion(
                finding=finding,
                verified_facts="已验证事实成立。",
                analysis_judgment="成本上升是主要驱动。",
                open_questions="暂无。",
                recommendation="重新议价。",
            )
        )
        session.flush()
        apply_finding_decision(session, finding, "submitted", reviewer="陈晨", comment=None)
        apply_finding_decision(session, finding, "approved", reviewer="王总", comment=None)


def test_freeze_requires_approved_findings(publishing_session: Session) -> None:
    publish_analysis_run(publishing_session)
    snapshot_id = publishing_session.scalar(select(Finding.metric_snapshot_id).limit(1))
    with pytest.raises(PublishingFreezeError) as error:
        freeze_report_snapshot(publishing_session, metric_snapshot_id=snapshot_id)
    assert "approved" in str(error.value)


def test_freeze_and_render_all_formats(publishing_session: Session) -> None:
    publish_analysis_run(publishing_session)
    _approve_top_findings(publishing_session)
    snapshot_id = publishing_session.scalar(select(Finding.metric_snapshot_id).limit(1))
    _report, view = freeze_report_snapshot(publishing_session, metric_snapshot_id=snapshot_id)

    assert view.findings, "approved findings must be frozen into the view"
    assert view.metrics, "metric values must be frozen into the view"
    key_values = view.key_values()
    assert view.identity.metric_snapshot_id == key_values["metric_snapshot_id"]

    presentation = Presentation(BytesIO(render_pptx(view)))
    pptx_text = "\n".join(
        shape.text_frame.text
        for slide in presentation.slides
        for shape in slide.shapes
        if shape.has_text_frame
    )
    assert view.identity.title in pptx_text
    assert f"v{view.identity.report_version}" in pptx_text

    workbook = load_workbook(BytesIO(render_xlsx(view)))
    assert "指标结果" in workbook.sheetnames
    xlsx_values = {
        str(cell.value)
        for sheet in workbook.worksheets
        for row in sheet.iter_rows()
        for cell in row
        if cell.value is not None
    }
    assert key_values["metric_snapshot_id"] in xlsx_values

    html_document = render_html(view).decode("utf-8")
    assert view.identity.title in html_document
    assert "证据脚注" in html_document
    assert key_values["metric_snapshot_id"] in html_document


class FakeStore:
    """In-memory content-addressed store for fast, network-free tests."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_immutable(self, content: bytes, filename: str):
        import hashlib

        from flow_api.infrastructure.models.intake import StoredObject

        sha = hashlib.sha256(content).hexdigest()
        if sha not in self.objects:
            self.objects[sha] = content
        return StoredObject(
            sha256=sha,
            object_key=f"raw/{sha[:2]}/{sha}",
            size_bytes=len(content),
            content_type="application/octet-stream",
        )


def test_publication_attempts_persist_and_retry(publishing_session: Session) -> None:
    publish_analysis_run(publishing_session)
    _approve_top_findings(publishing_session)
    snapshot_id = publishing_session.scalar(select(Finding.metric_snapshot_id).limit(1))
    report, _view = freeze_report_snapshot(publishing_session, metric_snapshot_id=snapshot_id)

    def boom(_html: bytes) -> bytes:
        raise RuntimeError("printer offline")

    service = PublicationService(pdf_printer=boom, store=FakeStore())
    outcomes = service.publish(publishing_session, report.id)
    assert outcomes["pdf"] == "failed"
    assert outcomes["pptx"] == "succeeded"

    service_retry = PublicationService(
        pdf_printer=lambda _html: b"%PDF-1.4 fake", store=FakeStore()
    )
    outcomes_retry = service_retry.publish(publishing_session, report.id)
    assert outcomes_retry["pdf"] == "succeeded"

    attempt_formats = publishing_session.scalars(select(PublicationAttempt.format)).all()
    assert attempt_formats.count("pdf") >= 2


def test_succeeded_attempt_persists_reusable_stored_object(publishing_session: Session) -> None:
    """Task 6 契约：成功 attempt 必须持久化并复用 StoredObject 行（下载授权边界）。"""
    import hashlib

    from flow_api.infrastructure.models.intake import StoredObject
    from publishing.publishing_support import fresh_approved_report

    report, _view = fresh_approved_report(publishing_session)
    payload = b"%PDF-1.4 persisted object"
    service = PublicationService(pdf_printer=lambda _html: payload, store=FakeStore())
    outcomes = service.publish(publishing_session, report.id, formats=("pdf",))
    assert outcomes["pdf"] == "succeeded"

    attempt = publishing_session.scalar(
        select(PublicationAttempt).where(
            PublicationAttempt.report_snapshot_id == report.id,
            PublicationAttempt.format == "pdf",
            PublicationAttempt.status == "succeeded",
        )
    )
    assert attempt is not None
    assert attempt.stored_object_id is not None
    stored_row = publishing_session.get(StoredObject, attempt.stored_object_id)
    assert stored_row is not None
    assert stored_row.sha256 == hashlib.sha256(payload).hexdigest()
    assert stored_row.size_bytes == len(payload)
    assert stored_row.object_key.startswith("raw/")

    # 内容寻址：同 payload 再次发布复用同一 StoredObject 行
    service.publish(publishing_session, report.id, formats=("pdf",))
    duplicate_rows = publishing_session.scalars(
        select(StoredObject).where(StoredObject.sha256 == stored_row.sha256)
    ).all()
    assert len(duplicate_rows) == 1
