"""Identity-bound read queries for the Investigation workbench."""

from __future__ import annotations

from dataclasses import dataclass
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
    ReviewEvent,
)
from flow_api.infrastructure.models.canonical import (
    Customer,
    CustomerSegment,
    FactArCollection,
    FactOperatingActual,
    LogisticsProduct,
    Region,
)
from flow_api.infrastructure.models.intake import (
    ImportVersion,
    QualityIssue,
    ReconciliationResult,
    SourceFile,
    SourceRecord,
)

OPERATING_PLAYBOOKS = frozenset(
    {
        "revenue_vpm",
        "gross_profit_bridge",
        "fulfillment_cost_rve",
        "operating_profit_bridge",
    }
)

PLAYBOOK_METRIC_CODES = {
    "revenue_vpm": "revenue",
    "fulfillment_cost_rve": "direct_cost",
    "gross_profit_bridge": "gross_profit",
    "operating_profit_bridge": "operating_profit",
    "ar_cash_impact": "collection_rate",
}


@dataclass(frozen=True, slots=True)
class SourceRef:
    file_name: str
    sheet_name: str
    source_row: int
    source_column: str


@dataclass(frozen=True, slots=True)
class OperatingRecordLine:
    fact_id: UUID
    month_key: int
    customer_id: UUID
    segment_name: str | None
    logistics_product_id: UUID
    region_id: UUID
    order_count: str
    revenue: str
    warehousing_cost: str
    transportation_cost: str
    other_direct_cost: str
    lineage: SourceRef


@dataclass(frozen=True, slots=True)
class ArRecordLine:
    fact_id: UUID
    month_key: int
    customer_id: UUID
    invoice_number: str | None
    aging_bucket: str | None
    receivable_balance: str
    due_amount: str
    overdue_amount: str
    collected_amount: str
    lineage: SourceRef


@dataclass(frozen=True, slots=True)
class FindingBinding:
    finding: Finding
    run: AnalysisRun
    snapshot: MetricSnapshot
    import_version: ImportVersion
    result: AnalysisResult | None
    metric_definition: MetricDefinition | None


class InvestigationNotFoundError(RuntimeError):
    code = "investigation_not_found"


class InvestigationIdentityMismatchError(RuntimeError):
    code = "investigation_identity_mismatch"


def _batch_metadata(import_version: ImportVersion) -> dict[str, object]:
    summary = import_version.summary or {}
    raw = summary.get("batch")
    if not isinstance(raw, dict):
        raise InvestigationNotFoundError("bound import has no batch metadata")
    return {str(key): value for key, value in raw.items()}


def _month(payload: dict[str, object], field: str) -> int:
    value = payload.get(field)
    if isinstance(value, str) and len(value) == 7:
        month = int(value.replace("-", ""))
    else:
        raise InvestigationNotFoundError(f"bound import has invalid {field}")
    if month < 197001 or month % 100 not in range(1, 13):
        raise InvestigationNotFoundError(f"bound import has invalid {field}")
    return month


