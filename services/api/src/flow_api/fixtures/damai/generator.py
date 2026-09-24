"""大麦 canonical 数据集生成器（Task 2）。

确定性保证：固定随机种子（Random(42)）、Decimal 全程、UUID5 派生实体 ID；
相同 profile 版本产生字节一致的数据包。生成器不读数据库。
"""

from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from decimal import Decimal
from typing import Any

from flow_api.fixtures.damai.profile import (
    ANALYSIS_MONTHS,
    BUSINESS_FAMILIES,
    BUSINESS_UNITS,
    CUSTOMERS,
    DAMAI_PROFILE_V1,
    PLANTED_EVENTS,
    PRIOR_MONTHS,
    PRODUCTS,
    REGIONS,
)

_WAN = Decimal("1")  # 内部单位：万元
_RANDOM_SEED = 42
# 月度季节系数（确定性基线：Q4 旺季、2 月淡季）
_SEASONALITY = {
    1: Decimal("0.95"), 2: Decimal("0.82"), 3: Decimal("0.98"),
    4: Decimal("1.00"), 5: Decimal("1.02"), 6: Decimal("1.00"),
    7: Decimal("1.00"), 8: Decimal("1.02"), 9: Decimal("1.05"),
    10: Decimal("1.08"), 11: Decimal("1.12"), 12: Decimal("1.10"),
}
_Q4 = {10, 11, 12}


def _month_of(month: str) -> int:
    return int(month.split("-")[1])


def _d(value: Decimal, places: str = "0.0001") -> Decimal:
    return value.quantize(Decimal(places))


def _family_month_revenues(
    months: tuple[str, ...],
    month_targets: dict[str, Decimal],
) -> dict[str, dict[str, Decimal]]:
    """按月给三业务族分配收入（权重 × 确定性扰动），族之和恰等于月度目标。

    month_targets 已含季节系数；scale 仅消除舍入残差，不得抵消季节。
    """

    rng = random.Random(_RANDOM_SEED)
    weights = {f.family_id: f.target_weight for f in BUSINESS_FAMILIES}
    result: dict[str, dict[str, Decimal]] = {}
    for month in months:
        target = month_targets[month]
        raw: dict[str, Decimal] = {}
        for family_id, weight in weights.items():
            jitter = Decimal(str(rng.uniform(0.97, 1.03)))
            raw[family_id] = target * weight * jitter
        scale = target / sum(raw.values(), Decimal("0"))
        result[month] = {fid: _d(v * scale) for fid, v in raw.items()}
    return result


