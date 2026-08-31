from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.canonical import (
    Customer,
    FactArCollection,
    FactBudget,
    FactFinancialActual,
    FactOperatingActual,
    ManagementAccount,
    Period,
    ScenarioVersion,
)
from flow_api.infrastructure.models.intake import (
    ImportVersion,
    QualityIssue,
    ReconciliationResult,
    WarningAcknowledgement,
)
from flow_api.metrics.source_rows import (
    ArSourceRow,
    BudgetSourceRow,
    FinancialSourceRow,
    OperatingSourceRow,
    PublishedMetricSource,
)

MetricSourceErrorCode = Literal[
    "blocking_quality_issue",
    "failed_reconciliation",
    "invalid_batch_metadata",
    "invalid_published_state",
    "no_published_import",
    "unacknowledged_warning",
]


class MetricSourceUnavailableError(RuntimeError):
    def __init__(self, code: MetricSourceErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


def _month_key(payload: dict[str, Any], field: str) -> int:
    raw_value = payload.get(field)
    if not isinstance(raw_value, str) or len(raw_value) != 7 or raw_value[4] != "-":
        raise MetricSourceUnavailableError(
            "invalid_batch_metadata", f"published import has invalid {field}"
        )
    try:
        month_key = int(raw_value.replace("-", ""))
    except ValueError as error:
        raise MetricSourceUnavailableError(
            "invalid_batch_metadata", f"published import has invalid {field}"
        ) from error
    month = month_key % 100
    if month < 1 or month > 12:
        raise MetricSourceUnavailableError(
            "invalid_batch_metadata", f"published import has invalid {field}"
        )
    return month_key


def _required_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise MetricSourceUnavailableError(
            "invalid_batch_metadata", f"published import has invalid {field}"
        )
    return value


class MetricSourceRepository:
    def get_published_source(
        self, session: Session, batch_id: UUID
    ) -> PublishedMetricSource:
        version = session.scalar(
            select(ImportVersion).where(
                ImportVersion.batch_id == batch_id,
                ImportVersion.is_published.is_(True),
            )
        )
        if version is None:
            raise MetricSourceUnavailableError(
                "no_published_import", f"batch has no published import: {batch_id}"
            )
        if version.status != "published":
            raise MetricSourceUnavailableError(
                "invalid_published_state", "published import has an invalid lifecycle state"
            )
        failed_reconciliations = session.scalar(
            select(func.count())
            .select_from(ReconciliationResult)
            .where(
                ReconciliationResult.import_version_id == version.id,
                ReconciliationResult.passed.is_(False),
            )
        )
        if failed_reconciliations:
            raise MetricSourceUnavailableError(
                "failed_reconciliation", "published import has a failed reconciliation"
            )
        blocking_issues = session.scalar(
            select(func.count())
            .select_from(QualityIssue)
            .where(
                QualityIssue.import_version_id == version.id,
                QualityIssue.severity == "blocking",
            )
        )
        if blocking_issues:
            raise MetricSourceUnavailableError(
                "blocking_quality_issue", "published import has a blocking quality issue"
            )
        unacknowledged_warnings = session.scalar(
            select(func.count())
            .select_from(QualityIssue)
            .outerjoin(
                WarningAcknowledgement,
                WarningAcknowledgement.quality_issue_id == QualityIssue.id,
            )
            .where(
                QualityIssue.import_version_id == version.id,
                QualityIssue.severity == "warning",
                WarningAcknowledgement.id.is_(None),
            )
        )
        if unacknowledged_warnings:
            raise MetricSourceUnavailableError(
                "unacknowledged_warning", "published import has an unacknowledged warning"
            )
        raw_batch = version.summary.get("batch")
        if not isinstance(raw_batch, dict):
            raise MetricSourceUnavailableError(
                "invalid_batch_metadata", "published import has no batch metadata"
            )
        batch_payload = {str(key): value for key, value in raw_batch.items()}
        return PublishedMetricSource(
            batch_id=batch_id,
            import_version_id=version.id,
            analysis_start_month=_month_key(batch_payload, "analysis_start_month"),
            analysis_end_month=_month_key(batch_payload, "analysis_end_month"),
            comparison_start_month=_month_key(batch_payload, "comparison_start_month"),
            comparison_end_month=_month_key(batch_payload, "comparison_end_month"),
            actual_scenario_code=_required_string(batch_payload, "actual_scenario_code"),
            budget_scenario_code=_required_string(batch_payload, "budget_scenario_code"),
        )

    def operating_rows(
        self, session: Session, source: PublishedMetricSource
    ) -> tuple[OperatingSourceRow, ...]:
        records = session.execute(
            select(FactOperatingActual, Period.month_key, Customer.segment_id)
            .join(Period, Period.id == FactOperatingActual.period_id)
            .join(Customer, Customer.id == FactOperatingActual.customer_id)
            .where(FactOperatingActual.import_version_id == source.import_version_id)
            .order_by(Period.month_key, FactOperatingActual.id)
        ).all()
        return tuple(
            OperatingSourceRow(
                fact_id=fact.id,
                import_version_id=fact.import_version_id,
                period_id=fact.period_id,
                month_key=month_key,
                organization_id=fact.organization_id,
                customer_id=fact.customer_id,
                customer_segment_id=segment_id,
                logistics_product_id=fact.logistics_product_id,
                region_id=fact.region_id,
                order_count=fact.order_count,
                shipment_count=fact.shipment_count,
                revenue=fact.revenue,
                warehousing_cost=fact.warehousing_cost,
                transportation_cost=fact.transportation_cost,
                other_direct_cost=fact.other_direct_cost,
            )
            for fact, month_key, segment_id in records
        )

    def financial_rows(
        self, session: Session, source: PublishedMetricSource
    ) -> tuple[FinancialSourceRow, ...]:
        records = session.execute(
            select(FactFinancialActual, Period.month_key, ManagementAccount.code)
            .join(Period, Period.id == FactFinancialActual.period_id)
            .join(
                ManagementAccount,
                ManagementAccount.id == FactFinancialActual.management_account_id,
            )
            .where(FactFinancialActual.import_version_id == source.import_version_id)
            .order_by(Period.month_key, FactFinancialActual.id)
        ).all()
        return tuple(
            FinancialSourceRow(
                fact_id=fact.id,
                import_version_id=fact.import_version_id,
                period_id=fact.period_id,
                month_key=month_key,
                organization_id=fact.organization_id,
                management_account_id=fact.management_account_id,
                management_account_code=account_code,
                amount=fact.amount,
            )
            for fact, month_key, account_code in records
        )

    def budget_rows(
        self, session: Session, source: PublishedMetricSource
    ) -> tuple[BudgetSourceRow, ...]:
        records = session.execute(
            select(FactBudget, Period.month_key, ScenarioVersion.code)
            .join(Period, Period.id == FactBudget.period_id)
            .join(ScenarioVersion, ScenarioVersion.id == FactBudget.scenario_version_id)
            .where(
                FactBudget.import_version_id == source.import_version_id,
                ScenarioVersion.code == source.budget_scenario_code,
            )
            .order_by(Period.month_key, FactBudget.id)
        ).all()
        return tuple(
            BudgetSourceRow(
                fact_id=fact.id,
                import_version_id=fact.import_version_id,
                period_id=fact.period_id,
                month_key=month_key,
                organization_id=fact.organization_id,
                customer_segment_id=fact.customer_segment_id,
                logistics_product_id=fact.logistics_product_id,
                management_account_id=fact.management_account_id,
                scenario_version_id=fact.scenario_version_id,
                scenario_code=scenario_code,
                metric_code=fact.metric_code,
                amount=fact.amount,
            )
            for fact, month_key, scenario_code in records
        )

    def ar_rows(
        self, session: Session, source: PublishedMetricSource
    ) -> tuple[ArSourceRow, ...]:
        records = session.execute(
            select(FactArCollection, Period.month_key, Customer.segment_id)
            .join(Period, Period.id == FactArCollection.period_id)
            .join(Customer, Customer.id == FactArCollection.customer_id)
            .where(FactArCollection.import_version_id == source.import_version_id)
            .order_by(Period.month_key, FactArCollection.id)
        ).all()
        return tuple(
            ArSourceRow(
                fact_id=fact.id,
                import_version_id=fact.import_version_id,
                period_id=fact.period_id,
                month_key=month_key,
                customer_id=fact.customer_id,
                customer_segment_id=segment_id,
                invoice_number=fact.invoice_number,
                aging_bucket=fact.aging_bucket,
                receivable_balance=fact.receivable_balance,
                due_amount=fact.due_amount,
                overdue_amount=fact.overdue_amount,
                collected_amount=fact.collected_amount,
            )
            for fact, month_key, segment_id in records
        )
