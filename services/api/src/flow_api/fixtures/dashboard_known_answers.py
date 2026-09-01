from __future__ import annotations

import json
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

DATABASE_FIXTURE_NAMESPACE = UUID("23cb1107-9809-59cc-8c5c-690900ce9ef1")
DASHBOARD_ORACLE_NAMESPACE = UUID("7b156574-0343-58e0-a7a7-6c44127a8fab")
MONEY = Decimal("0.0001")
SIX = Decimal("0.000001")
METRIC_DEFINITION_SET_HASH = (
    "4214ae85339eb7495defb69f1d59fdddec5e3183d5d4ba64c966be9f53270b38"
)
ANALYSIS_POLICY_HASH = (
    "448b390877b20090af02f6584e79a1c9796fe5ab0a5c9aeb784f6ab497e94f5a"
)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object in {path}")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _decimal(row: dict[str, Any], field: str) -> Decimal:
    return Decimal(str(row[field]))


def _sum(rows: list[dict[str, Any]], field: str) -> Decimal:
    return sum((_decimal(row, field) for row in rows), start=Decimal("0"))


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _six(value: Decimal) -> Decimal:
    return value.quantize(SIX, rounding=ROUND_HALF_UP)


def _string(value: Decimal, *, scale: int) -> str:
    return str(_money(value) if scale == 4 else _six(value))


def _id(entity: str, key: str) -> str:
    return str(uuid5(DATABASE_FIXTURE_NAMESPACE, f"{entity}:{key}"))


def _oracle_id(entity: str) -> str:
    return str(uuid5(DASHBOARD_ORACLE_NAMESPACE, entity))


def _available(
    value: Decimal | str,
    *,
    scale: int = 4,
    direction: str = "neutral",
) -> dict[str, Any]:
    exact = _string(value, scale=scale) if isinstance(value, Decimal) else value
    return {
        "status": "available",
        "exact_value": exact,
        "display_value": exact,
        "semantic_direction": direction,
        "unavailable_code": None,
        "unavailable_message": None,
    }


def _unavailable(
    code: str = "comparison_not_published",
    message: str = "当前口径未发布该比较值",
) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "exact_value": None,
        "display_value": "—",
        "semantic_direction": "neutral",
        "unavailable_code": code,
        "unavailable_message": message,
    }


def _percent_change(current: Decimal, comparison: Decimal) -> Decimal:
    if comparison == 0:
        raise ValueError("dashboard oracle comparison denominator cannot be zero")
    return (current - comparison) / comparison


def _direction(value: Decimal, *, inverse: bool = False) -> str:
    if value == 0:
        return "neutral"
    favorable = value > 0
    if inverse:
        favorable = not favorable
    return "positive" if favorable else "negative"


def _operating_totals(
    rows: list[dict[str, Any]], month: str
) -> dict[str, Decimal]:
    selected = [row for row in rows if row["month_key"] == month]
    revenue = _sum(selected, "revenue")
    orders = _sum(selected, "order_count")
    direct_cost = sum(
        (
            _decimal(row, "warehousing_cost")
            + _decimal(row, "transportation_cost")
            + _decimal(row, "other_direct_cost")
            for row in selected
        ),
        start=Decimal("0"),
    )
    return {
        "orders": orders,
        "revenue": revenue,
        "revenue_per_order": revenue / orders,
        "gross_margin": (revenue - direct_cost) / revenue,
        "fulfillment_cost_rate": direct_cost / revenue,
    }


def _financial_total(
    rows: list[dict[str, Any]], month: str, account: str
) -> Decimal:
    return sum(
        (
            _decimal(row, "amount")
            for row in rows
            if row["month_key"] == month and row["management_account_code"] == account
        ),
        start=Decimal("0"),
    )


def _ar_total(rows: list[dict[str, Any]], month: str) -> Decimal:
    return _sum([row for row in rows if row["month_key"] == month], "receivable_balance")


