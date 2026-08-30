from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from flow_api.data_contract.records import (
    ArCollectionRecord,
    CanonicalPackage,
    FinancialActualRecord,
    OperatingActualRecord,
)

MONEY_QUANTUM = Decimal("0.0001")
RATIO_QUANTUM = Decimal("0.000001")


def _sum(values: Iterable[Decimal]) -> Decimal:
    return sum(values, start=Decimal("0")).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def _money(value: Decimal) -> str:
    return format(value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP), ".4f")


def _ratio(numerator: Decimal, denominator: Decimal) -> str:
    if denominator == 0:
        raise ValueError("known-answer ratio denominator cannot be zero")
    return format((numerator / denominator).quantize(RATIO_QUANTUM, rounding=ROUND_HALF_UP), ".6f")


def _operating_totals(rows: Iterable[OperatingActualRecord]) -> dict[str, str]:
    selected = tuple(rows)
    revenue = _sum(row.revenue for row in selected)
    direct_cost = _sum(
        row.warehousing_cost + row.transportation_cost + row.other_direct_cost for row in selected
    )
    gross_profit = revenue - direct_cost
    return {
        "orders": _money(_sum(row.order_count for row in selected)),
        "shipments": _money(_sum(row.shipment_count for row in selected)),
        "revenue": _money(revenue),
        "direct_cost": _money(direct_cost),
        "gross_profit": _money(gross_profit),
        "gross_margin": _ratio(gross_profit, revenue),
    }


def _financial_sum(rows: Iterable[FinancialActualRecord], account_code: str) -> Decimal:
    return _sum(row.amount for row in rows if row.management_account_code == account_code)


def _headline(
    operating_rows: Iterable[OperatingActualRecord],
    financial_rows: Iterable[FinancialActualRecord],
) -> dict[str, str]:
    selected_financial = tuple(financial_rows)
    result = _operating_totals(operating_rows)
    operating_expense = _financial_sum(selected_financial, "OPERATING_EXPENSE")
    operating_profit = _financial_sum(selected_financial, "OPERATING_PROFIT")
    operating_cash_flow = _financial_sum(selected_financial, "OPERATING_CASH_FLOW")
    result.update(
        {
            "operating_expense": _money(operating_expense),
            "operating_profit": _money(operating_profit),
            "operating_cash_flow": _money(operating_cash_flow),
            "cash_conversion": _ratio(operating_cash_flow, operating_profit),
        }
    )
    return result


def _revenue_slice(
    rows: Iterable[OperatingActualRecord], key_for_row: dict[str, str] | None, attribute: str
) -> dict[str, str]:
    totals: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for row in rows:
        raw_key = str(getattr(row, attribute))
        key = key_for_row[raw_key] if key_for_row is not None else raw_key
        totals[key] += row.revenue
    return {key: _money(totals[key]) for key in sorted(totals)}


def _ar_answers(rows: Iterable[ArCollectionRecord]) -> dict[str, Any]:
    selected = tuple(rows)
    by_bucket: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    by_customer: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    overdue_by_customer: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for row in selected:
        by_bucket[row.aging_bucket or "invoice"] += row.receivable_balance
        by_customer[row.customer_code] += row.receivable_balance
        overdue_by_customer[row.customer_code] += row.overdue_amount
    return {
        "receivable_balance": _money(_sum(row.receivable_balance for row in selected)),
        "due_amount": _money(_sum(row.due_amount for row in selected)),
        "overdue_amount": _money(_sum(row.overdue_amount for row in selected)),
        "collected_amount": _money(_sum(row.collected_amount for row in selected)),
        "receivable_balance_by_bucket": {key: _money(by_bucket[key]) for key in sorted(by_bucket)},
        "receivable_balance_by_customer": {
            key: _money(by_customer[key]) for key in sorted(by_customer)
        },
        "overdue_amount_by_customer": {
            key: _money(overdue_by_customer[key]) for key in sorted(overdue_by_customer)
        },
    }


