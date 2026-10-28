"""导入数据概览驾驶舱（R2b）：从科目余额表直接派生的 KPI 视图。

边界：不写治理发布链（AnalysisRun/MetricSnapshot），只读校验视图。
九页驾驶舱全量接线需要归一化管线设计，属后续阶段；本视图让导入数据立即可查。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from flow_api.importer.store import ImportStore

_ZERO = Decimal("0")


def cockpit_overview(store: ImportStore, dataset_id: str) -> dict[str, Any] | None:
    """聚合导入账套的六项核心 KPI + 勾稽校验。

    - 资产/负债/权益总计：期末余额按类别×方向聚合
    - 资产负债率：负债总计 ÷ 资产总计
    - 本期净利润：损益类贷方发生额（收入）− 借方发生额（费用）
    - 勾稽：资产 −(负债+权益)，非零说明类别标注或科目余额有误
    """
    balances = store.dataset_balances(dataset_id)
    if not balances:
        return None
    assets = liabilities = equity = _ZERO
    pnl_credit = pnl_debit = _ZERO
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
            pnl_credit += row["credit_amount"]
            pnl_debit += row["debit_amount"]
    net_profit = pnl_credit - pnl_debit
    debt_ratio = (liabilities / assets).quantize(Decimal("0.0001")) if assets else None
    identity = assets - liabilities - equity
    return {
        "dataset_id": dataset_id,
        "periods": sorted(periods),
        "account_count": len(balances),
        "kpi": [
            {"code": "total_assets", "label": "资产总计", "value": str(assets), "unit": "CNY"},
            {
                "code": "total_liabilities",
                "label": "负债总计",
                "value": str(liabilities),
                "unit": "CNY",
            },
            {"code": "total_equity", "label": "权益总计", "value": str(equity), "unit": "CNY"},
            {"code": "net_profit", "label": "本期净利润", "value": str(net_profit), "unit": "CNY"},
            {
                "code": "debt_ratio",
                "label": "资产负债率",
                "value": (str(debt_ratio) if debt_ratio is not None else None),
                "unit": "ratio",
            },
        ],
        "identity_check": {
            "formula": "资产总计 − 负债总计 − 权益总计",
            "value": str(identity),
            "passed": identity == _ZERO,
        },
        "source_note": "导入账套只读校验视图；未进入治理发布链，不与九页驾驶舱数值混用。",
    }
