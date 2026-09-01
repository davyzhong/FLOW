from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import Field

from flow_api.analysis.decimal_math import contribution_ratio, ensure_decimal, money, reconcile
from flow_api.analysis.models import (
    AnalysisResultDraft,
    DegradationCode,
    DriverContributionDraft,
    FrozenModel,
    StrictDecimal,
)


class RevenueMixCell(FrozenModel):
    cell_code: str = Field(min_length=1, max_length=128)
    comparison_orders: StrictDecimal = Field(ge=0)
    comparison_revenue: StrictDecimal
    analysis_orders: StrictDecimal = Field(ge=0)
    analysis_revenue: StrictDecimal
    source_record_count: int = Field(gt=0)


class FulfillmentTotals(FrozenModel):
    comparison_orders: StrictDecimal = Field(ge=0)
    comparison_shipments: StrictDecimal = Field(ge=0)
    comparison_cost: StrictDecimal
    analysis_orders: StrictDecimal = Field(ge=0)
    analysis_shipments: StrictDecimal = Field(ge=0)
    analysis_cost: StrictDecimal
    source_record_count: int = Field(gt=0)


def _driver(
    code: str, method: str, amount: Decimal, total: Decimal, **trace: Any
) -> DriverContributionDraft:
    persisted = money(amount)
    return DriverContributionDraft(
        driver_code=code,
        calculation_method=method,
        contribution_amount=persisted,
        contribution_ratio=contribution_ratio(persisted, money(total)),
        calculation_trace={key: str(value) for key, value in trace.items()},
    )


def _degraded(
    *,
    playbook_code: str,
    impact: Decimal,
    required_fields: tuple[str, ...],
    available_fields: tuple[str, ...],
    missing_fields: tuple[str, ...],
    source_record_count: int,
    code: DegradationCode,
    message: str,
    trace: dict[str, Any],
    tolerance: Decimal,
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
        required_fields=required_fields,
        available_fields=available_fields,
        missing_fields=missing_fields,
        source_record_count=source_record_count,
        calculation_trace=trace,
        degradation_code=code,
        degradation_message=message,
    )


def calculate_revenue_vpm(
    cells: tuple[RevenueMixCell, ...],
    *,
    tolerance: Decimal,
    expected_comparison_revenue: Decimal | None = None,
    expected_analysis_revenue: Decimal | None = None,
) -> AnalysisResultDraft:
    checked_tolerance = ensure_decimal(tolerance)
    required = ("order_count", "revenue", "logistics_product")
    row_count = sum(cell.source_record_count for cell in cells)
    comparison_revenue = sum(
        (cell.comparison_revenue for cell in cells), start=Decimal("0")
    )
    analysis_revenue = sum((cell.analysis_revenue for cell in cells), start=Decimal("0"))
    impact = analysis_revenue - comparison_revenue

    codes = [cell.cell_code for cell in cells]
    expected_mismatch = (
        expected_comparison_revenue is not None
        and abs(comparison_revenue - ensure_decimal(expected_comparison_revenue))
        > checked_tolerance
    ) or (
        expected_analysis_revenue is not None
        and abs(analysis_revenue - ensure_decimal(expected_analysis_revenue)) > checked_tolerance
    )
    if len(codes) != len(set(codes)) or expected_mismatch:
        return _degraded(
            playbook_code="revenue_vpm",
            impact=impact,
            required_fields=required,
            available_fields=required,
            missing_fields=("reconciled_mix_cells",),
            source_record_count=row_count,
            code="source_total_mismatch",
            message="product mix cells are duplicated or do not reconcile to source totals",
            trace={
                "comparison_revenue": str(comparison_revenue),
                "analysis_revenue": str(analysis_revenue),
            },
            tolerance=checked_tolerance,
        )
    if not cells or any(
        cell.comparison_orders <= 0 or cell.analysis_orders <= 0 for cell in cells
    ):
        return _degraded(
            playbook_code="revenue_vpm",
            impact=impact,
            required_fields=required,
            available_fields=required,
            missing_fields=("matched_nonzero_mix_cell",),
            source_record_count=row_count,
            code="unmatched_mix_cell",
            message="V/P/M requires non-zero orders for every product in both windows",
            trace={"cell_codes": sorted(codes)},
            tolerance=checked_tolerance,
        )

    comparison_orders = sum((cell.comparison_orders for cell in cells), start=Decimal("0"))
    analysis_orders = sum((cell.analysis_orders for cell in cells), start=Decimal("0"))
    if comparison_orders <= 0:
        return _degraded(
            playbook_code="revenue_vpm",
            impact=impact,
            required_fields=required,
            available_fields=required,
            missing_fields=("positive_comparison_orders",),
            source_record_count=row_count,
            code="zero_denominator",
            message="comparison orders must be positive",
            trace={},
            tolerance=checked_tolerance,
        )
    base_average_price = comparison_revenue / comparison_orders
    volume = (analysis_orders - comparison_orders) * base_average_price
    mix = sum(
        (
            cell.analysis_orders
            * ((cell.comparison_revenue / cell.comparison_orders) - base_average_price)
            for cell in cells
        ),
        start=Decimal("0"),
    )
    price = sum(
        (
            cell.analysis_orders
            * (
                (cell.analysis_revenue / cell.analysis_orders)
                - (cell.comparison_revenue / cell.comparison_orders)
            )
            for cell in cells
        ),
        start=Decimal("0"),
    )
    drivers = (
        _driver(
            "volume",
            "(analysis_orders - comparison_orders) * comparison_average_price",
            volume,
            impact,
            analysis_orders=analysis_orders,
            comparison_orders=comparison_orders,
            comparison_average_price=base_average_price,
        ),
        _driver(
            "mix",
            "sum(analysis_cell_orders * (comparison_cell_price - comparison_average_price))",
            mix,
            impact,
            cell_count=len(cells),
        ),
        _driver(
            "price",
            "sum(analysis_cell_orders * (analysis_cell_price - comparison_cell_price))",
            price,
            impact,
            cell_count=len(cells),
        ),
    )
    persisted_sum = sum(
        (driver.contribution_amount for driver in drivers), start=Decimal("0")
    )
    difference = reconcile(persisted_sum, money(impact), checked_tolerance)
    return AnalysisResultDraft(
        playbook_code="revenue_vpm",
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
        source_record_count=row_count,
        calculation_trace={
            "comparison_orders": str(comparison_orders),
            "analysis_orders": str(analysis_orders),
            "comparison_revenue": str(comparison_revenue),
            "analysis_revenue": str(analysis_revenue),
            "base_average_price": str(base_average_price),
        },
    )


