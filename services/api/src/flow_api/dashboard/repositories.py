from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.analytics import (
    AnalysisDriver,
    AnalysisResult,
    AnalysisRun,
    DriverContribution,
    Evidence,
    Finding,
    FindingScoreComponent,
    MetricDefinition,
    MetricSnapshot,
    MetricValue,
)
from flow_api.infrastructure.models.canonical import (
    Customer,
    CustomerSegment,
    LogisticsProduct,
    Organization,
    Period,
    Region,
)
from flow_api.infrastructure.models.intake import (
    AnalysisBatch,
    ImportVersion,
    QualityIssue,
    ReconciliationResult,
    WarningAcknowledgement,
)

DashboardSourceErrorCode = Literal[
    "no_published_run",
    "run_not_found",
    "run_not_published",
    "snapshot_not_found",
    "snapshot_not_published",
    "import_not_found",
    "import_not_published",
    "batch_not_found",
    "batch_not_published",
    "period_not_found",
    "run_snapshot_mismatch",
    "run_import_mismatch",
    "snapshot_import_mismatch",
]


class DashboardSourceUnavailableError(RuntimeError):
    def __init__(self, code: DashboardSourceErrorCode, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class PublishedMetricValue:
    value: MetricValue
    definition: MetricDefinition
    period: Period | None
    organization: Organization | None
    customer: Customer | None
    customer_segment: CustomerSegment | None
    logistics_product: LogisticsProduct | None
    region: Region | None


@dataclass(frozen=True, slots=True)
class PublishedAnalysisResult:
    result: AnalysisResult
    drivers: tuple[AnalysisDriver, ...]

    @property
    def playbook_code(self) -> str:
        return self.result.playbook_code


@dataclass(frozen=True, slots=True)
class PublishedFinding:
    finding: Finding
    drivers: tuple[DriverContribution, ...]
    score_components: tuple[FindingScoreComponent, ...]
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True, slots=True)
class DashboardDimensionOptions:
    organizations: tuple[Organization, ...]
    customer_segments: tuple[CustomerSegment, ...]
    logistics_products: tuple[LogisticsProduct, ...]
    regions: tuple[Region, ...]


@dataclass(frozen=True, slots=True)
class DashboardQualitySummary:
    blocking_issue_count: int
    warning_issue_count: int
    acknowledged_warning_count: int
    reconciliation_status: Literal["passed", "failed", "not_available"]


@dataclass(frozen=True, slots=True)
class DashboardTrendMetric:
    metric_code: str
    exact_value: str


@dataclass(frozen=True, slots=True)
class DashboardTrendSourcePoint:
    snapshot_id: UUID
    month_key: int
    metrics: tuple[DashboardTrendMetric, ...]


@dataclass(frozen=True, slots=True)
class DashboardSourceBundle:
    run: AnalysisRun
    snapshot: MetricSnapshot
    import_version: ImportVersion
    batch: AnalysisBatch
    as_of_period: Period
    metric_values: tuple[PublishedMetricValue, ...]
    analysis_results: tuple[PublishedAnalysisResult, ...]
    findings: tuple[PublishedFinding, ...]
    dimension_options: DashboardDimensionOptions
    quality: DashboardQualitySummary


