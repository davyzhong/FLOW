from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from flow_api.infrastructure.models.analytics import (
    MetricDefinition,
    MetricSnapshot,
    MetricValue,
)
from flow_api.metrics.calculator import MetricCalculator
from flow_api.metrics.decimal_math import MetricCalculationError
from flow_api.metrics.models import MetricCatalog
from flow_api.metrics.persistence import (
    MetricDefinitionConflictError,
    ensure_definition_dependencies,
    upsert_metric_definitions,
)
from flow_api.metrics.repositories import (
    MetricSourceRepository,
    MetricSourceUnavailableError,
)


class MetricSnapshotBlockedError(RuntimeError):
    def __init__(self, *reasons: str) -> None:
        self.reasons = tuple(reasons)
        super().__init__(", ".join(self.reasons))


class MetricSnapshotService:
    def __init__(self, repository: MetricSourceRepository | None = None) -> None:
        self.repository = repository or MetricSourceRepository()

    def create_snapshot(
        self,
        session: Session,
        *,
        batch_id: UUID,
        as_of_month: int,
        catalog: MetricCatalog,
        failure_hook: Callable[[], None] | None = None,
    ) -> MetricSnapshot:
        try:
            source = self.repository.get_published_source(session, batch_id)
            calculation = MetricCalculator(session, self.repository).calculate(
                source, catalog, as_of_month
            )
        except MetricSourceUnavailableError as error:
            raise MetricSnapshotBlockedError(error.code) from error
        except MetricCalculationError as error:
            raise MetricSnapshotBlockedError(error.code) from error

        existing = session.scalar(
            select(MetricSnapshot).where(
                MetricSnapshot.batch_id == batch_id,
                MetricSnapshot.import_version_id == source.import_version_id,
                MetricSnapshot.as_of_period_id == calculation.as_of_period_id,
                MetricSnapshot.engine_version == catalog.engine_version,
                MetricSnapshot.definition_set_id == catalog.definition_set_id,
                MetricSnapshot.definition_set_hash == calculation.definition_set_hash,
                MetricSnapshot.fingerprint == calculation.fingerprint,
                MetricSnapshot.status == "published",
            )
        )
        if existing is not None:
            return existing

        with session.begin_nested():
            definitions = upsert_metric_definitions(session, catalog)
            ensure_definition_dependencies(session, catalog, definitions)
            latest_version = session.scalar(
                select(func.max(MetricSnapshot.version)).where(
                    MetricSnapshot.batch_id == batch_id
                )
            )
            snapshot = MetricSnapshot(
                batch_id=batch_id,
                import_version_id=source.import_version_id,
                as_of_period_id=calculation.as_of_period_id,
                version=(latest_version or 0) + 1,
                engine_version=catalog.engine_version,
                definition_set_id=catalog.definition_set_id,
                definition_set_hash=calculation.definition_set_hash,
                fingerprint=calculation.fingerprint,
                status="building",
            )
            session.add(snapshot)
            session.flush()
            session.add_all(
                [
                    MetricValue(
                        metric_snapshot_id=snapshot.id,
                        metric_definition_id=definitions[value.metric_code].id,
                        comparison_type=value.comparison_type,
                        period_id=value.period_id,
                        organization_id=value.grain.organization_id,
                        customer_id=value.grain.customer_id,
                        customer_segment_id=value.grain.customer_segment_id,
                        logistics_product_id=value.grain.logistics_product_id,
                        region_id=value.grain.region_id,
                        value=value.persisted_value,
                        exact_value=str(value.exact_value),
                        calculation_trace={
                            "dependencies": [
                                {"metric_code": code, "exact_value": str(dependency)}
                                for code, dependency in value.dependency_values
                            ],
                            "source_fact_count": value.source_fact_count,
                        },
                    )
                    for value in calculation.values
                ]
            )
            session.flush()
            if failure_hook is not None:
                failure_hook()
            snapshot.status = "published"
            session.flush()
        return snapshot

    def get_snapshot_values(
        self, session: Session, snapshot_id: UUID
    ) -> tuple[MetricValue, ...]:
        return tuple(
            session.scalars(
                select(MetricValue)
                .join(MetricDefinition)
                .options(joinedload(MetricValue.metric_definition))
                .where(MetricValue.metric_snapshot_id == snapshot_id)
                .order_by(
                    MetricDefinition.metric_code,
                    MetricValue.comparison_type,
                    MetricValue.period_id,
                    MetricValue.organization_id.nulls_first(),
                    MetricValue.customer_id.nulls_first(),
                    MetricValue.customer_segment_id.nulls_first(),
                    MetricValue.logistics_product_id.nulls_first(),
                    MetricValue.region_id.nulls_first(),
                )
            )
        )


__all__ = [
    "MetricDefinitionConflictError",
    "MetricSnapshotBlockedError",
    "MetricSnapshotService",
]
