from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Callable
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.analysis.bridges import (
    FulfillmentTotals,
    RevenueMixCell,
    calculate_fulfillment_rve,
    calculate_revenue_vpm,
)
from flow_api.analysis.decimal_math import ratio
from flow_api.analysis.evidence import build_verified_evidence
from flow_api.analysis.findings import qualify_finding, rank_findings
from flow_api.analysis.models import AnalysisResultDraft, FindingDraft
from flow_api.analysis.playbooks import (
    ArCashInput,
    ProfitBridgeInput,
    calculate_ar_cash_impact,
    calculate_gross_profit_bridge,
    calculate_operating_profit_bridge,
)
from flow_api.analysis.policy import LoadedAnalysisPolicy
from flow_api.analysis.repositories import AnalysisSourceBundle, AnalysisSourceRepository
from flow_api.infrastructure.models.analytics import (
    AnalysisDriver,
    AnalysisResult,
    AnalysisRun,
    DriverContribution,
    Evidence,
    Finding,
    FindingScoreComponent,
)
from flow_api.metrics.source_rows import OperatingSourceRow

FINDING_TYPES = {
    "revenue_vpm": "revenue_growth",
    "fulfillment_cost_rve": "fulfillment_cost_increase",
    "gross_profit_bridge": "gross_profit_deterioration",
    "operating_profit_bridge": "operating_profit_deterioration",
    "ar_cash_impact": "ar_cash_deterioration",
}


def _sum(values: list[Decimal]) -> Decimal:
    return sum(values, start=Decimal("0"))


def _operating_windows(
    bundle: AnalysisSourceBundle,
) -> tuple[tuple[OperatingSourceRow, ...], tuple[OperatingSourceRow, ...]]:
    source = bundle.source
    analysis = tuple(
        row
        for row in bundle.operating_rows
        if source.analysis_start_month <= row.month_key <= source.analysis_end_month
    )
    comparison = tuple(
        row
        for row in bundle.operating_rows
        if source.comparison_start_month <= row.month_key <= source.comparison_end_month
    )
    return analysis, comparison


def _revenue_cells(bundle: AnalysisSourceBundle) -> tuple[RevenueMixCell, ...]:
    analysis, comparison = _operating_windows(bundle)
    analysis_by_product: dict[UUID, list[OperatingSourceRow]] = defaultdict(list)
    comparison_by_product: dict[UUID, list[OperatingSourceRow]] = defaultdict(list)
    for row in analysis:
        analysis_by_product[row.logistics_product_id].append(row)
    for row in comparison:
        comparison_by_product[row.logistics_product_id].append(row)
    cells: list[RevenueMixCell] = []
    for product_id in sorted(
        set(analysis_by_product) | set(comparison_by_product), key=str
    ):
        analysis_rows = analysis_by_product[product_id]
        comparison_rows = comparison_by_product[product_id]
        cells.append(
            RevenueMixCell(
                cell_code=str(product_id),
                comparison_orders=_sum([row.order_count for row in comparison_rows]),
                comparison_revenue=_sum([row.revenue for row in comparison_rows]),
                analysis_orders=_sum([row.order_count for row in analysis_rows]),
                analysis_revenue=_sum([row.revenue for row in analysis_rows]),
                source_record_count=len(analysis_rows) + len(comparison_rows),
            )
        )
    return tuple(cells)


def _financial_total(bundle: AnalysisSourceBundle, code: str, *, analysis: bool) -> Decimal:
    source = bundle.source
    start = source.analysis_start_month if analysis else source.comparison_start_month
    end = source.analysis_end_month if analysis else source.comparison_end_month
    return _sum(
        [
            row.amount
            for row in bundle.financial_rows
            if start <= row.month_key <= end and row.management_account_code == code
        ]
    )


def _profit_input(
    bundle: AnalysisSourceBundle, revenue_result: AnalysisResultDraft
) -> ProfitBridgeInput:
    analysis, comparison = _operating_windows(bundle)
    comparison_revenue = _sum([row.revenue for row in comparison])
    analysis_revenue = _sum([row.revenue for row in analysis])
    comparison_warehouse = _sum([row.warehousing_cost for row in comparison])
    analysis_warehouse = _sum([row.warehousing_cost for row in analysis])
    comparison_transport = _sum([row.transportation_cost for row in comparison])
    analysis_transport = _sum([row.transportation_cost for row in analysis])
    comparison_other = _sum([row.other_direct_cost for row in comparison])
    analysis_other = _sum([row.other_direct_cost for row in analysis])
    return ProfitBridgeInput(
        revenue_result=revenue_result,
        comparison_warehousing_cost=comparison_warehouse,
        analysis_warehousing_cost=analysis_warehouse,
        comparison_transportation_cost=comparison_transport,
        analysis_transportation_cost=analysis_transport,
        comparison_other_direct_cost=comparison_other,
        analysis_other_direct_cost=analysis_other,
        comparison_gross_profit=(
            comparison_revenue
            - comparison_warehouse
            - comparison_transport
            - comparison_other
        ),
        analysis_gross_profit=(
            analysis_revenue - analysis_warehouse - analysis_transport - analysis_other
        ),
        comparison_operating_expense=_financial_total(
            bundle, "OPERATING_EXPENSE", analysis=False
        ),
        analysis_operating_expense=_financial_total(
            bundle, "OPERATING_EXPENSE", analysis=True
        ),
        comparison_operating_profit=_financial_total(
            bundle, "OPERATING_PROFIT", analysis=False
        ),
        analysis_operating_profit=_financial_total(
            bundle, "OPERATING_PROFIT", analysis=True
        ),
        source_record_count=len(analysis) + len(comparison) + len(bundle.financial_rows),
    )


