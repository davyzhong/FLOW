from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import Field

from flow_api.analysis.decimal_math import (
    contribution_ratio,
    ensure_decimal,
    money,
    ratio,
    reconcile,
)
from flow_api.analysis.models import (
    AnalysisResultDraft,
    DriverContributionDraft,
    FrozenModel,
    StrictDecimal,
)


class ProfitBridgeInput(FrozenModel):
    revenue_result: AnalysisResultDraft
    comparison_warehousing_cost: StrictDecimal
    analysis_warehousing_cost: StrictDecimal
    comparison_transportation_cost: StrictDecimal
    analysis_transportation_cost: StrictDecimal
    comparison_other_direct_cost: StrictDecimal
    analysis_other_direct_cost: StrictDecimal
    comparison_gross_profit: StrictDecimal
    analysis_gross_profit: StrictDecimal
    comparison_operating_expense: StrictDecimal
    analysis_operating_expense: StrictDecimal
    comparison_operating_profit: StrictDecimal
    analysis_operating_profit: StrictDecimal
    source_record_count: int = Field(gt=0)


class ArCashInput(FrozenModel):
    comparison_bucket_balances: dict[str, StrictDecimal]
    analysis_bucket_balances: dict[str, StrictDecimal]
    comparison_closing_ar: StrictDecimal
    analysis_closing_ar: StrictDecimal
    comparison_dso: StrictDecimal
    analysis_dso: StrictDecimal
    due_amount: StrictDecimal = Field(ge=0)
    collected_amount: StrictDecimal = Field(ge=0)
    overdue_by_customer: dict[str, StrictDecimal]
    aging_complete: bool
    source_record_count: int = Field(gt=0)


class PlaybookSpec(FrozenModel):
    code: str = Field(min_length=1, max_length=128)
    version: int = Field(gt=0)
    dependencies: tuple[str, ...]


class PlaybookRegistry(FrozenModel):
    specs: dict[str, PlaybookSpec]
    execution_order: tuple[str, ...]


def _driver(
    code: str,
    method: str,
    amount: Decimal,
    total: Decimal,
    trace: dict[str, Any] | None = None,
) -> DriverContributionDraft:
    persisted = money(amount)
    return DriverContributionDraft(
        driver_code=code,
        calculation_method=method,
        contribution_amount=persisted,
        contribution_ratio=contribution_ratio(persisted, money(total)),
        calculation_trace=trace or {},
    )


def _upstream_degraded(
    playbook_code: str,
    impact: Decimal,
    source_record_count: int,
    tolerance: Decimal,
    upstream_code: str,
) -> AnalysisResultDraft:
    return AnalysisResultDraft(
        playbook_code=playbook_code,
        playbook_version=1,
        status="degraded",
        comparison_basis="prior_year",
        impact_amount=money(impact),
        unit="CNY",
        drivers=(),
        reconciliation_difference=Decimal("0.0000"),
        reconciliation_tolerance=tolerance,
        required_fields=("reconciled_revenue_vpm",),
        available_fields=(),
        missing_fields=("reconciled_revenue_vpm",),
        source_record_count=source_record_count,
        calculation_trace={"upstream_playbook": upstream_code},
        degradation_code="upstream_result_degraded",
        degradation_message=f"required upstream result is degraded: {upstream_code}",
    )


def calculate_gross_profit_bridge(
    payload: ProfitBridgeInput, *, tolerance: Decimal
) -> AnalysisResultDraft:
    checked_tolerance = ensure_decimal(tolerance)
    impact = payload.analysis_gross_profit - payload.comparison_gross_profit
    if payload.revenue_result.status != "complete":
        return _upstream_degraded(
            "gross_profit_bridge",
            impact,
            payload.source_record_count,
            checked_tolerance,
            payload.revenue_result.playbook_code,
        )

    drivers = tuple(
        _driver(
            f"revenue_{driver.driver_code}",
            f"reused from {payload.revenue_result.playbook_code}",
            driver.contribution_amount,
            impact,
            {"source_driver_code": driver.driver_code},
        )
        for driver in payload.revenue_result.drivers
    ) + (
        _driver(
            "warehousing_cost",
            "-(analysis warehousing cost - comparison warehousing cost)",
            -(payload.analysis_warehousing_cost - payload.comparison_warehousing_cost),
            impact,
        ),
        _driver(
            "transportation_cost",
            "-(analysis transportation cost - comparison transportation cost)",
            -(
                payload.analysis_transportation_cost
                - payload.comparison_transportation_cost
            ),
            impact,
        ),
        _driver(
            "other_direct_cost",
            "-(analysis other direct cost - comparison other direct cost)",
            -(payload.analysis_other_direct_cost - payload.comparison_other_direct_cost),
            impact,
        ),
    )
    driver_sum = sum(
        (driver.contribution_amount for driver in drivers), start=Decimal("0")
    )
    difference = reconcile(driver_sum, money(impact), checked_tolerance)
    fields = (
        "revenue_vpm",
        "warehousing_cost",
        "transportation_cost",
        "other_direct_cost",
        "gross_profit",
    )
    return AnalysisResultDraft(
        playbook_code="gross_profit_bridge",
        playbook_version=1,
        status="complete",
        comparison_basis="prior_year",
        impact_amount=money(impact),
        unit="CNY",
        drivers=drivers,
        reconciliation_difference=difference,
        reconciliation_tolerance=checked_tolerance,
        required_fields=fields,
        available_fields=fields,
        missing_fields=(),
        source_record_count=payload.source_record_count,
        calculation_trace={"driver_sum": str(driver_sum)},
    )