def calculate_fulfillment_rve(
    totals: FulfillmentTotals, *, tolerance: Decimal
) -> AnalysisResultDraft:
    checked_tolerance = ensure_decimal(tolerance)
    required = ("order_count", "shipment_count", "direct_cost")
    impact = totals.analysis_cost - totals.comparison_cost
    if (
        totals.comparison_orders <= 0
        or totals.comparison_shipments <= 0
        or totals.analysis_orders <= 0
        or totals.analysis_shipments <= 0
    ):
        return _degraded(
            playbook_code="fulfillment_cost_rve",
            impact=impact,
            required_fields=required,
            available_fields=required,
            missing_fields=("positive_orders_and_shipments",),
            source_record_count=totals.source_record_count,
            code="zero_denominator",
            message="R/V/E requires positive orders and shipments in both windows",
            trace={},
            tolerance=checked_tolerance,
        )
    shipments_per_order_0 = totals.comparison_shipments / totals.comparison_orders
    shipments_per_order_1 = totals.analysis_shipments / totals.analysis_orders
    cost_per_shipment_0 = totals.comparison_cost / totals.comparison_shipments
    cost_per_shipment_1 = totals.analysis_cost / totals.analysis_shipments
    volume = (
        (totals.analysis_orders - totals.comparison_orders)
        * shipments_per_order_0
        * cost_per_shipment_0
    )
    efficiency = (
        totals.analysis_orders
        * (shipments_per_order_1 - shipments_per_order_0)
        * cost_per_shipment_0
    )
    rate = (
        totals.analysis_orders
        * shipments_per_order_1
        * (cost_per_shipment_1 - cost_per_shipment_0)
    )
    drivers = (
        _driver("volume", "order volume effect", volume, impact),
        _driver("efficiency", "shipments per order effect", efficiency, impact),
        _driver("rate", "cost per shipment effect", rate, impact),
    )
    persisted_sum = sum(
        (driver.contribution_amount for driver in drivers), start=Decimal("0")
    )
    difference = reconcile(persisted_sum, money(impact), checked_tolerance)
    return AnalysisResultDraft(
        playbook_code="fulfillment_cost_rve",
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
        source_record_count=totals.source_record_count,
        calculation_trace={
            "comparison_shipments_per_order": str(shipments_per_order_0),
            "analysis_shipments_per_order": str(shipments_per_order_1),
            "comparison_cost_per_shipment": str(cost_per_shipment_0),
            "analysis_cost_per_shipment": str(cost_per_shipment_1),
        },
    )


__all__ = [
    "FulfillmentTotals",
    "RevenueMixCell",
    "calculate_fulfillment_rve",
    "calculate_revenue_vpm",
]