def _ar_input(bundle: AnalysisSourceBundle) -> ArCashInput:
    source = bundle.source
    analysis_rows = tuple(
        row for row in bundle.ar_rows if row.month_key == source.analysis_end_month
    )
    comparison_rows = tuple(
        row for row in bundle.ar_rows if row.month_key == source.comparison_end_month
    )
    analysis_buckets: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    comparison_buckets: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    overdue_by_customer: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for row in analysis_rows:
        analysis_buckets[row.aging_bucket or "unclassified"] += row.receivable_balance
        overdue_by_customer[str(row.customer_id)] += row.overdue_amount
    for row in comparison_rows:
        comparison_buckets[row.aging_bucket or "unclassified"] += row.receivable_balance
    analysis, comparison = _operating_windows(bundle)
    analysis_revenue = _sum([row.revenue for row in analysis])
    comparison_revenue = _sum([row.revenue for row in comparison])
    analysis_ar = _sum([row.receivable_balance for row in analysis_rows])
    comparison_ar = _sum([row.receivable_balance for row in comparison_rows])
    return ArCashInput(
        comparison_bucket_balances=dict(comparison_buckets),
        analysis_bucket_balances=dict(analysis_buckets),
        comparison_closing_ar=comparison_ar,
        analysis_closing_ar=analysis_ar,
        comparison_dso=ratio(comparison_ar / comparison_revenue * Decimal("365")),
        analysis_dso=ratio(analysis_ar / analysis_revenue * Decimal("365")),
        due_amount=_sum([row.due_amount for row in analysis_rows]),
        collected_amount=_sum([row.collected_amount for row in analysis_rows]),
        overdue_by_customer=dict(overdue_by_customer),
        aging_complete=all(row.aging_bucket is not None for row in analysis_rows + comparison_rows),
        source_record_count=len(analysis_rows) + len(comparison_rows),
    )


def calculate_analysis_results(
    bundle: AnalysisSourceBundle, *, tolerance: Decimal
) -> tuple[AnalysisResultDraft, ...]:
    cells = _revenue_cells(bundle)
    revenue = calculate_revenue_vpm(cells, tolerance=tolerance)
    analysis, comparison = _operating_windows(bundle)
    fulfillment = calculate_fulfillment_rve(
        FulfillmentTotals(
            comparison_orders=_sum([row.order_count for row in comparison]),
            comparison_shipments=_sum([row.shipment_count for row in comparison]),
            comparison_cost=_sum(
                [
                    row.warehousing_cost
                    + row.transportation_cost
                    + row.other_direct_cost
                    for row in comparison
                ]
            ),
            analysis_orders=_sum([row.order_count for row in analysis]),
            analysis_shipments=_sum([row.shipment_count for row in analysis]),
            analysis_cost=_sum(
                [
                    row.warehousing_cost
                    + row.transportation_cost
                    + row.other_direct_cost
                    for row in analysis
                ]
            ),
            source_record_count=len(analysis) + len(comparison),
        ),
        tolerance=tolerance,
    )
    profit_input = _profit_input(bundle, revenue)
    gross = calculate_gross_profit_bridge(profit_input, tolerance=tolerance)
    operating = calculate_operating_profit_bridge(
        profit_input, gross_result=gross, tolerance=tolerance
    )
    ar_cash = calculate_ar_cash_impact(_ar_input(bundle), tolerance=tolerance)
    return revenue, fulfillment, gross, operating, ar_cash


