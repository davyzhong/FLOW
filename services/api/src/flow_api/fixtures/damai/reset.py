"""Transaction-scoped cleanup for the Damai synthetic business batch."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, or_, select, text, update
from sqlalchemy.orm import Session

from flow_api.enterprise.models import AnalysisCycle
from flow_api.infrastructure.models.analytics import (
    AnalysisRun,
    Finding,
    MetricSnapshot,
    ReviewEvent,
)
from flow_api.infrastructure.models.canonical import (
    FactArCollection,
    FactBudget,
    FactFinancialActual,
    FactOperatingActual,
)
from flow_api.infrastructure.models.cockpit import ActionItem
from flow_api.infrastructure.models.intake import AnalysisBatch, ImportVersion
from flow_api.infrastructure.models.publishing import ReportSnapshot
from flow_api.security.models import AuditEvent


def _repository_root() -> Path:
    for root in (Path.cwd(), *Path.cwd().parents):
        if (root / "templates/excel/flow_v1_contract.yaml").is_file():
            return root
    raise FileNotFoundError("未找到 FLOW 仓库根目录")


def reset_damai_business_data(session: Session, enterprise_id: UUID) -> dict[str, int]:
    """Execute the package SQL reset within the caller's transaction.

    The SQL targets only the named Damai batch joined through this enterprise's cycle.
    System dictionaries, enterprise/cycle rows, statement publication history, audit
    events, and shared stored objects are retained. The caller rolls back if reseeding
    or subsequent verification fails.
    """
    if session.get_bind().dialect.name == "sqlite":
        return _reset_sqlite_business_data(session, enterprise_id)

    connection = session.connection()
    from flow_api.settings import get_settings

    connection.execute(
        text("SELECT set_config('flow.target_enterprise_id', :enterprise_id, true)"),
        {"enterprise_id": str(enterprise_id)},
    )
    connection.execute(
        text("SELECT set_config('flow.audit_retention_days', :retention_days, true)"),
        {"retention_days": str(get_settings().flow_audit_retention_days)},
    )
    sql_path = _repository_root() / "data/enterprise/damai-logistics/v2/sql/20_business_reset.sql"
    source = sql_path.read_text(encoding="utf-8")
    statements = []
    for fragment in source.split(";"):
        statement = "\n".join(
            line for line in fragment.splitlines() if not line.lstrip().startswith("--")
        ).strip()
        if statement:
            statements.append(statement)
    if not statements:
        raise RuntimeError("企业业务重置 SQL 为空")
    for statement in statements:
        connection.exec_driver_sql(statement)
    row = connection.exec_driver_sql(
        "SELECT batches, imports, snapshots, cycles_reopened, review_events_archived "
        "FROM _damai_reset_counts"
    ).one()
    return {
        "batches_deleted": int(row.batches),
        "imports_deleted": int(row.imports),
        "snapshots_deleted": int(row.snapshots),
        "cycles_reopened": int(row.cycles_reopened),
        "review_events_archived": int(row.review_events_archived),
    }


def _reset_sqlite_business_data(session: Session, enterprise_id: UUID) -> dict[str, int]:
    """在 SQLite 中按相同数据边界重置业务账套并归档审核历史。"""

    batch_ids = list(
        session.scalars(
            select(AnalysisBatch.id)
            .join(AnalysisCycle, AnalysisCycle.id == AnalysisBatch.analysis_cycle_id)
            .where(
                AnalysisCycle.enterprise_id == enterprise_id,
                AnalysisBatch.name == "damai-demo-v1",
            )
        )
    )
    import_ids = list(
        session.scalars(select(ImportVersion.id).where(ImportVersion.batch_id.in_(batch_ids)))
    ) if batch_ids else []
    snapshot_ids = list(
        session.scalars(select(MetricSnapshot.id).where(MetricSnapshot.batch_id.in_(batch_ids)))
    ) if batch_ids else []
    run_query = select(AnalysisRun.id).where(
        or_(
            AnalysisRun.import_version_id.in_(import_ids),
            AnalysisRun.metric_snapshot_id.in_(snapshot_ids),
        )
    )
    run_ids = list(session.scalars(run_query))
    finding_query = select(Finding.id).where(
        or_(
            Finding.analysis_run_id.in_(run_ids),
            Finding.metric_snapshot_id.in_(snapshot_ids),
        )
    )
    finding_ids = list(session.scalars(finding_query))
    reviews = list(
        session.scalars(select(ReviewEvent).where(ReviewEvent.finding_id.in_(finding_ids)))
    ) if finding_ids else []
    now = datetime.now(UTC)
    from flow_api.settings import get_settings

    retain_until = now + timedelta(days=get_settings().flow_audit_retention_days)
    for review in reviews:
        event_id = str(review.id)
        session.add(
            AuditEvent(
                event_type="finding.review_history.archived",
                actor_id=review.reviewer[:128],
                actor_role=None,
                enterprise_id=enterprise_id,
                resource_scope="enterprise",
                resource_type="finding_review_event",
                resource_id=str(review.finding_id),
                action="enterprise.business.reset",
                decision="allow",
                reason_code=f"enterprise-reset:{event_id}"[:64],
                correlation_id=f"enterprise-reset:{event_id}"[:128],
                request_id=f"enterprise-reset:{event_id}"[:128],
                redacted_metadata={
                    "source_event_id": event_id,
                    "finding_id": str(review.finding_id),
                    "sequence": review.sequence,
                    "reviewer": review.reviewer,
                    "decision": review.decision,
                    "comment": review.comment,
                    "source_created_at": review.created_at.isoformat(),
                },
                artifact_refs=[],
                created_at=now,
                retention_class="security_default",
                retain_until=retain_until,
            )
        )

    if finding_ids or snapshot_ids:
        action_filter = []
        if finding_ids:
            action_filter.append(ActionItem.finding_id.in_(finding_ids))
        if snapshot_ids:
            action_filter.append(ActionItem.snapshot_id.in_(snapshot_ids))
        session.execute(delete(ActionItem).where(or_(*action_filter)))
    if snapshot_ids:
        session.execute(
            delete(ReportSnapshot).where(ReportSnapshot.metric_snapshot_id.in_(snapshot_ids))
        )
    if run_ids:
        session.execute(delete(AnalysisRun).where(AnalysisRun.id.in_(run_ids)))
    if import_ids:
        for model in (FactArCollection, FactBudget, FactFinancialActual, FactOperatingActual):
            session.execute(delete(model).where(model.import_version_id.in_(import_ids)))
    if snapshot_ids:
        session.execute(delete(MetricSnapshot).where(MetricSnapshot.id.in_(snapshot_ids)))
    if import_ids:
        session.execute(delete(ImportVersion).where(ImportVersion.id.in_(import_ids)))
    if batch_ids:
        session.execute(delete(AnalysisBatch).where(AnalysisBatch.id.in_(batch_ids)))

    cycle_filter = (
        AnalysisCycle.enterprise_id == enterprise_id,
        AnalysisCycle.period_key == "2023-03",
        AnalysisCycle.status != "open",
    )
    cycles_reopened = len(
        list(session.scalars(select(AnalysisCycle.id).where(*cycle_filter)))
    )
    if cycles_reopened:
        session.execute(
            update(AnalysisCycle).where(*cycle_filter).values(status="open")
        )
    session.flush()
    return {
        "batches_deleted": len(batch_ids),
        "imports_deleted": len(import_ids),
        "snapshots_deleted": len(snapshot_ids),
        "cycles_reopened": cycles_reopened,
        "review_events_archived": len(reviews),
    }


__all__ = ["reset_damai_business_data"]