class DashboardSourceRepository:
    """Read-only projection source constrained to governed published tables."""

    def get_latest(self, session: Session) -> DashboardSourceBundle:
        run_id = session.scalar(
            select(AnalysisRun.id)
            .join(MetricSnapshot, MetricSnapshot.id == AnalysisRun.metric_snapshot_id)
            .join(Period, Period.id == MetricSnapshot.as_of_period_id)
            .where(
                AnalysisRun.status == "published",
                MetricSnapshot.status == "published",
            )
            .order_by(
                Period.month_key.desc(),
                AnalysisRun.created_at.desc(),
                AnalysisRun.id.desc(),
            )
            .limit(1)
        )
        if run_id is None:
            raise DashboardSourceUnavailableError(
                "no_published_run", "no published analysis run is available"
            )
        return self.get_by_run_id(session, run_id)

    def get_by_run_id(
        self, session: Session, run_id: UUID
    ) -> DashboardSourceBundle:
        run = session.get(AnalysisRun, run_id)
        if run is None:
            raise DashboardSourceUnavailableError(
                "run_not_found", f"analysis run does not exist: {run_id}"
            )
        if run.status != "published":
            raise DashboardSourceUnavailableError(
                "run_not_published", "dashboard requires a published analysis run"
            )

        snapshot = session.get(MetricSnapshot, run.metric_snapshot_id)
        if snapshot is None:
            raise DashboardSourceUnavailableError(
                "snapshot_not_found", "analysis-run snapshot does not exist"
            )
        if snapshot.id != run.metric_snapshot_id:
            raise DashboardSourceUnavailableError(
                "run_snapshot_mismatch", "analysis run is bound to a different snapshot"
            )
        if snapshot.status != "published":
            raise DashboardSourceUnavailableError(
                "snapshot_not_published", "analysis-run snapshot is not published"
            )

        import_version = session.get(ImportVersion, run.import_version_id)
        if import_version is None:
            raise DashboardSourceUnavailableError(
                "import_not_found", "analysis-run import version does not exist"
            )
        if run.import_version_id != snapshot.import_version_id:
            raise DashboardSourceUnavailableError(
                "run_import_mismatch", "analysis run and snapshot imports do not match"
            )
        if import_version.id != snapshot.import_version_id:
            raise DashboardSourceUnavailableError(
                "snapshot_import_mismatch", "snapshot is bound to a different import"
            )
        if import_version.status != "published" or not import_version.is_published:
            raise DashboardSourceUnavailableError(
                "import_not_published", "analysis-run import is not published"
            )
        if snapshot.batch_id != import_version.batch_id:
            raise DashboardSourceUnavailableError(
                "snapshot_import_mismatch",
                "snapshot and import belong to different batches",
            )

        batch = session.get(AnalysisBatch, snapshot.batch_id)
        if batch is None:
            raise DashboardSourceUnavailableError(
                "batch_not_found", "analysis-run batch does not exist"
            )
        if batch.status != "published":
            raise DashboardSourceUnavailableError(
                "batch_not_published", "analysis-run batch is not published"
            )
        period = session.get(Period, snapshot.as_of_period_id)
        if period is None:
            raise DashboardSourceUnavailableError(
                "period_not_found", "analysis-run as-of period does not exist"
            )

        return DashboardSourceBundle(
            run=run,
            snapshot=snapshot,
            import_version=import_version,
            batch=batch,
            as_of_period=period,
            metric_values=self._metric_values(session, snapshot.id),
            analysis_results=self._analysis_results(session, run.id),
            findings=self._findings(session, run.id),
            dimension_options=self._dimension_options(session),
            quality=self._quality(session, import_version.id),
        )

    def get_snapshot_series(
        self, session: Session, bundle: DashboardSourceBundle
    ) -> tuple[DashboardTrendSourcePoint, ...]:
        start_month = self._shift_month(bundle.as_of_period.month_key, -11)
        rows = tuple(
            session.execute(
                select(MetricSnapshot, Period)
                .join(Period, Period.id == MetricSnapshot.as_of_period_id)
                .where(
                    MetricSnapshot.status == "published",
                    MetricSnapshot.batch_id == bundle.snapshot.batch_id,
                    MetricSnapshot.import_version_id
                    == bundle.snapshot.import_version_id,
                    MetricSnapshot.definition_set_hash
                    == bundle.snapshot.definition_set_hash,
                    MetricSnapshot.engine_version == bundle.snapshot.engine_version,
                    Period.month_key.between(
                        start_month, bundle.as_of_period.month_key
                    ),
                )
                .order_by(Period.month_key, MetricSnapshot.version.desc())
            ).tuples()
        )
        latest_by_month: dict[int, MetricSnapshot] = {}
        for snapshot, period in rows:
            latest_by_month.setdefault(period.month_key, snapshot)
        snapshot_ids = tuple(snapshot.id for snapshot in latest_by_month.values())
        if not snapshot_ids:
            return ()
        values = tuple(
            session.execute(
                select(MetricValue, MetricDefinition)
                .join(
                    MetricDefinition,
                    MetricDefinition.id == MetricValue.metric_definition_id,
                )
                .where(
                    MetricValue.metric_snapshot_id.in_(snapshot_ids),
                    MetricValue.comparison_type == "actual_month",
                    MetricValue.organization_id.is_(None),
                    MetricValue.customer_id.is_(None),
                    MetricValue.customer_segment_id.is_(None),
                    MetricValue.logistics_product_id.is_(None),
                    MetricValue.region_id.is_(None),
                    MetricDefinition.metric_code.in_(
                        (
                            "revenue",
                            "operating_profit",
                            "gross_margin",
                            "operating_cash_flow",
                        )
                    ),
                )
                .order_by(
                    MetricValue.metric_snapshot_id,
                    MetricDefinition.metric_code,
                )
            ).tuples()
        )
        by_snapshot: dict[UUID, list[DashboardTrendMetric]] = {}
        for value, definition in values:
            by_snapshot.setdefault(value.metric_snapshot_id, []).append(
                DashboardTrendMetric(
                    metric_code=definition.metric_code,
                    exact_value=value.exact_value,
                )
            )
        return tuple(
            DashboardTrendSourcePoint(
                snapshot_id=snapshot.id,
                month_key=month_key,
                metrics=tuple(by_snapshot.get(snapshot.id, ())),
            )
            for month_key, snapshot in sorted(latest_by_month.items())
        )

    @staticmethod
    def _shift_month(month_key: int, offset: int) -> int:
        year, month = divmod(month_key, 100)
        absolute = year * 12 + month - 1 + offset
        shifted_year, shifted_month = divmod(absolute, 12)
        return shifted_year * 100 + shifted_month + 1

    @staticmethod
    def _metric_values(
        session: Session, snapshot_id: UUID
    ) -> tuple[PublishedMetricValue, ...]:
        rows = session.execute(
            select(
                MetricValue,
                MetricDefinition,
                Period,
                Organization,
                Customer,
                CustomerSegment,
                LogisticsProduct,
                Region,
            )
            .join(
                MetricDefinition,
                MetricDefinition.id == MetricValue.metric_definition_id,
            )
            .outerjoin(Period, Period.id == MetricValue.period_id)
            .outerjoin(Organization, Organization.id == MetricValue.organization_id)
            .outerjoin(Customer, Customer.id == MetricValue.customer_id)
            .outerjoin(
                CustomerSegment,
                CustomerSegment.id == MetricValue.customer_segment_id,
            )
            .outerjoin(
                LogisticsProduct,
                LogisticsProduct.id == MetricValue.logistics_product_id,
            )
            .outerjoin(Region, Region.id == MetricValue.region_id)
            .where(MetricValue.metric_snapshot_id == snapshot_id)
            .order_by(
                MetricDefinition.metric_code,
                MetricValue.comparison_type,
                Period.month_key.nulls_last(),
                Organization.code.nulls_last(),
                Customer.code.nulls_last(),
                CustomerSegment.code.nulls_last(),
                LogisticsProduct.code.nulls_last(),
                Region.code.nulls_last(),
                MetricValue.id,
            )
        )
        return tuple(PublishedMetricValue(*row) for row in rows.tuples())

    @staticmethod
    def _analysis_results(
        session: Session, run_id: UUID
    ) -> tuple[PublishedAnalysisResult, ...]:
        results = tuple(
            session.scalars(
                select(AnalysisResult)
                .where(AnalysisResult.analysis_run_id == run_id)
                .order_by(AnalysisResult.playbook_code, AnalysisResult.id)
            )
        )
        drivers = tuple(
            session.scalars(
                select(AnalysisDriver)
                .join(AnalysisResult)
                .where(AnalysisResult.analysis_run_id == run_id)
                .order_by(
                    AnalysisDriver.analysis_result_id,
                    AnalysisDriver.position,
                    AnalysisDriver.id,
                )
            )
        )
        by_result: dict[UUID, list[AnalysisDriver]] = {}
        for driver in drivers:
            by_result.setdefault(driver.analysis_result_id, []).append(driver)
        return tuple(
            PublishedAnalysisResult(result, tuple(by_result.get(result.id, ())))
            for result in results
        )

    @staticmethod
    def _findings(session: Session, run_id: UUID) -> tuple[PublishedFinding, ...]:
        findings = tuple(
            session.scalars(
                select(Finding)
                .where(Finding.analysis_run_id == run_id)
                .order_by(
                    Finding.total_score.desc().nulls_last(),
                    func.abs(Finding.impact_amount).desc(),
                    Finding.id,
                )
            )
        )
        finding_ids = tuple(finding.id for finding in findings)
        if not finding_ids:
            return ()
        drivers = tuple(
            session.scalars(
                select(DriverContribution)
                .where(DriverContribution.finding_id.in_(finding_ids))
                .order_by(
                    DriverContribution.finding_id,
                    DriverContribution.position,
                    DriverContribution.id,
                )
            )
        )
        scores = tuple(
            session.scalars(
                select(FindingScoreComponent)
                .where(FindingScoreComponent.finding_id.in_(finding_ids))
                .order_by(
                    FindingScoreComponent.finding_id,
                    FindingScoreComponent.component_code,
                    FindingScoreComponent.id,
                )
            )
        )
        evidence = tuple(
            session.scalars(
                select(Evidence)
                .where(Evidence.finding_id.in_(finding_ids))
                .order_by(
                    Evidence.finding_id,
                    Evidence.evidence_type,
                    Evidence.object_type,
                    Evidence.object_id,
                    Evidence.id,
                )
            )
        )
        driver_map: dict[UUID, list[DriverContribution]] = {}
        score_map: dict[UUID, list[FindingScoreComponent]] = {}
        evidence_map: dict[UUID, list[Evidence]] = {}
        for driver in drivers:
            driver_map.setdefault(driver.finding_id, []).append(driver)
        for score in scores:
            score_map.setdefault(score.finding_id, []).append(score)
        for evidence_item in evidence:
            evidence_map.setdefault(evidence_item.finding_id, []).append(evidence_item)
        return tuple(
            PublishedFinding(
                finding=finding,
                drivers=tuple(driver_map.get(finding.id, ())),
                score_components=tuple(score_map.get(finding.id, ())),
                evidence=tuple(evidence_map.get(finding.id, ())),
            )
            for finding in findings
        )

    @staticmethod
    def _dimension_options(session: Session) -> DashboardDimensionOptions:
        return DashboardDimensionOptions(
            organizations=tuple(
                session.scalars(select(Organization).order_by(Organization.code))
            ),
            customer_segments=tuple(
                session.scalars(
                    select(CustomerSegment).order_by(CustomerSegment.code)
                )
            ),
            logistics_products=tuple(
                session.scalars(
                    select(LogisticsProduct).order_by(LogisticsProduct.code)
                )
            ),
            regions=tuple(session.scalars(select(Region).order_by(Region.code))),
        )

    @staticmethod
    def _quality(session: Session, import_version_id: UUID) -> DashboardQualitySummary:
        blocking, warning, acknowledged = session.execute(
            select(
                func.count(QualityIssue.id).filter(
                    QualityIssue.severity == "blocking"
                ),
                func.count(QualityIssue.id).filter(QualityIssue.severity == "warning"),
                func.count(WarningAcknowledgement.id),
            )
            .select_from(QualityIssue)
            .outerjoin(
                WarningAcknowledgement,
                WarningAcknowledgement.quality_issue_id == QualityIssue.id,
            )
            .where(QualityIssue.import_version_id == import_version_id)
        ).one()
        reconciliations = tuple(
            session.scalars(
                select(ReconciliationResult.passed)
                .where(ReconciliationResult.import_version_id == import_version_id)
                .order_by(ReconciliationResult.reconciliation_code)
            )
        )
        reconciliation_status: Literal["passed", "failed", "not_available"]
        if not reconciliations:
            reconciliation_status = "not_available"
        elif all(reconciliations):
            reconciliation_status = "passed"
        else:
            reconciliation_status = "failed"
        return DashboardQualitySummary(
            blocking_issue_count=int(blocking or 0),
            warning_issue_count=int(warning or 0),
            acknowledged_warning_count=int(acknowledged or 0),
            reconciliation_status=reconciliation_status,
        )


__all__ = [
    "DashboardSourceBundle",
    "DashboardSourceRepository",
    "DashboardSourceUnavailableError",
    "DashboardTrendSourcePoint",
    "PublishedAnalysisResult",
    "PublishedFinding",
    "PublishedMetricValue",
]
