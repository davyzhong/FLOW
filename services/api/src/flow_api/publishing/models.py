"""Frozen, renderer-facing view of a Report Snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class SnapshotMetric:
    code: str
    name: str
    formula: str
    unit: str
    definition_version: int
    comparison: str
    period: str | None
    value: str
    budget: str | None = None
    variance: str | None = None


@dataclass(frozen=True, slots=True)
class SnapshotFinding:
    finding_id: str
    title: str
    finding_type: str | None
    impact_amount: str
    status: str
    conclusion: dict[str, str] = field(default_factory=dict)
    drivers: tuple[dict[str, str], ...] = ()
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SnapshotIdentity:
    batch_id: str
    metric_snapshot_id: str
    analysis_run_id: str
    report_snapshot_id: str
    report_version: int
    title: str
    template_code: str
    metric_engine_version: str
    analysis_engine_version: str
    generated_at: str


@dataclass(frozen=True, slots=True)
class ReportView:
    identity: SnapshotIdentity
    metrics: tuple[SnapshotMetric, ...]
    findings: tuple[SnapshotFinding, ...]
    quality_summary: dict[str, int]
    reconciliations: tuple[dict[str, str], ...]

    def identity_footer(self) -> dict[str, str]:
        return {
            "报告版本": f"v{self.identity.report_version}",
            "数据批次": self.identity.batch_id,
            "指标快照": self.identity.metric_snapshot_id,
            "分析运行": self.identity.analysis_run_id,
            "指标引擎": self.identity.metric_engine_version,
            "分析引擎": self.identity.analysis_engine_version,
            "生成时间": self.identity.generated_at,
        }

    def key_values(self) -> dict[str, str]:
        """Canonical key values every rendered format must contain."""
        values: dict[str, str] = {
            "report_version": f"v{self.identity.report_version}",
            "batch_id": self.identity.batch_id,
            "metric_snapshot_id": self.identity.metric_snapshot_id,
            "analysis_run_id": self.identity.analysis_run_id,
        }
        for metric in self.metrics:
            values[f"metric:{metric.code}:{metric.comparison}"] = metric.value
        for finding in self.findings:
            values[f"finding:{finding.finding_id}:impact"] = finding.impact_amount
        return values


def view_to_json(view: ReportView) -> dict[str, Any]:
    import dataclasses

    return dataclasses.asdict(view)


def view_from_json(payload: dict[str, Any]) -> ReportView:
    from pydantic import TypeAdapter

    return TypeAdapter(ReportView).validate_python(payload)


__all__ = [
    "ReportView",
    "SnapshotFinding",
    "SnapshotIdentity",
    "SnapshotMetric",
    "view_to_json",
    "view_from_json",
]
