"""大麦 canonical 数据集生成器（Task 2 / Task A2 明细粒度）。

确定性保证：固定随机种子（Random(42)）、Decimal 全程、UUID5 派生实体 ID；
相同 profile 版本产生字节一致的数据包。生成器不读数据库。

粒度（规格 §3.3 / 计划 v2.4 Task A2）：
- 经营明细 24 月 × 40 客户 × 2 产品 = 1,920 行（族月总额为控制总量，
  按客户规模权重 × 产品权重分摊，尾差并入末行保恒等）；
- 预算 12 月 × 4 单元 × 4 客群 × 8 产品 × 7 行 = 10,752 行，单元格内
  收入 − 三成本 − 费用 = 经营利润 精确闭合；OCF = 经营利润 × 0.92；
- AR 24 月 × 40 客户 × 5 桶 = 4,800 行，未到期 + 逾期 = 余额，非负；
- 植入事件 E1/E2（族毛利率路径）、E3（DM-CUST-007/019 账龄 2026-03 起恶化）、
  E4（国内仓配事业部预算 ×1.12 使实际低于预算）、E5（2026-05/06 利润现金背离）、
  E6（分析期后 6 月部分客户第二产品轮换）均可追溯至明细行。
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
    CUSTOMER_ASSIGNMENTS,
    CUSTOMER_SEGMENTS,
    CUSTOMERS,
    DAMAI_PROFILE_V1,
    PLANTED_EVENTS,
    PRIOR_MONTHS,
    PRODUCT_ASSIGNMENTS,
    PRODUCT_MARGIN_OFFSET,
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

_PRODUCT_IDS: tuple[str, ...] = tuple(f"P-{i:02d}" for i in range(1, 9))
_PRODUCT_FAMILY: dict[str, str] = {
    pid: PRODUCT_ASSIGNMENTS[pid]["family_id"] for pid in _PRODUCT_IDS
}
_PRODUCT_UNIT: dict[str, str] = {
    pid: PRODUCT_ASSIGNMENTS[pid]["business_unit"] for pid in _PRODUCT_IDS
}
# 产品收入权重（族内分摊用，确定性常数）
_PRODUCT_WEIGHT: dict[str, Decimal] = {
    "P-01": Decimal("3"), "P-02": Decimal("2"), "P-03": Decimal("2"),
    "P-04": Decimal("3"), "P-05": Decimal("2"), "P-06": Decimal("2"),
    "P-07": Decimal("1"), "P-08": Decimal("1"),
}
# 客户规模权重：编号越小规模越大（41 − 编号）
_CUSTOMER_SCALE: dict[int, Decimal] = {i: Decimal(41 - i) for i in range(1, 41)}

# 预算成本/费用率（占预算收入比，和 = 0.96，经营利润率 4%）
_BUDGET_COST_RATES: tuple[tuple[str, Decimal], ...] = (
    ("WAREHOUSING_COST", Decimal("0.27")),
    ("TRANSPORTATION_COST", Decimal("0.54")),
    ("OTHER_DIRECT_COST", Decimal("0.09")),
)
_BUDGET_EXPENSE_RATE = Decimal("0.06")
_BUDGET_OCF_RATE = Decimal("0.92")  # 营运资本调节 8%（记 manifest 血缘）
_BUDGET_MULTIPLIER = Decimal("1.03")
_BUDGET_MULTIPLIER_E4 = Decimal("1.12")  # 国内仓配事业部：实际低于预算（E4）
_E4_UNIT = "国内仓配事业部"

# AR 账龄桶基准占比（90+ 取尾差，保证五桶之和恒等于余额）
_AR_BUCKET_RATES: tuple[tuple[str, Decimal], ...] = (
    ("current", Decimal("0.70")),
    ("1-30", Decimal("0.12")),
    ("31-60", Decimal("0.08")),
    ("61-90", Decimal("0.06")),
)
_E3_CUSTOMERS = ("DM-CUST-007", "DM-CUST-019")
_E3_START_MONTH = "2026-03"
_E3_OVERDUE_FACTOR = Decimal("1.35")
_E3_COLLECT_FACTOR = Decimal("0.75")
_AR_COLLECT_RATE = Decimal("0.88")


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


def _active_products(customer_index: int, month: str) -> tuple[int, int]:
    """客户活跃产品（0-based 序号）。常规每客户 2 个；E6 组合轮换：

    分析期后 6 个月起，index % 8 ∈ {0, 2} 的客户第二产品由 (2i+1)%8 轮换至
    (2i+3)%8——P-02/P-06 收缩、P-04/P-08 扩张，且每月 8 产品仍全覆盖。
    """

    first = (2 * customer_index) % 8
    second = (2 * customer_index + 1) % 8
    if (
        month in ANALYSIS_MONTHS
        and ANALYSIS_MONTHS.index(month) >= 6
        and customer_index % 8 in (0, 2)
    ):
        second = (2 * customer_index + 3) % 8
    return first, second


def _row_margin(family_id: str, product_id: str, month: str) -> Decimal:
    """行毛利率 = 族基线 10% + E1/E2 族级调整 + 产品偏移。"""

    margin = Decimal("0.10") + PRODUCT_MARGIN_OFFSET[product_id]
    month_index = ANALYSIS_MONTHS.index(month) if month in ANALYSIS_MONTHS else None
    if (
        family_id == "international_cross_border"
        and month_index is not None
        and _month_of(month) in _Q4
    ):
        margin -= Decimal("0.015")  # E1：跨境旺季毛利率承压
    if family_id == "china_logistics" and month_index is not None and month_index >= 6:
        margin += Decimal("0.008")  # E2：国内仓配效率改善
    return margin


def build_damai_package() -> dict[str, Any]:
    """构建大麦 canonical 数据包（确定性；不读数据库、不用进程随机数）。"""

    profile = DAMAI_PROFILE_V1
    revenue_low, _ = profile.annual_revenue_target
    analysis_total = revenue_low + Decimal("500000")  # 目标区间中值：1,100 亿
    analysis_base = _d(analysis_total / Decimal("12"))
    prior_base = _d(analysis_base / Decimal("1.18"))  # 同比增长约 18%

    operating_actual: list[dict[str, Any]] = []
    all_months = (*PRIOR_MONTHS, *ANALYSIS_MONTHS)
    month_targets = {
        month: _d(
            (analysis_base if month in ANALYSIS_MONTHS else prior_base)
            * _SEASONALITY[_month_of(month)]
        )
        for month in all_months
    }
    by_family_by_month = _family_month_revenues(all_months, month_targets)

    # 经营明细：族月总额为控制总量，按 客户规模 × 产品权重 分摊到
    # (客户, 产品) 明细行，尾差并入该族当月最后一行，保证族之和恒等。
    for month in all_months:
        by_family = by_family_by_month[month]
        active: dict[str, list[tuple[int, int]]] = {
            f.family_id: [] for f in BUSINESS_FAMILIES
        }
        for customer_index in range(40):
            for product_index in _active_products(customer_index, month):
                product_id = _PRODUCT_IDS[product_index]
                active[_PRODUCT_FAMILY[product_id]].append(
                    (customer_index, product_index)
                )
        for family in BUSINESS_FAMILIES:
            family_total = by_family[family.family_id]
            pairs = active[family.family_id]
            weights = [
                _CUSTOMER_SCALE[ci + 1] * _PRODUCT_WEIGHT[_PRODUCT_IDS[pi]]
                for ci, pi in pairs
            ]
            weight_sum = sum(weights, Decimal("0"))
            running = Decimal("0")
            for position, ((ci, pi), weight) in enumerate(
                zip(pairs, weights, strict=True)
            ):
                product_id = _PRODUCT_IDS[pi]
                if position < len(pairs) - 1:
                    revenue = _d(family_total * weight / weight_sum)
                    running += revenue
                else:  # 尾差并入末行
                    revenue = family_total - running
                margin = _row_margin(family.family_id, product_id, month)
                cost = _d(revenue * (Decimal("1") - margin))
                customer_id = f"DM-CUST-{ci + 1:03d}"
                operating_actual.append(
                    {
                        "month": month,
                        "business_unit": _PRODUCT_UNIT[product_id],
                        "family_id": family.family_id,
                        "region": CUSTOMER_ASSIGNMENTS[customer_id]["primary_region"],
                        "customer_id": customer_id,
                        "product": product_id,
                        "revenue": str(revenue),
                        "cost": str(cost),
                        "gross_profit": str(revenue - cost),
                    }
                )

    # 业务族汇总 = 明细精确聚合（供占比校验与 statements 附注引用）
    family_agg: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(
        lambda: {"revenue": Decimal("0"), "cost": Decimal("0")}
    )
    for row in operating_actual:
        agg = family_agg[(row["month"], row["family_id"])]
        agg["revenue"] += Decimal(row["revenue"])
        agg["cost"] += Decimal(row["cost"])
    family_actual = [
        {
            "month": month,
            "family_id": family_id,
            "revenue": str(agg["revenue"]),
            "cost": str(agg["cost"]),
        }
        for (month, family_id), agg in sorted(family_agg.items())
    ]

    # 财务实际：经营收入逐月精确对账
    financial_actual = []
    for month in all_months:
        revenue = sum(
            (Decimal(r["revenue"]) for r in operating_actual if r["month"] == month),
            Decimal("0"),
        )
        financial_actual.append({"month": month, "revenue": str(revenue)})

    # 预算：仅分析期，12×4×4×8 单元格 × 7 类行 = 10,752。
    # 非空单元格收入 = 同 (月, 客群, 产品) 实际 × 1.03（E4 单元 ×1.12）；
    # 空单元格用确定性基线；单元格内恒等式精确闭合。
    cell_actual: dict[tuple[str, str, str], Decimal] = defaultdict(Decimal)
    customer_segment = {
        cid: str(assign["segment"]) for cid, assign in CUSTOMER_ASSIGNMENTS.items()
    }
    for row in operating_actual:
        if row["month"] in ANALYSIS_MONTHS:
            key = (row["month"], customer_segment[row["customer_id"]], row["product"])
            cell_actual[key] += Decimal(row["revenue"])

    budget: list[dict[str, Any]] = []
    for month_index, month in enumerate(ANALYSIS_MONTHS):
        for unit in BUSINESS_UNITS:
            for segment_index, segment in enumerate(CUSTOMER_SEGMENTS):
                for product_index, product_id in enumerate(_PRODUCT_IDS):
                    if (
                        _PRODUCT_UNIT[product_id] == unit
                        and (month, segment, product_id) in cell_actual
                    ):
                        multiplier = (
                            _BUDGET_MULTIPLIER_E4 if unit == _E4_UNIT
                            else _BUDGET_MULTIPLIER
                        )
                        revenue = _d(
                            cell_actual[(month, segment, product_id)] * multiplier
                        )
                    else:  # 空单元格确定性基线
                        revenue = Decimal("25.0000") + Decimal(
                            (month_index * 11 + segment_index * 5 + product_index * 3)
                            % 13
                        )
                    lines: dict[str, Decimal] = {"REVENUE": revenue}
                    for account, rate in _BUDGET_COST_RATES:
                        lines[account] = _d(revenue * rate)
                    lines["OPERATING_EXPENSE"] = _d(revenue * _BUDGET_EXPENSE_RATE)
                    lines["OPERATING_PROFIT"] = (
                        revenue
                        - lines["WAREHOUSING_COST"]
                        - lines["TRANSPORTATION_COST"]
                        - lines["OTHER_DIRECT_COST"]
                        - lines["OPERATING_EXPENSE"]
                    )
                    lines["OPERATING_CASH_FLOW"] = _d(
                        lines["OPERATING_PROFIT"] * _BUDGET_OCF_RATE
                    )
                    for account, amount in lines.items():
                        budget.append(
                            {
                                "month": month,
                                "business_unit": unit,
                                "customer_segment": segment,
                                "product": product_id,
                                "account": account,
                                "amount": str(amount),
                                "scenario": "budget-v1",
                            }
                        )

    # 客户月收入索引（AR 余额系数用）
    customer_month_revenue: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
    for row in operating_actual:
        customer_month_revenue[(row["month"], row["customer_id"])] += Decimal(
            row["revenue"]
        )

    # AR 账龄：24 月 × 40 客户 × 5 桶 = 4,800；未到期 + 逾期 = 余额，非负。
    # E3：DM-CUST-007/019 自 2026-03 起逾期桶 ×1.35、回款 ×0.75。
    ar_aging: list[dict[str, Any]] = []
    for month in all_months:
        for ci in range(1, 41):
            customer_id = f"DM-CUST-{ci:03d}"
            credit_days = int(CUSTOMER_ASSIGNMENTS[customer_id]["credit_term_days"])
            base = customer_month_revenue[(month, customer_id)]
            outstanding = _d(base * Decimal(credit_days) / Decimal("120"))
            e3 = customer_id in _E3_CUSTOMERS and month >= _E3_START_MONTH
            factor = _E3_OVERDUE_FACTOR if e3 else Decimal("1")
            amounts: dict[str, Decimal] = {}
            running = Decimal("0")
            for bucket, rate in _AR_BUCKET_RATES:
                if bucket == "current":
                    continue
                value = _d(outstanding * rate * (factor if bucket != "1-30" else Decimal("1")))
                amounts[bucket] = value
                running += value
            amounts["90+"] = _d(outstanding * Decimal("0.04") * factor)
            running += amounts["90+"]
            amounts["current"] = outstanding - running  # 尾差入未到期桶
            collected = _d(
                base * _AR_COLLECT_RATE * (_E3_COLLECT_FACTOR if e3 else Decimal("1"))
            )
            for bucket in ("current", "1-30", "31-60", "61-90", "90+"):
                balance = amounts[bucket]
                ar_aging.append(
                    {
                        "month": month,
                        "customer_id": customer_id,
                        "bucket": bucket,
                        "balance": str(balance),
                        "due": str(balance if bucket == "current" else Decimal("0")),
                        "overdue": str(Decimal("0") if bucket == "current" else balance),
                        "collected": str(
                            collected if bucket == "current" else Decimal("0")
                        ),
                    }
                )

    # 经营现金流：经营利润 + 背离调整（E5：2026-05/06 现金流反常走低）
    operating_profit_by_month: dict[str, Decimal] = defaultdict(Decimal)
    for row in operating_actual:
        operating_profit_by_month[row["month"]] += Decimal(row["gross_profit"])
    expense_rate = Decimal("0.06")
    cash_flow = []
    for month in all_months:
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
            "customer_segments": [
                {"segment_id": f"SEG-{i:02d}", "name": name}
                for i, name in enumerate(CUSTOMER_SEGMENTS, 1)
            ],
            "customers": [
                {
                    "customer_id": customer_id,
                    "name": CUSTOMERS[index],
                    "synthetic": True,
                    "segment": assign["segment"],
                    "primary_region": assign["primary_region"],
                    "credit_term_days": assign["credit_term_days"],
                }
                for index, (customer_id, assign) in enumerate(
                    CUSTOMER_ASSIGNMENTS.items()
                )
            ],
            "products": [
                {
                    "product_id": product_id,
                    "name": PRODUCTS[index],
                    "family_id": PRODUCT_ASSIGNMENTS[product_id]["family_id"],
                    "business_unit": PRODUCT_ASSIGNMENTS[product_id]["business_unit"],
                }
                for index, product_id in enumerate(_PRODUCT_IDS)
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