def _run_fingerprint(
    snapshot_id: UUID, policy_hash: str, engine_version: str
) -> str:
    canonical = json.dumps(
        {
            "snapshot_id": str(snapshot_id),
            "policy_hash": policy_hash,
            "engine_version": engine_version,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _persist_result(
    session: Session, run: AnalysisRun, draft: AnalysisResultDraft
) -> AnalysisResult:
    result = AnalysisResult(
        analysis_run=run,
        playbook_code=draft.playbook_code,
        playbook_version=draft.playbook_version,
        status=draft.status,
        comparison_basis=draft.comparison_basis,
        impact_amount=draft.impact_amount,
        unit=draft.unit,
        reconciliation_difference=draft.reconciliation_difference,
        reconciliation_tolerance=draft.reconciliation_tolerance,
        required_fields=list(draft.required_fields),
        available_fields=list(draft.available_fields),
        missing_fields=list(draft.missing_fields),
        source_record_count=draft.source_record_count,
        calculation_trace=draft.calculation_trace,
        degradation_code=draft.degradation_code,
        degradation_message=draft.degradation_message,
    )
    result.drivers = [
        AnalysisDriver(
            position=position,
            driver_code=driver.driver_code,
            calculation_method=driver.calculation_method,
            contribution_amount=driver.contribution_amount,
            contribution_ratio=driver.contribution_ratio,
            calculation_trace=driver.calculation_trace,
        )
        for position, driver in enumerate(draft.drivers, start=1)
    ]
    session.add(result)
    session.flush()
    return result


def _persist_finding(
    session: Session,
    run: AnalysisRun,
    result: AnalysisResult,
    draft: FindingDraft,
) -> Finding:
    finding = Finding(
        metric_snapshot_id=run.metric_snapshot_id,
        analysis_run=run,
        analysis_result=result,
        finding_type=draft.finding_type,
        title=draft.title,
        status="candidate",
        fact_statement=draft.fact_statement,
        comparison_basis=draft.comparison_basis,
        impact_amount=draft.impact_amount,
        confidence=draft.confidence,
        business_meaning=draft.business_meaning,
        total_score=draft.total_score,
        policy_version=draft.policy_version,
        fingerprint=draft.fingerprint,
        qualification_trace=draft.qualification_trace,
    )
    finding.drivers = [
        DriverContribution(
            position=position,
            driver_code=driver.driver_code,
            calculation_method=driver.calculation_method,
            contribution_amount=driver.contribution_amount,
            contribution_ratio=driver.contribution_ratio,
            calculation_trace=driver.calculation_trace,
        )
        for position, driver in enumerate(result.drivers, start=1)
    ]
    finding.score_components = [
        FindingScoreComponent(
            component_code=component.component_code,
            raw_value=component.raw_value,
            normalized_score=component.normalized_score,
            weight=component.weight,
            weighted_score=component.weighted_score,
            calculation_trace=component.calculation_trace,
        )
        for component in draft.score_components
    ]
    session.add(finding)
    session.flush()
    finding_evidence = []
    for item in draft.evidence:
        finding_evidence.append(
            Evidence(
                finding=finding,
                status="verified",
                evidence_type=item.evidence_type,
                object_type=item.object_type,
                object_id=item.object_id,
                evidence_digest=item.digest,
                verification_trace=item.verification_trace,
            )
        )
    session.add_all(finding_evidence)
    return finding


class AnalysisRunService:
    def __init__(self, repository: AnalysisSourceRepository | None = None) -> None:
        self.repository = repository or AnalysisSourceRepository()

    def create_run(
        self,
        session: Session,
        *,
        snapshot_id: UUID,
        loaded_policy: LoadedAnalysisPolicy,
        failure_hook: Callable[[], None] | None = None,
    ) -> AnalysisRun:
        policy = loaded_policy.policy
        existing = session.scalar(
            select(AnalysisRun).where(
                AnalysisRun.metric_snapshot_id == snapshot_id,
                AnalysisRun.policy_set_hash == loaded_policy.policy_hash,
                AnalysisRun.engine_version == policy.engine_version,
                AnalysisRun.status == "published",
            )
        )
        if existing is not None:
            return existing
        bundle = self.repository.get_bound_source(session, snapshot_id)
        drafts = calculate_analysis_results(
            bundle, tolerance=policy.reconciliation_tolerance
        )
        run_identity = _run_fingerprint(
            snapshot_id, loaded_policy.policy_hash, policy.engine_version
        )
        with session.begin_nested():
            run = AnalysisRun(
                metric_snapshot_id=snapshot_id,
                import_version_id=bundle.import_version_id,
                policy_id=policy.policy_id,
                policy_set_hash=loaded_policy.policy_hash,
                engine_version=policy.engine_version,
                fingerprint=run_identity,
                status="building",
            )
            session.add(run)
            session.flush()
            persisted_results = {
                draft.playbook_code: _persist_result(session, run, draft)
                for draft in drafts
            }
            finding_drafts: list[FindingDraft] = []
            fingerprints: set[str] = set()
            for draft in drafts:
                evidence = build_verified_evidence(draft, bundle)
                outcome = qualify_finding(
                    result=draft,
                    finding_type=FINDING_TYPES[draft.playbook_code],
                    policy=policy,
                    evidence=evidence,
                    persistence_flags=(),
                    run_identity=run_identity,
                    expected_run_identity=run_identity,
                    existing_fingerprints=frozenset(fingerprints),
                )
                if outcome.finding is not None:
                    fingerprints.add(outcome.finding.fingerprint)
                    finding_drafts.append(outcome.finding)
            for finding_draft in rank_findings(tuple(finding_drafts)):
                _persist_finding(
                    session,
                    run,
                    persisted_results[finding_draft.playbook_code],
                    finding_draft,
                )
            session.flush()
            if failure_hook is not None:
                failure_hook()
            run.status = "published"
            session.flush()
        return run


__all__ = ["AnalysisRunService", "calculate_analysis_results"]