def calculate_known_answers(package: CanonicalPackage) -> dict[str, Any]:
    analysis_months = {
        period.month_key for period in package.periods if period.window == "analysis"
    }
    comparison_months = {
        period.month_key for period in package.periods if period.window == "comparison"
    }
    final_quarter_months = {"2026-06", "2026-07", "2026-08"}
    prior_final_quarter_months = {"2025-06", "2025-07", "2025-08"}

    analysis_operating = tuple(
        row for row in package.operating_actuals if row.month_key in analysis_months
    )
    comparison_operating = tuple(
        row for row in package.operating_actuals if row.month_key in comparison_months
    )
    analysis_financial = tuple(
        row for row in package.financial_actuals if row.month_key in analysis_months
    )
    comparison_financial = tuple(
        row for row in package.financial_actuals if row.month_key in comparison_months
    )

    analysis_headline = _headline(analysis_operating, analysis_financial)
    comparison_headline = _headline(comparison_operating, comparison_financial)
    budget_totals = {
        metric: _money(
            _sum(row.amount for row in package.monthly_budgets if row.metric_code == metric)
        )
        for metric in (
            "REVENUE",
            "DIRECT_COST",
            "OPERATING_EXPENSE",
            "OPERATING_PROFIT",
            "OPERATING_CASH_FLOW",
        )
    }

    customer_to_segment = {row.code: row.segment_code for row in package.customers}
    revenue_slices = {
        "by_segment": _revenue_slice(analysis_operating, customer_to_segment, "customer_code"),
        "by_product": _revenue_slice(analysis_operating, None, "logistics_product_code"),
        "by_organization": _revenue_slice(analysis_operating, None, "organization_code"),
        "by_region": _revenue_slice(analysis_operating, None, "region_code"),
        "by_month": _revenue_slice(analysis_operating, None, "month_key"),
    }

    operating_revenue = Decimal(analysis_headline["revenue"])
    financial_revenue = _financial_sum(analysis_financial, "REVENUE")
    operating_direct_cost = Decimal(analysis_headline["direct_cost"])
    financial_direct_cost = _sum(
        row.amount
        for row in analysis_financial
        if row.management_account_code
        in {"WAREHOUSING_COST", "TRANSPORTATION_COST", "OTHER_DIRECT_COST"}
    )
    reconciliation = {
        "operating_to_financial_revenue": {
            "operating": _money(operating_revenue),
            "financial": _money(financial_revenue),
            "difference": _money(operating_revenue - financial_revenue),
        },
        "operating_to_financial_direct_cost": {
            "operating": _money(operating_direct_cost),
            "financial": _money(financial_direct_cost),
            "difference": _money(operating_direct_cost - financial_direct_cost),
        },
    }

    final_month_ar = _ar_answers(
        row for row in package.ar_collections if row.month_key == package.batch.analysis_end_month
    )
    risk_overdue = sum(
        (
            Decimal(final_month_ar["overdue_amount_by_customer"][customer])
            for customer in ("CUST_KEY_01", "CUST_KEY_02")
        ),
        start=Decimal("0"),
    )
    total_overdue = Decimal(final_month_ar["overdue_amount"])

    final_q_operating = tuple(
        row for row in analysis_operating if row.month_key in final_quarter_months
    )
    prior_final_q_operating = tuple(
        row for row in comparison_operating if row.month_key in prior_final_quarter_months
    )
    final_q_financial = tuple(
        row for row in analysis_financial if row.month_key in final_quarter_months
    )
    final_q_budget_profit = _sum(
        row.amount
        for row in package.monthly_budgets
        if row.month_key in final_quarter_months and row.metric_code == "OPERATING_PROFIT"
    )

    analysis_by_product = {
        product.code: _operating_totals(
            row for row in analysis_operating if row.logistics_product_code == product.code
        )
        for product in package.logistics_products
    }
    comparison_by_product = {
        product.code: _operating_totals(
            row for row in comparison_operating if row.logistics_product_code == product.code
        )
        for product in package.logistics_products
    }
    budget_margin = Decimal("1") - Decimal("0.655")
    growth_product_below_budget_margin = any(
        Decimal(analysis_by_product[code]["revenue"])
        > Decimal(comparison_by_product[code]["revenue"])
        and Decimal(analysis_by_product[code]["gross_margin"]) < budget_margin
        for code in analysis_by_product
    )

    segment_orders: dict[str, dict[str, Decimal]] = {}
    for segment_code in customer_to_segment.values():
        segment_orders[segment_code] = {
            "analysis": _sum(
                row.order_count
                for row in analysis_operating
                if customer_to_segment[row.customer_code] == segment_code
            ),
            "comparison": _sum(
                row.order_count
                for row in comparison_operating
                if customer_to_segment[row.customer_code] == segment_code
            ),
        }

    final_q_totals = _operating_totals(final_q_operating)
    prior_final_q_totals = _operating_totals(prior_final_q_operating)
    final_q_transport = _sum(row.transportation_cost for row in final_q_operating)
    prior_final_q_transport = _sum(row.transportation_cost for row in prior_final_q_operating)
    final_q_orders = _sum(row.order_count for row in final_q_operating)
    prior_final_q_orders = _sum(row.order_count for row in prior_final_q_operating)
    final_q_profit = _financial_sum(final_q_financial, "OPERATING_PROFIT")

    row_counts = {
        "periods": len(package.periods),
        "organizations": len(package.organizations),
        "customer_segments": len(package.customer_segments),
        "customers": len(package.customers),
        "logistics_products": len(package.logistics_products),
        "regions": len(package.regions),
        "management_accounts": len(package.management_accounts),
        "scenario_versions": len(package.scenario_versions),
        "operating_actuals": len(package.operating_actuals),
        "financial_actuals": len(package.financial_actuals),
        "monthly_budgets": len(package.monthly_budgets),
        "ar_collections": len(package.ar_collections),
    }

    return {
        "contract_version": package.batch.contract_version,
        "batch_code": package.batch.batch_code,
        "windows": {
            "analysis": [package.batch.analysis_start_month, package.batch.analysis_end_month],
            "comparison": [
                package.batch.comparison_start_month,
                package.batch.comparison_end_month,
            ],
        },
        "row_counts": row_counts,
        "headline_totals": {
            "analysis": analysis_headline,
            "comparison": comparison_headline,
            "budget": budget_totals,
        },
        "revenue_slices": revenue_slices,
        "final_month_ar": final_month_ar,
        "final_quarter": {
            "actual": final_q_totals,
            "comparison": prior_final_q_totals,
            "actual_operating_profit": _money(final_q_profit),
            "budget_operating_profit": _money(final_q_budget_profit),
            "operating_profit_gap": _money(final_q_profit - final_q_budget_profit),
        },
        "reconciliation": reconciliation,
        "story_predicates": {
            "revenue_yoy_positive": Decimal(analysis_headline["revenue"])
            > Decimal(comparison_headline["revenue"]),
            "key_account_orders_yoy_negative": segment_orders["KEY_ACCOUNT"]["analysis"]
            < segment_orders["KEY_ACCOUNT"]["comparison"],
            "domestic_orders_yoy_positive": segment_orders["DOMESTIC"]["analysis"]
            > segment_orders["DOMESTIC"]["comparison"],
            "gross_margin_final_quarter_down": Decimal(final_q_totals["gross_margin"])
            < Decimal(prior_final_q_totals["gross_margin"]),
            "transport_cost_per_order_final_quarter_up": (final_q_transport / final_q_orders)
            > (prior_final_q_transport / prior_final_q_orders),
            "cash_conversion_below_one": Decimal(analysis_headline["cash_conversion"])
            < Decimal("1"),
            "overdue_ar_concentrated": risk_overdue / total_overdue > Decimal("0.25"),
            "growth_product_below_budget_margin": growth_product_below_budget_margin,
            "operating_profit_final_quarter_below_budget": final_q_profit < final_q_budget_profit,
        },
    }


def write_known_answers(package: CanonicalPackage, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(calculate_known_answers(package), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