def build_damai_package() -> dict[str, Any]:
    """构建大麦 canonical 数据包（确定性；不读数据库、不用随机数）。"""

    profile = DAMAI_PROFILE_V1
    revenue_low, _ = profile.annual_revenue_target
    analysis_total = (revenue_low + Decimal("500000"))  # 目标区间中值：1,100 亿
    analysis_base = _d(analysis_total / Decimal("12"))
    prior_base = _d(analysis_base / Decimal("1.18"))  # 同比增长约 18%

    random.Random(_RANDOM_SEED + 1)

    operating_actual: list[dict[str, Any]] = []
    family_actual: list[dict[str, Any]] = []
    all_months = (*PRIOR_MONTHS, *ANALYSIS_MONTHS)
    month_targets = {
        month: _d(
            (analysis_base if month in ANALYSIS_MONTHS else prior_base)
            * _SEASONALITY[_month_of(month)]
        )
        for month in all_months
    }
    by_family_by_month = _family_month_revenues(all_months, month_targets)

    for month in all_months:
        month_index = ANALYSIS_MONTHS.index(month) if month in ANALYSIS_MONTHS else None
        by_family = by_family_by_month[month]
        for family in BUSINESS_FAMILIES:
            revenue = by_family[family.family_id]
            # 毛利率路径：基线 10%；跨境 Q4 承压 −1.5pp；国内后期改善 +0.8pp（E1/E2）
            margin = Decimal("0.10")
            in_analysis_late = month_index is not None and month_index >= 6
            is_q4_intl = (
                family.family_id == "international_cross_border"
                and month_index is not None
                and _month_of(month) in _Q4
            )
            if is_q4_intl:
                margin -= Decimal("0.015")
            if family.family_id == "china_logistics" and in_analysis_late:
                margin += Decimal("0.008")
            cost = _d(revenue * (Decimal("1") - margin))
            unit = BUSINESS_UNITS[
                (hash(family.family_id) + _month_of(month)) % len(BUSINESS_UNITS)
            ]
            operating_actual.append(
                {
                    "month": month,
                    "business_unit": unit,
                    "family_id": family.family_id,
                    "region": REGIONS[_month_of(month) % len(REGIONS)],
                    "customer_id": "AGGREGATE",
                    "product": "AGGREGATE",
                    "revenue": str(revenue),
                    "cost": str(cost),
                    "gross_profit": str(revenue - cost),
                }
            )
            family_actual.append(
                {
                    "month": month,
                    "family_id": family.family_id,
                    "revenue": str(revenue),
                    "cost": str(cost),
                }
            )

    # 财务实际：经营收入逐月精确对账
    financial_actual = []
    for month in (*PRIOR_MONTHS, *ANALYSIS_MONTHS):
        revenue = sum(
            (
                Decimal(str(r["revenue"]))
                for r in operating_actual
                if r["month"] == month
            ),
            Decimal("0"),
        )
        financial_actual.append({"month": month, "revenue": str(revenue)})

    # 预算：仅分析期，收入 = 实际 × 1.03（保证 E4 某区域可低于预算）
    budget = []
    for month in ANALYSIS_MONTHS:
        actual_revenue = sum(
            (
                Decimal(str(r["revenue"]))
                for r in operating_actual
                if r["month"] == month
            ),
            Decimal("0"),
        )
        budget.append(
            {
                "month": month,
                "revenue": str(_d(actual_revenue * Decimal("1.03"))),
                "scenario": "budget-v1",
            }
        )

    # AR 账龄：分析期应收余额；E3 两大客户后期账龄恶化
    ar_aging: list[dict[str, Any]] = []
    for index, month in enumerate(ANALYSIS_MONTHS):
        revenue = sum(
            (
                Decimal(str(r["revenue"]))
                for r in operating_actual
                if r["month"] == month
            ),
            Decimal("0"),
        )
        outstanding = _d(revenue * Decimal("0.35"))
        deterioration = Decimal("1") + Decimal("0.35") * (
            index >= 6
        )  # 后 6 个月恶化
        b_current = _d(outstanding * Decimal("0.70"))
        b_31_60 = _d(outstanding * Decimal("0.12") * deterioration)
        b_61_90 = _d(outstanding * Decimal("0.10") * deterioration)
        b_90_plus = outstanding - b_current - b_31_60 - b_61_90
        collected = _d(revenue * Decimal("0.88"))
        ar_aging.append(
            {
                "month": month,
                "ar_outstanding": str(outstanding),
                "b_current": str(b_current),
                "b_31_60": str(b_31_60),
                "b_61_90": str(b_61_90),
                "b_90_plus": str(b_90_plus),
                "collected": str(collected),
                "deterioration_customers": ["DM-CUST-007", "DM-CUST-019"]
                if index >= 6
                else [],
            }
        )

    # 经营现金流：经营利润 + 背离调整（E5：第 9/10 月现金流反常走低）
    operating_profit_by_month: dict[str, Decimal] = defaultdict(Decimal)
    for row in operating_actual:
        operating_profit_by_month[row["month"]] += Decimal(
            str(row["gross_profit"])
        )
    expense_rate = Decimal("0.06")
    cash_flow = []
    for month in (*PRIOR_MONTHS, *ANALYSIS_MONTHS):
        profit = operating_profit_by_month[month] * (Decimal("1") - expense_rate)
        ocf = profit
        if month in ("2026-05", "2026-06"):
            ocf = profit * Decimal("0.55")  # E5：利润-现金短期背离
        cash_flow.append(
            {"month": month, "operating_profit": str(_d(profit)), "ocf": str(_d(ocf))}
        )

    # forecast sidecar：分析期逐月预测收入（static-only）
    forecast_rows = []
    for month in ANALYSIS_MONTHS:
        forecast_rows.append(
            {
                "month": month,
                "forecast_revenue": str(
                    _d(analysis_base * _SEASONALITY[_month_of(month)])
                ),
            }
        )
    forecast_body = json.dumps(forecast_rows, sort_keys=True).encode()
    forecast_sidecar = {
        "version": "damai-forecast-v1",
        "persistence": "static-only",
        "page_coverage": "excluded",
        "sha256": hashlib.sha256(forecast_body).hexdigest(),
        "rows": forecast_rows,
    }

    return {
        "profile_version": DAMAI_PROFILE_V1.profile_version,
        "enterprise": {
            "code": profile.enterprise_code,
            "name": profile.enterprise_name,
            "uuid": str(profile.enterprise_uuid),
            "synthetic": True,
        },
        "master_data": {
            "business_units": [
                {"unit_id": f"BU-{i:02d}", "name": name}
                for i, name in enumerate(BUSINESS_UNITS, 1)
            ],
            "regions": [
                {"region_id": f"R-{i:02d}", "name": name}
                for i, name in enumerate(REGIONS, 1)
            ],
            "customers": [
                {"customer_id": f"DM-CUST-{i:03d}", "name": name, "synthetic": True}
                for i, name in enumerate(CUSTOMERS, 1)
            ],
            "products": [
                {"product_id": f"P-{i:02d}", "name": name} for i, name in enumerate(PRODUCTS, 1)
            ],
        },
        "monthly_facts": {
            "operating_actual": operating_actual,
            "family_actual": family_actual,
            "financial_actual": financial_actual,
            "budget": budget,
            "ar_aging": ar_aging,
            "cash_flow": cash_flow,
        },
        "forecast_sidecar": forecast_sidecar,
        "planted_events": [
            {"event_id": e.event_id, "kind": e.kind, "scope": e.scope, "note": e.note}
            for e in PLANTED_EVENTS
        ],
    }


__all__ = ["build_damai_package"]