def _budget_month(rows: list[dict[str, Any]], month: str) -> dict[str, Decimal]:
    selected = [
        row
        for row in rows
        if row["month_key"] == month
        and row["organization_code"] is not None
        and row["customer_segment_code"] is None
        and row["logistics_product_code"] is None
    ]

    def total(code: str) -> Decimal:
        return sum(
            (_decimal(row, "amount") for row in selected if row["metric_code"] == code),
            start=Decimal("0"),
        )

    revenue = total("REVENUE")
    direct_cost = total("DIRECT_COST")
    operating_profit = total("OPERATING_PROFIT")
    operating_cash_flow = total("OPERATING_CASH_FLOW")
    return {
        "revenue": revenue,
        "gross_margin": (revenue - direct_cost) / revenue,
        "fulfillment_cost_rate": direct_cost / revenue,
        "operating_profit": operating_profit,
        "operating_cash_flow": operating_cash_flow,
    }


def _dimension_options(rows: list[dict[str, Any]], entity: str) -> list[dict[str, str]]:
    return [
        {
            "id": _id(entity, str(row["code"])),
            "code": str(row["code"]),
            "name": str(row["name"]),
        }
        for row in rows
    ]


def _card_value(
    metric_code: str,
    current: Decimal,
    comparison: Decimal | None,
    *,
    ratio_metric: bool,
    inverse: bool,
) -> dict[str, Any]:
    if comparison is None:
        return _unavailable()
    change = current - comparison if ratio_metric else _percent_change(current, comparison)
    return _available(
        change,
        scale=6,
        direction=_direction(change, inverse=inverse),
    )


