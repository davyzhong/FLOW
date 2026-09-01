from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.analysis.policy import load_analysis_policy
from flow_api.analysis.service import AnalysisRunService
from flow_api.data_contract.contract import load_contract
from flow_api.infrastructure.models.analytics import AnalysisRun, MetricSnapshot
from flow_api.infrastructure.models.intake import AnalysisBatch, QualityIssue
from flow_api.intake.detector import profile_workbook
from flow_api.intake.extractor import extract_candidate_package
from flow_api.intake.mapping import load_aliases, propose_mapping
from flow_api.intake.quality import evaluate_quality
from flow_api.intake.service import IntakeService
from flow_api.intake.source_storage import StoredSource
from flow_api.intake.transforms import load_transform_rules
from flow_api.metrics.catalog import load_metric_catalog
from flow_api.metrics.models import MetricCatalog
from flow_api.metrics.service import MetricSnapshotService

DEMO_BATCH_NAME = "FLOW Finance BP dashboard demo"
DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[5]

DASHBOARD_MONTHS = (
    202509,
    202510,
    202511,
    202512,
    202601,
    202602,
    202603,
    202604,
    202605,
    202606,
    202607,
    202608,
)


@dataclass(frozen=True)
class DashboardDemoPublication:
    batch_id: UUID
    import_version_id: UUID
    metric_snapshot_ids: tuple[UUID, ...]
    analysis_run_id: UUID


def publish_dashboard_snapshot_series(
    session: Session,
    *,
    batch_id: UUID,
    catalog: MetricCatalog,
    months: tuple[int, ...] = DASHBOARD_MONTHS,
) -> tuple[MetricSnapshot, ...]:
    service = MetricSnapshotService()
    return tuple(
        service.create_snapshot(
            session,
            batch_id=batch_id,
            as_of_month=month,
            catalog=catalog,
        )
        for month in months
    )


def _publish_demo_import(session: Session, repository_root: Path) -> AnalysisBatch:
    workbook_path = (
        repository_root / "fixtures/workbooks/external_logistics_nonstandard_v1.xlsx"
    )
    content = workbook_path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    contract = load_contract(repository_root / "templates/excel/flow_v1_contract.yaml")
    aliases = load_aliases(repository_root / "config/intake/flow_v1_aliases.yaml")
    transforms = load_transform_rules(
        repository_root / "config/intake/flow_v1_transforms.yaml"
    )
    profile = profile_workbook(content)
    proposal = propose_mapping(profile, contract, aliases)
    candidate = extract_candidate_package(
        content, profile, proposal, contract, transforms
    )
    report = evaluate_quality(candidate.package, contract, proposal)
    stored = StoredSource(
        sha256=digest,
        object_key=f"raw/{digest[:2]}/{digest}",
        size_bytes=len(content),
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        original_filename=workbook_path.name,
    )
    service = IntakeService(session)
    batch = service.create_batch(
        DEMO_BATCH_NAME,
        description="Deterministic governed demo for the Finance BP dashboard.",
    )
    source = service.attach_source(batch.id, stored)
    mapping = service.propose_mapping(source.id, proposal)
    version = service.validate_import(source.id, mapping.id, candidate, report)
    for issue in session.scalars(
        select(QualityIssue).where(
            QualityIssue.import_version_id == version.id,
            QualityIssue.severity == "warning",
        )
    ):
        service.acknowledge_warning(
            issue.id,
            actor="flow.dashboard.demo",
            reason="Deterministic fixture warning reviewed for dashboard acceptance.",
        )
    service.publish_import(version.id)
    session.flush()
    return batch


def bootstrap_dashboard_demo(
    session: Session,
    *,
    repository_root: Path = DEFAULT_REPOSITORY_ROOT,
) -> DashboardDemoPublication:
    batch = session.scalar(
        select(AnalysisBatch)
        .where(
            AnalysisBatch.name == DEMO_BATCH_NAME,
            AnalysisBatch.status == "published",
        )
        .order_by(AnalysisBatch.created_at.desc(), AnalysisBatch.id.desc())
        .limit(1)
    )
    if batch is None:
        batch = _publish_demo_import(session, repository_root)

    published_import = next(
        (version for version in batch.import_versions if version.is_published),
        None,
    )
    if published_import is None:
        raise RuntimeError("dashboard demo batch has no published import")

    catalog = load_metric_catalog(
        repository_root / "config/metrics/flow_v1_metrics.yaml"
    )
    snapshots = publish_dashboard_snapshot_series(
        session,
        batch_id=batch.id,
        catalog=catalog,
    )
    analysis_policy = load_analysis_policy(
        repository_root / "services/api/config/analysis/flow-logistics-v1.yaml"
    )
    run: AnalysisRun = AnalysisRunService().create_run(
        session,
        snapshot_id=snapshots[-1].id,
        loaded_policy=analysis_policy,
    )
    session.flush()
    return DashboardDemoPublication(
        batch_id=batch.id,
        import_version_id=published_import.id,
        metric_snapshot_ids=tuple(snapshot.id for snapshot in snapshots),
        analysis_run_id=run.id,
    )


__all__ = [
    "DASHBOARD_MONTHS",
    "DashboardDemoPublication",
    "bootstrap_dashboard_demo",
    "publish_dashboard_snapshot_series",
]