def calculate_operating_profit_bridge(
    payload: ProfitBridgeInput,
    *,
    gross_result: AnalysisResultDraft,
    tolerance: Decimal,
) -> AnalysisResultDraft:
    checked_tolerance = ensure_decimal(tolerance)
    impact = payload.analysis_operating_profit - payload.comparison_operating_profit
    if gross_result.status != "complete":
        return _upstream_degraded(
            "operating_profit_bridge",
            impact,
            payload.source_record_count,
            checked_tolerance,
            gross_result.playbook_code,
        )
    drivers = tuple(
        _driver(
            driver.driver_code,
            f"reused from {gross_result.playbook_code}",
            driver.contribution_amount,
            impact,
            {"source_driver_code": driver.driver_code},
        )
        for driver in gross_result.drivers
    ) + (
        _driver(
            "operating_expense",
            "-(analysis operating expense - comparison operating expense)",
            -(payload.analysis_operating_expense - payload.comparison_operating_expense),
            impact,
        ),
    )
    driver_sum = sum(
        (driver.contribution_amount for driver in drivers), start=Decimal("0")
    )
    difference = reconcile(driver_sum, money(impact), checked_tolerance)
    fields = ("gross_profit_bridge", "operating_expense", "operating_profit")
    return AnalysisResultDraft(
        playbook_code="operating_profit_bridge",
        playbook_version=1,
        status="complete",
        comparison_basis="prior_year",
        impact_amount=money(impact),
        unit="CNY",
        drivers=drivers,
        reconciliation_difference=difference,
        reconciliation_tolerance=checked_tolerance,
        required_fields=fields,
        available_fields=fields,
        missing_fields=(),
        source_record_count=payload.source_record_count,
        calculation_trace={"driver_sum": str(driver_sum)},
    )


def _aging_driver_code(bucket: str) -> str:
    normalized = bucket.lower().replace("+", "_plus").replace("-", "_")
    return f"aging_{normalized}"