def _build_metric_cards(
    metrics: dict[str, Any],
    operating: list[dict[str, Any]],
    financial: list[dict[str, Any]],
    ar_rows: list[dict[str, Any]],
    budgets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    current_month = "2026-08"
    prior_month = "2025-08"
    current = _operating_totals(operating, current_month)
    prior = _operating_totals(operating, prior_month)
    current.update(
        {
            "operating_profit": _financial_total(
                financial, current_month, "OPERATING_PROFIT"
            ),
            "operating_cash_flow": _financial_total(
                financial, current_month, "OPERATING_CASH_FLOW"
            ),
            "ar_balance": _ar_total(ar_rows, current_month),
        }
    )
    prior.update(
        {
            "operating_profit": _financial_total(
                financial, prior_month, "OPERATING_PROFIT"
            ),
            "operating_cash_flow": _financial_total(
                financial, prior_month, "OPERATING_CASH_FLOW"
            ),
            "ar_balance": _ar_total(ar_rows, prior_month),
        }
    )
    budget = _budget_month(budgets, current_month)
    actual_ytd = {key: Decimal(value) for key, value in metrics["actual_ytd"].items()}
    budget_ytd = {key: Decimal(value) for key, value in metrics["budget_ytd"].items()}
    definitions = (
        ("orders", "履约订单量", "规模", "order", False, False),
        ("revenue", "营业收入", "增长", "CNY", False, False),
        ("revenue_per_order", "单均收入", "价格/结构", "CNY/order", False, False),
        ("gross_margin", "毛利率", "盈利", "ratio", True, False),
        (
            "fulfillment_cost_rate",
            "履约成本率",
            "成本",
            "ratio",
            True,
            True,
        ),
        ("operating_profit", "经营利润", "利润", "CNY", False, False),
        ("ar_balance", "应收账款", "营运资本", "CNY", False, True),
        ("operating_cash_flow", "经营现金流", "现金", "CNY", False, False),
    )
    cards: list[dict[str, Any]] = []
    actual_month = metrics["actual_month"]
    for code, title, category, unit, ratio_metric, inverse in definitions:
        scale = 6 if ratio_metric or code == "revenue_per_order" else 4
        companion = None
        if code == "ar_balance":
            companion = _available(metrics["actual_month"]["dso"], scale=6)
        elif code == "operating_cash_flow":
            companion = _available(metrics["actual_month"]["cash_conversion"], scale=6)
        cards.append(
            {
                "metric_code": code,
                "title": title,
                "category": category,
                "unit": unit,
                "primary": _available(actual_month[code], scale=scale),
                "budget": _card_value(
                    code,
                    current[code],
                    budget.get(code),
                    ratio_metric=ratio_metric,
                    inverse=inverse,
                ),
                "yoy": _card_value(
                    code,
                    current[code],
                    prior[code],
                    ratio_metric=ratio_metric,
                    inverse=inverse,
                ),
                "ytd_budget": _card_value(
                    code,
                    actual_ytd[code],
                    budget_ytd.get(code),
                    ratio_metric=ratio_metric,
                    inverse=inverse,
                ),
                "companion": companion,
            }
        )
    return cards


def _build_trends(
    operating: list[dict[str, Any]], financial: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    months = sorted({str(row["month_key"]) for row in operating if row["month_key"] >= "2025-09"})
    points: list[dict[str, Any]] = []
    for month in months:
        totals = _operating_totals(operating, month)
        points.append(
            {
                "month": month,
                "metric_snapshot_id": _oracle_id(f"metric-snapshot:{month}"),
                "revenue": _available(totals["revenue"]),
                "operating_profit": _available(
                    _financial_total(financial, month, "OPERATING_PROFIT")
                ),
                "gross_margin": _available(totals["gross_margin"], scale=6),
                "operating_cash_flow": _available(
                    _financial_total(financial, month, "OPERATING_CASH_FLOW")
                ),
            }
        )
    return points


def _product_actuals(
    operating: list[dict[str, Any]], month: str
) -> dict[str, dict[str, Decimal]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in operating:
        if row["month_key"] == month:
            grouped[str(row["logistics_product_code"])].append(row)
    result: dict[str, dict[str, Decimal]] = {}
    for code, rows in grouped.items():
        revenue = _sum(rows, "revenue")
        orders = _sum(rows, "order_count")
        direct_cost = sum(
            (
                _decimal(row, "warehousing_cost")
                + _decimal(row, "transportation_cost")
                + _decimal(row, "other_direct_cost")
                for row in rows
            ),
            start=Decimal("0"),
        )
        result[code] = {
            "revenue": revenue,
            "orders": orders,
            "gross_margin": (revenue - direct_cost) / revenue,
            "fulfillment_cost_rate": direct_cost / revenue,
        }
    return result


def _build_products(
    operating: list[dict[str, Any]], products: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    current = _product_actuals(operating, "2026-08")
    prior = _product_actuals(operating, "2025-08")
    rows: list[dict[str, Any]] = []
    for product in products:
        code = str(product["code"])
        values = current[code]
        comparison = prior[code]
        revenue_change = _percent_change(values["revenue"], comparison["revenue"])
        order_change = _percent_change(values["orders"], comparison["orders"])
        margin_change = values["gross_margin"] - comparison["gross_margin"]
        rows.append(
            {
                "logistics_product_id": _id("logistics_product", code),
                "code": code,
                "name": str(product["name"]),
                "revenue": _available(values["revenue"]),
                "orders": _available(values["orders"]),
                "gross_margin": _available(values["gross_margin"], scale=6),
                "fulfillment_cost_rate": _available(
                    values["fulfillment_cost_rate"], scale=6
                ),
                "revenue_comparison": _available(
                    revenue_change, scale=6, direction=_direction(revenue_change)
                ),
                "orders_comparison": _available(
                    order_change, scale=6, direction=_direction(order_change)
                ),
                "gross_margin_comparison": _available(
                    margin_change, scale=6, direction=_direction(margin_change)
                ),
            }
        )
    rows.sort(key=lambda row: Decimal(row["revenue"]["exact_value"]), reverse=True)
    return rows


def _segment_product_actuals(
    operating: list[dict[str, Any]],
    customer_segment_by_customer: dict[str, str],
    month: str,
) -> dict[tuple[str, str], Decimal]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in operating:
        if row["month_key"] != month:
            continue
        key = (
            customer_segment_by_customer[str(row["customer_code"])],
            str(row["logistics_product_code"]),
        )
        grouped[key].append(row)
    result: dict[tuple[str, str], Decimal] = {}
    for key, rows in grouped.items():
        revenue = _sum(rows, "revenue")
        cost = sum(
            (
                _decimal(row, "warehousing_cost")
                + _decimal(row, "transportation_cost")
                + _decimal(row, "other_direct_cost")
                for row in rows
            ),
            start=Decimal("0"),
        )
        result[key] = (revenue - cost) / revenue
    return result


def _build_matrix(
    operating: list[dict[str, Any]],
    customers: list[dict[str, Any]],
    segments: list[dict[str, Any]],
    products: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    segment_by_customer = {
        str(row["code"]): str(row["segment_code"]) for row in customers
    }
    current = _segment_product_actuals(operating, segment_by_customer, "2026-08")
    prior = _segment_product_actuals(operating, segment_by_customer, "2025-08")
    cells: list[dict[str, Any]] = []
    for segment in segments:
        for product in products:
            key = (str(segment["code"]), str(product["code"]))
            change = current[key] - prior[key]
            cells.append(
                {
                    "customer_segment_id": _id("customer_segment", key[0]),
                    "logistics_product_id": _id("logistics_product", key[1]),
                    "actual_margin": _available(current[key], scale=6),
                    "comparison": _available(
                        change, scale=6, direction=_direction(change)
                    ),
                }
            )
    return cells


def build_dashboard_known_answers(repository_root: Path) -> dict[str, Any]:
    canonical = repository_root / "fixtures/canonical"
    expected = repository_root / "fixtures/expected"
    metrics = _read_json(expected / "metric_snapshots_v1.json")
    analysis = _read_json(expected / "analysis_results_v1.json")
    operating = _read_jsonl(canonical / "operating_actuals.jsonl")
    financial = _read_jsonl(canonical / "financial_actuals.jsonl")
    ar_rows = _read_jsonl(canonical / "ar_collections.jsonl")
    budgets = _read_jsonl(canonical / "monthly_budgets.jsonl")
    organizations = _read_jsonl(canonical / "organizations.jsonl")
    segments = _read_jsonl(canonical / "customer_segments.jsonl")
    customers = _read_jsonl(canonical / "customers.jsonl")
    products = _read_jsonl(canonical / "logistics_products.jsonl")
    regions = _read_jsonl(canonical / "regions.jsonl")
    batch_id = _oracle_id("batch")
    import_version_id = _oracle_id("import-version")
    metric_snapshot_id = _oracle_id("metric-snapshot:2026-08")
    analysis_run_id = _oracle_id("analysis-run")
    titles = {
        "fulfillment_cost_increase": "履约成本增加",
        "revenue_growth": "收入增长",
        "ar_cash_deterioration": "应收资金占用增加",
        "operating_profit_deterioration": "经营利润下降",
    }
    result_codes = {
        "fulfillment_cost_increase": "fulfillment_cost_rve",
        "revenue_growth": "revenue_vpm",
        "ar_cash_deterioration": "ar_cash_impact",
        "operating_profit_deterioration": "operating_profit_bridge",
    }
    findings = []
    for position, (finding_type, score) in enumerate(
        zip(analysis["finding_rank"], analysis["finding_scores"], strict=True), start=1
    ):
        finding_id = _oracle_id(f"finding:{finding_type}")
        impact = analysis["results"][result_codes[finding_type]]["impact_amount"]
        path = (
            f"/investigations/{finding_id}?batch_id={batch_id}"
            f"&metric_snapshot_id={metric_snapshot_id}&analysis_run_id={analysis_run_id}"
        )
        findings.append(
            {
                "finding_id": finding_id,
                "finding_type": finding_type,
                "title": titles[finding_type],
                "impact": _available(
                    impact,
                    direction=(
                        "positive" if finding_type == "revenue_growth" else "negative"
                    ),
                ),
                "total_score": score,
                "comparison_basis": "prior_year",
                "evidence_verified": 5,
                "evidence_total": 5,
                "scope": "global",
                "investigation_path": path,
                "position": position,
            }
        )
    for item in findings:
        item.pop("position")
    bridge = analysis["results"]["operating_profit_bridge"]
    driver_labels = {
        "revenue_volume": "收入业务量",
        "revenue_mix": "收入结构",
        "revenue_price": "收入单价",
        "warehousing_cost": "仓储成本",
        "transportation_cost": "运输成本",
        "other_direct_cost": "其他直接成本",
        "operating_expense": "期间费用",
    }
    trend_points = _build_trends(operating, financial)
    product_rows = _build_products(operating, products)
    segment_options = _dimension_options(segments, "customer_segment")
    product_options = _dimension_options(products, "logistics_product")
    return {
        "state": "ready",
        "context": {
            "batch_id": batch_id,
            "import_version_id": import_version_id,
            "metric_snapshot_id": metric_snapshot_id,
            "analysis_run_id": analysis_run_id,
            "as_of_month": "2026-08",
            "metric_definition_set_id": "flow.metrics.logistics.v1",
            "metric_definition_set_hash": METRIC_DEFINITION_SET_HASH,
            "metric_engine_version": "flow.metrics.engine.v1",
            "analysis_policy_id": "flow.analysis.logistics.v1",
            "analysis_policy_hash": ANALYSIS_POLICY_HASH,
            "analysis_engine_version": "flow-analysis/1",
            "generated_at": "2026-09-01T00:00:00Z",
        },
        "filter_options": {
            "dimensions": [
                {
                    "dimension": "organization",
                    "label": "组织",
                    "options": _dimension_options(organizations, "organization"),
                },
                {
                    "dimension": "customer_segment",
                    "label": "客户群",
                    "options": segment_options,
                },
                {
                    "dimension": "logistics_product",
                    "label": "物流产品",
                    "options": product_options,
                },
                {
                    "dimension": "region",
                    "label": "区域",
                    "options": _dimension_options(regions, "region"),
                },
            ],
            "supported_combinations": [
                [],
                ["organization"],
                ["customer_segment"],
                ["logistics_product"],
                ["region"],
                ["customer_segment", "logistics_product"],
            ],
        },
        "active_filters": {
            "period_view": "month",
            "organization_id": None,
            "customer_segment_id": None,
            "logistics_product_id": None,
            "region_id": None,
            "is_total_scope": True,
        },
        "data_status": {
            "batch_status": "published",
            "import_status": "published",
            "quality_status": "passed",
            "blocking_issue_count": 0,
            "warning_issue_count": 0,
            "acknowledged_warning_count": 0,
            "reconciliation_status": "passed",
            "metric_snapshot_status": "published",
            "analysis_run_status": "published",
            "freshness_status": "fresh",
        },
        "metric_cards": _build_metric_cards(
            metrics, operating, financial, ar_rows, budgets
        ),
        "trends": {
            "status": "complete",
            "coverage_count": len(trend_points),
            "expected_count": 12,
            "missing_months": [],
            "points": trend_points,
            "degradation_message": None,
        },
        "profit_bridge": {
            "status": "complete",
            "comparison_basis": "prior_year",
            "impact": _available(bridge["impact_amount"], direction="negative"),
            "reconciliation_status": "passed",
            "reconciliation_difference": "0.0000",
            "drivers": [
                {
                    "driver_code": driver["code"],
                    "label": driver_labels[driver["code"]],
                    "contribution": _available(
                        driver["amount"],
                        direction=(
                            "positive"
                            if Decimal(driver["amount"]) > 0
                            else "negative"
                        ),
                    ),
                }
                for driver in bridge["drivers"]
            ],
            "degradation_message": None,
        },
        "findings": findings,
        "product_table": {
            "status": "complete",
            "comparison_label": "同比",
            "rows": product_rows,
            "degradation_message": None,
        },
        "margin_matrix": {
            "status": "complete",
            "comparison_label": "同比",
            "rows": segment_options,
            "columns": product_options,
            "cells": _build_matrix(
                operating, customers, segments, products
            ),
            "degradation_message": None,
        },
        "highlights": [
            {
                "finding_id": item["finding_id"],
                "title": item["title"],
                "impact_display": item["impact"]["display_value"],
            }
            for item in findings[:3]
        ],
        "degradations": [],
    }


__all__ = ["build_dashboard_known_answers"]
