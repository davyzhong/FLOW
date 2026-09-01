from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from flow_api.infrastructure.models.analytics import MetricSnapshot
from flow_api.metrics.models import MetricCatalog
from flow_api.metrics.service import MetricSnapshotService

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


__all__ = ["DASHBOARD_MONTHS", "publish_dashboard_snapshot_series"]