def calculate_ar_cash_impact(
    payload: ArCashInput, *, tolerance: Decimal
) -> AnalysisResultDraft:
    checked_tolerance = ensure_decimal(tolerance)
    impact = -(payload.analysis_closing_ar - payload.comparison_closing_ar)
    required = (
        "receivable_balance",
        "aging_bucket",
        "due_amount",
        "collected_amount",
        "dso",
    )
    available = tuple(field for field in required if field != "aging_bucket")
    if not payload.aging_complete:
        return AnalysisResultDraft(
            playbook_code="ar_cash_impact",
            playbook_version=1,
            status="degraded",
            comparison_basis="prior_year",
            impact_amount=money(impact),
            unit="CNY",
            drivers=(),
            reconciliation_difference=Decimal("0.0000"),
            reconciliation_tolerance=checked_tolerance,
            required_fields=required,
            available_fields=available,
            missing_fields=("aging_bucket",),
            source_record_count=payload.source_record_count,
            calculation_trace={
                "comparison_closing_ar": str(payload.comparison_closing_ar),
                "analysis_closing_ar": str(payload.analysis_closing_ar),
            },
            degradation_code="missing_required_field",
            degradation_message="AR aging detail is incomplete",
        )
    if payload.due_amount == 0:
        return AnalysisResultDraft(
            playbook_code="ar_cash_impact",
            playbook_version=1,
            status="degraded",
            comparison_basis="prior_year",
            impact_amount=money(impact),
            unit="CNY",
            drivers=(),
            reconciliation_difference=Decimal("0.0000"),
            reconciliation_tolerance=checked_tolerance,
            required_fields=required,
            available_fields=required,
            missing_fields=("positive_due_amount",),
            source_record_count=payload.source_record_count,
            calculation_trace={},
            degradation_code="zero_denominator",
            degradation_message="collection rate requires a positive due amount",
        )
    bucket_codes = set(payload.comparison_bucket_balances) | set(
        payload.analysis_bucket_balances
    )
    comparison_bucket_total = sum(
        payload.comparison_bucket_balances.values(), start=Decimal("0")
    )
    analysis_bucket_total = sum(
        payload.analysis_bucket_balances.values(), start=Decimal("0")
    )
    if (
        abs(comparison_bucket_total - payload.comparison_closing_ar) > checked_tolerance
        or abs(analysis_bucket_total - payload.analysis_closing_ar) > checked_tolerance
    ):
        return AnalysisResultDraft(
            playbook_code="ar_cash_impact",
            playbook_version=1,
            status="degraded",
            comparison_basis="prior_year",
            impact_amount=money(impact),
            unit="CNY",
            drivers=(),
            reconciliation_difference=Decimal("0.0000"),
            reconciliation_tolerance=checked_tolerance,
            required_fields=required,
            available_fields=required,
            missing_fields=("reconciled_aging_buckets",),
            source_record_count=payload.source_record_count,
            calculation_trace={
                "comparison_bucket_total": str(comparison_bucket_total),
                "analysis_bucket_total": str(analysis_bucket_total),
            },
            degradation_code="source_total_mismatch",
            degradation_message="aging buckets do not reconcile to closing AR",
        )
    drivers = tuple(
        _driver(
            _aging_driver_code(bucket),
            "-(analysis bucket balance - comparison bucket balance)",
            -(
                payload.analysis_bucket_balances.get(bucket, Decimal("0"))
                - payload.comparison_bucket_balances.get(bucket, Decimal("0"))
            ),
            impact,
            {"aging_bucket": bucket},
        )
        for bucket in sorted(bucket_codes)
    )
    driver_sum = sum(
        (driver.contribution_amount for driver in drivers), start=Decimal("0")
    )
    difference = reconcile(driver_sum, money(impact), checked_tolerance)
    collection_rate = ratio(payload.collected_amount / payload.due_amount)
    collection_shortfall = money(payload.due_amount - payload.collected_amount)
    top_customer = None
    if payload.overdue_by_customer:
        top_customer = sorted(
            payload.overdue_by_customer.items(), key=lambda item: (-item[1], item[0])
        )[0][0]
    return AnalysisResultDraft(
        playbook_code="ar_cash_impact",
        playbook_version=1,
        status="complete",
        comparison_basis="prior_year",
        impact_amount=money(impact),
        unit="CNY",
        drivers=drivers,
        reconciliation_difference=difference,
        reconciliation_tolerance=checked_tolerance,
        required_fields=required,
        available_fields=required,
        missing_fields=(),
        source_record_count=payload.source_record_count,
        calculation_trace={
            "comparison_closing_ar": str(payload.comparison_closing_ar),
            "analysis_closing_ar": str(payload.analysis_closing_ar),
            "comparison_dso": str(payload.comparison_dso),
            "analysis_dso": str(payload.analysis_dso),
            "dso_change": str(payload.analysis_dso - payload.comparison_dso),
            "collection_rate": str(collection_rate),
            "collection_shortfall": str(collection_shortfall),
            "top_overdue_customer": top_customer,
        },
    )


def build_registry(specs: tuple[PlaybookSpec, ...]) -> PlaybookRegistry:
    codes = [spec.code for spec in specs]
    if len(codes) != len(set(codes)):
        raise ValueError("playbook registry has duplicate codes")
    by_code = {spec.code: spec for spec in specs}
    for spec in specs:
        unknown = set(spec.dependencies) - set(by_code)
        if unknown:
            raise ValueError(f"playbook {spec.code} has unknown dependencies: {sorted(unknown)}")
    completed: list[str] = []
    remaining = list(codes)
    while remaining:
        ready = [
            code
            for code in remaining
            if set(by_code[code].dependencies).issubset(completed)
        ]
        if not ready:
            raise ValueError("playbook dependency graph contains a cycle")
        for code in ready:
            completed.append(code)
            remaining.remove(code)
    return PlaybookRegistry(specs=by_code, execution_order=tuple(completed))


def build_default_registry() -> PlaybookRegistry:
    return build_registry(
        (
            PlaybookSpec(code="revenue_vpm", version=1, dependencies=()),
            PlaybookSpec(code="fulfillment_cost_rve", version=1, dependencies=()),
            PlaybookSpec(code="ar_cash_impact", version=1, dependencies=()),
            PlaybookSpec(
                code="gross_profit_bridge", version=1, dependencies=("revenue_vpm",)
            ),
            PlaybookSpec(
                code="operating_profit_bridge",
                version=1,
                dependencies=("gross_profit_bridge",),
            ),
        )
    )


__all__ = [
    "ArCashInput",
    "PlaybookRegistry",
    "PlaybookSpec",
    "ProfitBridgeInput",
    "build_default_registry",
    "build_registry",
    "calculate_ar_cash_impact",
    "calculate_gross_profit_bridge",
    "calculate_operating_profit_bridge",
]
