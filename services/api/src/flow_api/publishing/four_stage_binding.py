"""publishing 家族与 §7 四阶段 ABI 的绑定：冻结资源校验器注册。

路由与测试共用本模块，保证 `report_snapshot` 资源校验器只有一份注册点。
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from flow_api.publication.four_stage import (
    PublicationFreezeConflict,
    PublicationNotFound,
    VerifiedResource,
    register_resource_verifier,
)
from flow_api.publishing.service import PublishingFreezeError, build_report_view


def _enterprise_of_report_snapshot(session: Session, report: Any) -> UUID | None:
    from flow_api.enterprise.models import AnalysisCycle
    from flow_api.infrastructure.models.analytics import MetricSnapshot
    from flow_api.infrastructure.models.intake import AnalysisBatch

    snapshot = session.get(MetricSnapshot, report.metric_snapshot_id)
    if snapshot is None or snapshot.batch_id is None:
        return None
    batch = session.get(AnalysisBatch, snapshot.batch_id)
    if batch is None or batch.analysis_cycle_id is None:
        return None
    cycle = session.get(AnalysisCycle, batch.analysis_cycle_id)
    return cycle.enterprise_id if cycle else None


def _verify_report_snapshot(session: Session, resource_id: UUID) -> VerifiedResource:
    from flow_api.infrastructure.models.publishing import ReportSnapshot

    report = session.get(ReportSnapshot, resource_id)
    if report is None:
        raise PublicationNotFound(f"report snapshot does not exist: {resource_id}")
    try:
        build_report_view(session, report)
    except PublishingFreezeError as error:
        raise PublicationFreezeConflict(str(error)) from error
    frozen = report.frozen_view or {}
    view_payload = frozen.get("view") if isinstance(frozen, dict) else None
    if not isinstance(view_payload, dict):
        raise PublicationFreezeConflict("report snapshot has no frozen view payload")
    return VerifiedResource(
        canonical_payload=view_payload,
        scope="enterprise",
        enterprise_id=_enterprise_of_report_snapshot(session, report),
    )


register_resource_verifier("report_snapshot", _verify_report_snapshot)

__all__ = ["_enterprise_of_report_snapshot"]
