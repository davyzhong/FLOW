from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from flow_api.infrastructure.models.analytics import (
    MetricDefinition,
    MetricSnapshot,
    MetricValue,
)
from flow_api.infrastructure.models.intake import ImportVersion
from flow_api.metrics.repositories import MetricSourceRepository
from flow_api.metrics.source_rows import (
    ArSourceRow,
    FinancialSourceRow,
    OperatingSourceRow,
    PublishedMetricSource,
)

AnalysisSourceErrorCode = Literal[
    "snapshot_not_found",
    "snapshot_not_published",
    "import_not_found",
    "import_not_published",
    "snapshot_import_mismatch",
    "invalid_batch_metadata",
]


class AnalysisSourceUnavailableError(RuntimeError):
    def __init__(self, code: AnalysisSourceErrorCode, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class AnalysisSourceBundle:
    snapshot_id: UUID
    batch_id: UUID
    import_version_id: UUID
    source: PublishedMetricSource
    operating_rows: tuple[OperatingSourceRow, ...]
    financial_rows: tuple[FinancialSourceRow, ...]
    ar_rows: tuple[ArSourceRow, ...]
    metric_values: tuple[MetricValue, ...]
    source_digests: dict[str, str]


def _month_key(payload: dict[str, object], field: str) -> int:
    value = payload.get(field)
    if not isinstance(value, str) or len(value) != 7 or value[4] != "-":
        raise AnalysisSourceUnavailableError(
            "invalid_batch_metadata", f"bound import has invalid {field}"
        )
    try:
        month_key = int(value.replace("-", ""))
    except ValueError as error:
        raise AnalysisSourceUnavailableError(
            "invalid_batch_metadata", f"bound import has invalid {field}"
        ) from error
    if month_key % 100 not in range(1, 13):
        raise AnalysisSourceUnavailableError(
            "invalid_batch_metadata", f"bound import has invalid {field}"
        )
    return month_key


def _required_string(payload: dict[str, object], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise AnalysisSourceUnavailableError(
            "invalid_batch_metadata", f"bound import has invalid {field}"
        )
    return value


def _digest(rows: tuple[Any, ...]) -> str:
    payload = [asdict(row) for row in rows]
    canonical = json.dumps(payload, default=str, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class AnalysisSourceRepository:
    def __init__(self, metric_repository: MetricSourceRepository | None = None) -> None:
        self.metric_repository = metric_repository or MetricSourceRepository()

    def get_bound_source(
        self, session: Session, snapshot_id: UUID
    ) -> AnalysisSourceBundle:
        snapshot = session.get(MetricSnapshot, snapshot_id)
        if snapshot is None:
            raise AnalysisSourceUnavailableError(
                "snapshot_not_found", f"metric snapshot does not exist: {snapshot_id}"
            )
        if snapshot.status != "published":
            raise AnalysisSourceUnavailableError(
                "snapshot_not_published", "analysis requires a published metric snapshot"
            )
        import_version = session.get(ImportVersion, snapshot.import_version_id)
        if import_version is None:
            raise AnalysisSourceUnavailableError(
                "import_not_found", "snapshot-bound import version does not exist"
            )
        if import_version.status != "published":
            raise AnalysisSourceUnavailableError(
                "import_not_published", "snapshot-bound import was not published"
            )
        if import_version.batch_id != snapshot.batch_id:
            raise AnalysisSourceUnavailableError(
                "snapshot_import_mismatch",
                "snapshot and import version belong to different batches",
            )
        raw_batch = import_version.summary.get("batch")
        if not isinstance(raw_batch, dict):
            raise AnalysisSourceUnavailableError(
                "invalid_batch_metadata", "bound import has no batch metadata"
            )
        batch_payload = {str(key): value for key, value in raw_batch.items()}
        source = PublishedMetricSource(
            batch_id=snapshot.batch_id,
            import_version_id=import_version.id,
            analysis_start_month=_month_key(batch_payload, "analysis_start_month"),
            analysis_end_month=_month_key(batch_payload, "analysis_end_month"),
            comparison_start_month=_month_key(batch_payload, "comparison_start_month"),
            comparison_end_month=_month_key(batch_payload, "comparison_end_month"),
            actual_scenario_code=_required_string(batch_payload, "actual_scenario_code"),
            budget_scenario_code=_required_string(batch_payload, "budget_scenario_code"),
        )
        operating = self.metric_repository.operating_rows(session, source)
        financial = self.metric_repository.financial_rows(session, source)
        ar_rows = self.metric_repository.ar_rows(session, source)
        values = tuple(
            session.scalars(
                select(MetricValue)
                .join(MetricDefinition)
                .options(joinedload(MetricValue.metric_definition))
                .where(MetricValue.metric_snapshot_id == snapshot.id)
                .order_by(
                    MetricDefinition.metric_code,
                    MetricValue.comparison_type,
                    MetricValue.id,
                )
            )
        )
        return AnalysisSourceBundle(
            snapshot_id=snapshot.id,
            batch_id=snapshot.batch_id,
            import_version_id=import_version.id,
            source=source,
            operating_rows=operating,
            financial_rows=financial,
            ar_rows=ar_rows,
            metric_values=values,
            source_digests={
                "operating": _digest(operating),
                "financial": _digest(financial),
                "ar": _digest(ar_rows),
            },
        )


__all__ = [
    "AnalysisSourceBundle",
    "AnalysisSourceRepository",
    "AnalysisSourceUnavailableError",
]
