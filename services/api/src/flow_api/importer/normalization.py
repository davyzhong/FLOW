"""导入账套指标派生（九页接线第一阶段）。

边界：只从科目余额表可**真实推导**的口径生成指标值，逐项带推导公式；
无法从余额表得出的指标（毛利率、DSO、经营现金流等）一律不生成，不虚构。
不写治理发布链（MetricSnapshot/MetricDefinition），独立只读视图。
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from flow_api.importer.store import ImportStore

_ZERO = Decimal("0")


def derive_metrics(store: ImportStore, dataset_id: str) -> dict[str, Any] | None:
    """从科目余额行派生七项可推导指标 + 每项推导公式。"""
    balances = store.dataset_balances(dataset_id)
    if not balances:
        return None
    assets = liabilities = equity = _ZERO
    revenue = expenses = _ZERO
    periods: set[str] = set()
    for row in balances:
        periods.add(row["period"])
        category = row["account_category"]
        closing = row["closing_balance"]
        if category == "资产":
            assets += closing
        elif category == "负债":
            liabilities += closing
        elif category == "权益":
            equity += closing
        elif category == "损益":
            revenue += row["credit_amount"]
            expenses += row["debit_amount"]
    net_profit = revenue - expenses
    debt_ratio = (liabilities / assets).quantize(Decimal("0.0001")) if assets else None

    def metric(
        code: str, label: str, value: Decimal | None, unit: str, formula: str
    ) -> dict[str, Any]:
        return {
            "metric_code": code,
            "label": label,
            "value": None if value is None else str(value),
            "unit": unit,
            "formula": formula,
        }

    metrics = [
        metric("revenue", "营业收入", revenue, "CNY", "损益类科目本期贷方发生额合计"),
        metric(
            "total_expenses",
            "费用总额",
            expenses,
            "CNY",
            "损益类科目本期借方发生额合计",
        ),
        metric(
            "net_profit",
            "净利润",
            net_profit,
            "CNY",
            "营业收入 − 费用总额（损益类贷方 − 借方发生额）",
        ),
        metric(
            "total_assets",
            "资产总计",
            assets,
            "CNY",
            "资产类科目期末余额（借向）合计",
        ),
        metric(
            "total_liabilities",
            "负债总计",
            liabilities,
            "CNY",
            "负债类科目期末余额（贷向）合计",
        ),
        metric(
            "total_equity",
            "权益总计",
            equity,
            "CNY",
            "权益类科目期末余额（贷向）合计",
        ),
        metric(
            "debt_ratio",
            "资产负债率",
            debt_ratio,
            "ratio",
            "负债总计 ÷ 资产总计",
        ),
    ]
    return {
        "dataset_id": dataset_id,
        "periods": sorted(periods),
        "account_count": len(balances),
        "metrics": metrics,
        "excluded_note": (
            "毛利率、DSO、经营现金流等指标需要收入/成本分项、账龄或现金流量表数据，"
            "科目余额表无法推导，一律不生成（不虚构口径）。"
        ),
        "source_note": (
            "导入账套派生指标；未进入治理发布链，"
            "与九页驾驶舱（大麦演示数据治理链）数值互不混用。"
        ),
    }
