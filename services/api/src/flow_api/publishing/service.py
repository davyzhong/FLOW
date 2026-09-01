"""Freeze and render Report Snapshots."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.analytics import (
    AnalysisResult,
    AnalysisRun,
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
from flow_api.publishing.models import (
    ReportView,
    SnapshotFinding,
    SnapshotIdentity,
    SnapshotMetric,
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
    snapshot = session.get(MetricSnapshot, metric_snapshot_id)
    if snapshot is None or snapshot.status != "published":
        raise PublishingFreezeError("report requires a published metric snapshot")
    run = session.get(AnalysisRun, analysis_run_id) if analysis_run_id else None
    if run is None:
        run = session.scalar(
            select(AnalysisRun)
            .where(
                AnalysisRun.metric_snapshot_id == snapshot.id,
                AnalysisRun.status == "published",
            )
            .order_by(AnalysisRun.created_at.desc())
            .limit(1)
        )
    if run is None:
        raise PublishingFreezeError("report requires a published analysis run")

    approved = session.scalars(
        select(Finding)
        .where(Finding.analysis_run_id == run.id, Finding.status == "approved")
        .order_by(Finding.total_score.desc())
    ).all()
    if not approved:
        raise PublishingFreezeError(
            "report requires at least one approved finding; "
            "complete evidence review and approval first"
        )

    existing = session.scalar(
        select(ReportSnapshot)
        .where(ReportSnapshot.metric_snapshot_id == snapshot.id)
        .order_by(ReportSnapshot.version.desc())
        .limit(1)
    )
    version = (existing.version + 1) if existing is not None else 1
    if existing is not None and existing.template_code == TEMPLATE_CODE:
        items_exist = session.scalar(
            select(ReportSnapshotItem.id)
            .where(ReportSnapshotItem.report_snapshot_id == existing.id)
            .limit(1)
        )
        if items_exist is not None:
            return existing, build_report_view(session, existing)

    report = ReportSnapshot(
        metric_snapshot_id=snapshot.id,
        version=version,
        title=f"FLOW 月度经营分析 · 快照 v{snapshot.version}",
        template_code=TEMPLATE_CODE,
    )
    session.add(report)
    session.flush()

    position = 0
    for finding in approved:
        for evidence_id in [
            str(item)
            for item in session.scalars(
                select(Evidence.id).where(Evidence.finding_id == finding.id)
            )
        ]:
            position += 1
            session.add(
                ReportSnapshotItem(
                    report_snapshot=report,
                    position=position,
                    object_type="evidence",
                    object_id=evidence_id,
                )
            )
        position += 1
        session.add(
            ReportSnapshotItem(
                report_snapshot=report,
                position=position,
                object_type="finding",
                object_id=str(finding.id),
            )
        )
    session.flush()
    return report, build_report_view(session, report)


def build_report_view(session: Session, report: ReportSnapshot) -> ReportView:
    snapshot = session.get(MetricSnapshot, report.metric_snapshot_id)
    if snapshot is None:
        raise PublishingFreezeError("report snapshot lost its metric snapshot")
    run = session.scalar(
        select(AnalysisRun)
        .where(AnalysisRun.metric_snapshot_id == snapshot.id, AnalysisRun.status == "published")
        .order_by(AnalysisRun.created_at.desc())
        .limit(1)
    )
    if run is None:
        raise PublishingFreezeError("report snapshot has no published analysis run")
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
            variance=(
                str(Decimal(value) - Decimal(budget[code]))
                if code in budget
                else None
            ),
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
        .order_by(Finding.total_score.desc())
    ).all()
    snapshot_findings: list[SnapshotFinding] = []
    for finding in finding_rows:
        drivers = tuple(
            {
                "code": str(driver.driver_code),
                "amount": str(driver.contribution_amount),
                "ratio": (
                    str(driver.contribution_ratio) if driver.contribution_ratio else ""
                ),
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
                select(Evidence.id).where(
                    Evidence.finding_id == finding.id, Evidence.status == "verified"
                )
            )
        )
        result = (
            session.get(AnalysisResult, finding.analysis_result_id)
            if finding.analysis_result_id
            else None
        )
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
        metrics=tuple(metrics),
        findings=tuple(snapshot_findings),
        quality_summary=quality,
        reconciliations=tuple(reconciliations),
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
