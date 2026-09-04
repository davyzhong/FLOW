"""Freeze and render Report Snapshots."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid6 import uuid7

from flow_api.infrastructure.models.analytics import (
    AnalysisResult,
    AnalysisRun,
    Conclusion,
    DriverContribution,
    Evidence,
    Finding,
    MetricDefinition,
    MetricSnapshot,
    MetricValue,
)
from flow_api.infrastructure.models.intake import (
    ImportVersion,
    QualityIssue,
    ReconciliationResult,
)
from flow_api.infrastructure.models.publishing import ReportSnapshot, ReportSnapshotItem
from flow_api.investigation.state_machines import conclusion_is_complete
from flow_api.publishing.models import (
    ReportView,
    SnapshotFinding,
    SnapshotIdentity,
    SnapshotMetric,
    view_from_json,
    view_to_json,
)

TEMPLATE_CODE = "flow.monthly-review.v1"


class PublishingFreezeError(RuntimeError):
    code = "publishing_freeze_failed"


def _iso_now() -> str:
    return datetime.now(tz=UTC).isoformat(timespec="seconds")


def freeze_report_snapshot(
    session: Session,
    *,
    metric_snapshot_id: UUID,
    analysis_run_id: UUID | None = None,
) -> tuple[ReportSnapshot, ReportView]:
    # Serialize version allocation and lock before reading eligibility.
    snapshot = session.scalar(
        select(MetricSnapshot)
        .where(MetricSnapshot.id == metric_snapshot_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if snapshot is None or snapshot.status != "published":
        raise PublishingFreezeError("report requires a published metric snapshot")
    if analysis_run_id is not None:
        run = session.get(AnalysisRun, analysis_run_id)
    else:
        run = session.scalar(
            select(AnalysisRun)
            .where(AnalysisRun.metric_snapshot_id == snapshot.id, AnalysisRun.status == "published")
            .order_by(AnalysisRun.created_at.desc(), AnalysisRun.id.desc())
            .limit(1)
        )
    if run is None or run.status != "published" or run.metric_snapshot_id != snapshot.id:
        raise PublishingFreezeError(
            "report requires a published analysis run bound to its snapshot"
        )

    # Lock all findings in fixed order, then filter after refresh: a waiter must
    # never use pre-lock approval state. Review mutations acquire this same lock.
    findings = session.scalars(
        select(Finding)
        .where(Finding.analysis_run_id == run.id)
        .order_by(Finding.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).all()
    approved = [finding for finding in findings if finding.status == "approved"]
    if not approved:
        raise PublishingFreezeError("report requires at least one approved finding")
    for finding in approved:
        statuses = session.scalars(
            select(Evidence.status).where(Evidence.finding_id == finding.id)
        ).all()
        conclusion = session.scalar(
            select(Conclusion)
            .where(Conclusion.finding_id == finding.id)
            .execution_options(populate_existing=True)
        )
        if not statuses or any(status != "verified" for status in statuses):
            raise PublishingFreezeError("report requires every evidence row verified")
        if not conclusion_is_complete(conclusion):
            raise PublishingFreezeError("report requires a complete approved conclusion")

    existing = session.scalar(
        select(ReportSnapshot)
        .where(ReportSnapshot.metric_snapshot_id == snapshot.id)
        .order_by(ReportSnapshot.version.desc())
        .limit(1)
    )
    report = ReportSnapshot(
        id=uuid7(),
        metric_snapshot_id=snapshot.id,
        version=existing.version + 1 if existing else 1,
        title=f"FLOW 月度经营分析 · 快照 v{snapshot.version}",
        template_code=TEMPLATE_CODE,
    )
    view = _build_live_report_view(session, report, snapshot, run)
    if (
        existing is not None
        and existing.frozen_view is not None
        and _content_digest(build_report_view(session, existing)) == _content_digest(view)
    ):
        return existing, build_report_view(session, existing)

    report.frozen_view = {"schema_version": 1, "view": view_to_json(view)}
    session.add(report)
    session.flush()
    position = 0
    for frozen_finding in view.findings:
        for object_type, object_id in [
            *(("evidence", item) for item in frozen_finding.evidence_ids),
            ("finding", frozen_finding.finding_id),
        ]:
            position += 1
            session.add(
                ReportSnapshotItem(
                    report_snapshot_id=report.id,
                    position=position,
                    object_type=object_type,
                    object_id=object_id,
                )
            )
    session.flush()
    return report, view


def _content_digest(view: ReportView) -> str:
    payload = view_to_json(view)
    for field in ("report_snapshot_id", "report_version", "generated_at"):
        payload["identity"].pop(field)
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def build_report_view(session: Session, report: ReportSnapshot) -> ReportView:
    """Read only persisted frozen content; never reconstruct historical reports."""
    payload = report.frozen_view
    if not payload or payload.get("schema_version") != 1:
        raise PublishingFreezeError("report has no supported frozen content; 请重新冻结报告")
    try:
        view = view_from_json(payload["view"])
    except (KeyError, ValueError, TypeError) as error:
        raise PublishingFreezeError("invalid frozen report content") from error
    if (
        view.identity.report_snapshot_id != str(report.id)
        or view.identity.metric_snapshot_id != str(report.metric_snapshot_id)
        or view.identity.report_version != report.version
    ):
        raise PublishingFreezeError("frozen report identity mismatch")
    return view


def _build_live_report_view(
    session: Session,
    report: ReportSnapshot,
    snapshot: MetricSnapshot,
    run: AnalysisRun,
) -> ReportView:
    import_version = session.get(ImportVersion, run.import_version_id)
    if import_version is None:
        raise PublishingFreezeError("report lineage is missing its import version")

    definitions = {
        definition.id: definition
        for definition in session.scalars(
            select(MetricDefinition).where(
                MetricDefinition.metric_code.in_(
                    select(MetricDefinition.metric_code)
                    .join(
                        MetricValue,
                        MetricValue.metric_definition_id == MetricDefinition.id,
                    )
                    .where(MetricValue.metric_snapshot_id == snapshot.id)
                )
            )
        )
    }
    values = session.scalars(
        select(MetricValue).where(MetricValue.metric_snapshot_id == snapshot.id)
    ).all()

    current: dict[str, str] = {}
    budget: dict[str, str] = {}
    current_definitions: dict[str, MetricDefinition] = {}
    for value in values:
        definition = definitions.get(value.metric_definition_id)
        if definition is None:
            continue
        if value.comparison_type == "actual_month":
            current[str(definition.metric_code)] = str(value.value)
            current_definitions[str(definition.metric_code)] = definition
        elif value.comparison_type == "budget_month":
            budget[str(definition.metric_code)] = str(value.value)
    metrics = [
        SnapshotMetric(
            code=code,
            name=str(definition.name),
            formula=str(definition.formula),
            unit=str(definition.unit),
            definition_version=int(definition.version),
            comparison="current",
            period=None,
            value=value,
            budget=budget.get(code),
            variance=(str(Decimal(value) - Decimal(budget[code])) if code in budget else None),
        )
        for code, definition in current_definitions.items()
        for value in [current[code]]
    ]

    finding_rows = session.scalars(
        select(Finding)
        .where(
            Finding.analysis_run_id == run.id,
            Finding.status == "approved",
        )
        .order_by(Finding.total_score.desc(), Finding.id)
    ).all()
    snapshot_findings: list[SnapshotFinding] = []
    for finding in finding_rows:
        drivers = tuple(
            {
                "code": str(driver.driver_code),
                "amount": str(driver.contribution_amount),
                "ratio": (str(driver.contribution_ratio) if driver.contribution_ratio else ""),
                "method": driver.calculation_method or "",
            }
            for driver in session.scalars(
                select(DriverContribution)
                .where(DriverContribution.finding_id == finding.id)
                .order_by(DriverContribution.position)
            )
        )
        evidence_ids = tuple(
            str(item)
            for item in session.scalars(
                select(Evidence.id)
                .where(Evidence.finding_id == finding.id, Evidence.status == "verified")
                .order_by(Evidence.id)
            )
        )
        result = (
            session.get(AnalysisResult, finding.analysis_result_id)
            if finding.analysis_result_id
            else None
        )
        conclusion = session.scalar(select(Conclusion).where(Conclusion.finding_id == finding.id))
        snapshot_findings.append(
            SnapshotFinding(
                finding_id=str(finding.id),
                title=str(finding.title),
                finding_type=finding.finding_type,
                impact_amount=str(finding.impact_amount),
                status=str(finding.status),
                drivers=drivers,
                evidence_ids=evidence_ids,
                conclusion={
                    "verified_facts": conclusion.verified_facts if conclusion else "",
                    "analysis_judgment": conclusion.analysis_judgment if conclusion else "",
                    "open_questions": conclusion.open_questions if conclusion else "",
                    "recommendation": conclusion.recommendation if conclusion else "",
                    "playbook": str(result.playbook_code) if result else "",
                    "comparison": str(result.comparison_basis) if result else "",
                },
            )
        )

    quality = {"blocking": 0, "warning": 0}
    for issue in session.scalars(
        select(QualityIssue).where(QualityIssue.import_version_id == import_version.id)
    ):
        quality[issue.severity] = quality.get(issue.severity, 0) + 1
    reconciliations = [
        {
            "code": str(item.reconciliation_code),
            "passed": str(item.passed),
            "expected": item.expected_value or "",
            "actual": item.actual_value or "",
        }
        for item in session.scalars(
            select(ReconciliationResult).where(
                ReconciliationResult.import_version_id == import_version.id
            )
        )
    ]

    identity = SnapshotIdentity(
        batch_id=str(snapshot.batch_id),
        metric_snapshot_id=str(snapshot.id),
        analysis_run_id=str(run.id),
        report_snapshot_id=str(report.id),
        report_version=int(report.version),
        title=str(report.title),
        template_code=str(report.template_code),
        metric_engine_version=str(snapshot.engine_version),
        analysis_engine_version=str(run.engine_version),
        generated_at=_iso_now(),
    )
    return ReportView(
        identity=identity,
        metrics=tuple(sorted(metrics, key=lambda metric: metric.code)),
        findings=tuple(snapshot_findings),
        quality_summary=quality,
        reconciliations=tuple(sorted(reconciliations, key=lambda item: item["code"])),
    )


def digest_view(view: ReportView) -> str:
    payload = json.dumps(view.key_values(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = [
    "PublishingFreezeError",
    "TEMPLATE_CODE",
    "build_report_view",
    "digest_view",
    "freeze_report_snapshot",
]