class InvestigationRepository:
    def load_binding(
        self,
        session: Session,
        finding_id: UUID,
        *,
        batch_id: UUID | None,
        metric_snapshot_id: UUID | None,
        analysis_run_id: UUID | None,
    ) -> FindingBinding:
        finding = session.get(Finding, finding_id)
        if finding is None:
            raise InvestigationNotFoundError(f"finding does not exist: {finding_id}")
        run = session.get(AnalysisRun, finding.analysis_run_id)
        snapshot = session.get(MetricSnapshot, finding.metric_snapshot_id)
        if run is None or snapshot is None:
            raise InvestigationNotFoundError("finding is not bound to a published run")
        if batch_id is not None and batch_id != snapshot.batch_id:
            raise InvestigationIdentityMismatchError(
                "batch_id does not match the finding's immutable analysis lineage"
            )
        if metric_snapshot_id is not None and metric_snapshot_id != snapshot.id:
            raise InvestigationIdentityMismatchError(
                "metric_snapshot_id does not match the finding's immutable analysis lineage"
            )
        if analysis_run_id is not None and analysis_run_id != run.id:
            raise InvestigationIdentityMismatchError(
                "analysis_run_id does not match the finding's immutable analysis lineage"
            )
        import_version = session.get(ImportVersion, run.import_version_id)
        if import_version is None or import_version.batch_id != snapshot.batch_id:
            raise InvestigationNotFoundError("finding lineage is missing its import version")
        result = (
            session.get(AnalysisResult, finding.analysis_result_id)
            if finding.analysis_result_id
            else None
        )
        metric_definition = (
            session.get(MetricDefinition, finding.metric_definition_id)
            if finding.metric_definition_id
            else None
        )
        return FindingBinding(
            finding=finding,
            run=run,
            snapshot=snapshot,
            import_version=import_version,
            result=result,
            metric_definition=metric_definition,
        )

    def drivers(self, session: Session, finding: Finding) -> tuple[DriverContribution, ...]:
        return tuple(
            session.scalars(
                select(DriverContribution)
                .where(DriverContribution.finding_id == finding.id)
                .order_by(DriverContribution.position)
            )
        )

    def evidence(self, session: Session, finding: Finding) -> tuple[Evidence, ...]:
        return tuple(
            session.scalars(
                select(Evidence).where(Evidence.finding_id == finding.id).order_by(Evidence.id)
            )
        )

    def reviews(self, session: Session, finding: Finding) -> tuple[ReviewEvent, ...]:
        return tuple(
            session.scalars(
                select(ReviewEvent)
                .where(ReviewEvent.finding_id == finding.id)
                .order_by(ReviewEvent.sequence)
            )
        )

    def latest_review_event(self, session: Session, finding: Finding) -> ReviewEvent | None:
        return session.scalar(
            select(ReviewEvent)
            .where(ReviewEvent.finding_id == finding.id)
            .order_by(ReviewEvent.sequence.desc())
            .limit(1)
        )

    def quality_issues(
        self, session: Session, import_version: ImportVersion
    ) -> tuple[QualityIssue, ...]:
        return tuple(
            session.scalars(
                select(QualityIssue)
                .where(QualityIssue.import_version_id == import_version.id)
                .order_by(QualityIssue.severity, QualityIssue.code)
            )
        )

    def reconciliations(
        self, session: Session, import_version: ImportVersion
    ) -> tuple[ReconciliationResult, ...]:
        return tuple(
            session.scalars(
                select(ReconciliationResult)
                .where(ReconciliationResult.import_version_id == import_version.id)
                .order_by(ReconciliationResult.reconciliation_code)
            )
        )

    def _analysis_months(self, binding: FindingBinding) -> frozenset[int]:
        payload = _batch_metadata(binding.import_version)
        start = _month(payload, "analysis_start_month")
        end = _month(payload, "analysis_end_month")
        if end < start:
            raise InvestigationNotFoundError("bound import has an inverted analysis window")
        return frozenset(range(start, end + 1))

    def _lineage_refs(
        self,
        session: Session,
        source_record_ids: list[UUID],
    ) -> dict[UUID, SourceRef]:
        refs: dict[UUID, SourceRef] = {}
        if not source_record_ids:
            return refs
        records = list(
            session.scalars(select(SourceRecord).where(SourceRecord.id.in_(source_record_ids)))
        )
        file_ids = {record.source_file_id for record in records}
        files = {
            source_file.id: source_file
            for source_file in session.scalars(
                select(SourceFile).where(SourceFile.id.in_(file_ids))
            )
        }
        for record in records:
            source_file = files.get(record.source_file_id)
            if source_file is None:
                continue
            refs[record.id] = SourceRef(
                file_name=source_file.original_filename,
                sheet_name=record.sheet_name,
                source_row=record.source_row,
                source_column=record.source_column,
            )
        return refs

    def operating_records(
        self,
        session: Session,
        binding: FindingBinding,
        *,
        playbook_code: str,
        limit: int,
    ) -> tuple[OperatingRecordLine, ...]:
        months = self._analysis_months(binding)
        facts = session.scalars(
            select(FactOperatingActual).where(
                FactOperatingActual.import_version_id == binding.import_version.id
            )
        )
        in_window = [fact for fact in facts if fact.period.month_key in months]
        if playbook_code == "fulfillment_cost_rve":
            in_window.sort(
                key=lambda fact: (
                    fact.transportation_cost
                    + fact.warehousing_cost
                    + fact.other_direct_cost,
                    fact.transportation_cost,
                ),
                reverse=True,
            )
        else:
            in_window.sort(key=lambda fact: fact.revenue, reverse=True)
        in_window = in_window[:limit]
        customers = {
            customer.id: customer for customer in session.scalars(select(Customer))
        }
        refs = self._lineage_refs(session, [fact.source_record_id for fact in in_window])
        lines: list[OperatingRecordLine] = []
        for fact in in_window:
            lineage = refs.get(fact.source_record_id)
            if lineage is None:
                continue
            customer = customers.get(fact.customer_id)
            segment = customer.segment if customer is not None else None
            lines.append(
                OperatingRecordLine(
                    fact_id=fact.id,
                    month_key=fact.period.month_key,
                    customer_id=fact.customer_id,
                    segment_name=str(segment.name) if segment is not None else None,
                    logistics_product_id=fact.logistics_product_id,
                    region_id=fact.region_id,
                    order_count=str(fact.order_count),
                    revenue=str(fact.revenue),
                    warehousing_cost=str(fact.warehousing_cost),
                    transportation_cost=str(fact.transportation_cost),
                    other_direct_cost=str(fact.other_direct_cost),
                    lineage=lineage,
                )
            )
        return tuple(lines)

    def ar_records(
        self,
        session: Session,
        binding: FindingBinding,
        *,
        limit: int,
    ) -> tuple[ArRecordLine, ...]:
        months = self._analysis_months(binding)
        facts = session.scalars(
            select(FactArCollection).where(
                FactArCollection.import_version_id == binding.import_version.id
            )
        )
        in_window = [fact for fact in facts if fact.period.month_key in months]
        in_window.sort(
            key=lambda fact: (fact.overdue_amount, fact.due_amount),
            reverse=True,
        )
        in_window = in_window[:limit]
        refs = self._lineage_refs(session, [fact.source_record_id for fact in in_window])
        lines: list[ArRecordLine] = []
        for fact in in_window:
            lineage = refs.get(fact.source_record_id)
            if lineage is None:
                continue
            lines.append(
                ArRecordLine(
                    fact_id=fact.id,
                    month_key=fact.period.month_key,
                    customer_id=fact.customer_id,
                    invoice_number=fact.invoice_number,
                    aging_bucket=fact.aging_bucket,
                    receivable_balance=str(fact.receivable_balance),
                    due_amount=str(fact.due_amount),
                    overdue_amount=str(fact.overdue_amount),
                    collected_amount=str(fact.collected_amount),
                    lineage=lineage,
                )
            )
        return tuple(lines)

    def metric_definition_for_playbook(
        self,
        session: Session,
        binding: FindingBinding,
        *,
        playbook_code: str,
    ) -> MetricDefinition | None:
        metric_code = PLAYBOOK_METRIC_CODES.get(playbook_code)
        if metric_code is None:
            return None
        return session.scalar(
            select(MetricDefinition)
            .join(MetricValue, MetricValue.metric_definition_id == MetricDefinition.id)
            .where(
                MetricDefinition.metric_code == metric_code,
                MetricValue.metric_snapshot_id == binding.snapshot.id,
            )
            .order_by(MetricDefinition.version.desc())
            .limit(1)
        )

    def label_maps(
        self, session: Session
    ) -> tuple[dict[UUID, str], dict[UUID, str], dict[UUID, str], dict[UUID, str]]:
        segments = {row.id: str(row.name) for row in session.scalars(select(CustomerSegment))}
        products = {row.id: str(row.name) for row in session.scalars(select(LogisticsProduct))}
        regions = {row.id: str(row.name) for row in session.scalars(select(Region))}
        customers = {row.id: str(row.name) for row in session.scalars(select(Customer))}
        return segments, products, regions, customers


__all__ = [
    "ArRecordLine",
    "FindingBinding",
    "InvestigationIdentityMismatchError",
    "InvestigationNotFoundError",
    "InvestigationRepository",
    "OperatingRecordLine",
    "OPERATING_PLAYBOOKS",
    "SourceRef",
]
