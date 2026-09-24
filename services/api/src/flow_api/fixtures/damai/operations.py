"""大麦独立运营事实与分部序列生成（Task A3，规格 §4.3）。

DAMAI.SYN 的 /operations 数据完全由 canonical 数据包确定性推导，
不读取、不复用任何真实公司（阿里巴巴/菜鸟）fixture：
- 分部序列：全集团管理层口径收入 + 经调整 EBITA（经营利润 ×1.08 加回演示参数）；
- 运营事实：国际包裹量/国内履约单量（由收入按客单价推导）、业务线收入占比；
- 血缘：source_ref 指向发行版 manifest.json，摘要在装载时现算现核。

单位：分部序列/运营金额为人民币百万元（canonical 万元 ÷ 100）。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from flow_api.fixtures.damai.profile import BUSINESS_FAMILIES

_UNIT_TO_MN = Decimal("0.01")  # 万元 -> 百万元
_ORDER_UNIT_PRICE = Decimal("120")  # 客单价 120 万元/单（与 canonical 派生口径一致）
_SHIPMENTS_PER_ORDER = Decimal("2.0")
_EBITA_UPLIFT = Decimal("1.08")  # 经调整 EBITA = 经营利润 × 1.08（D&A 加回演示参数）


def _d(value: Decimal, places: str = "0.0001") -> Decimal:
    return value.quantize(Decimal(places))


def _fy_months(package: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    all_months = tuple(
        sorted({row["month"] for row in package["monthly_facts"]["operating_actual"]})
    )
    return {"FY2025": all_months[:12], "FY2026": all_months[12:]}


def _fy_totals(package: dict[str, Any]) -> dict[str, dict[str, Decimal]]:
    """逐财年 收入/经营利润/分族收入/分族件量（万元与百万件）。"""

    months_by_fy = _fy_months(package)
    totals: dict[str, dict[str, Decimal]] = {}
    for fy, months in months_by_fy.items():
        revenue = Decimal("0")
        profit = Decimal("0")
        by_family: dict[str, Decimal] = {}
        for row in package["monthly_facts"]["operating_actual"]:
            if row["month"] not in months:
                continue
            row_revenue = Decimal(str(row["revenue"]))
            revenue += row_revenue
            by_family[row["family_id"]] = (
                by_family.get(row["family_id"], Decimal("0")) + row_revenue
            )
        for row in package["monthly_facts"]["cash_flow"]:
            if row["month"] in months:
                profit += Decimal(str(row["operating_profit"]))
        totals[fy] = {"revenue": revenue, "operating_profit": profit, **{
            f"family:{fid}": value for fid, value in by_family.items()
        }}
    return totals


def build_damai_operations_payloads(package: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """生成两个 yaml 载荷：segment_series 与 operating_metrics（确定性）。"""

    totals = _fy_totals(package)

    segment_series: dict[str, Any] = {
        "sample": "damai_segment_series",
        "company": "大麦物流（synthetic 演示企业）",
        "unit": "人民币百万元",
        "note": (
            "synthetic 演示数据：全集团管理层口径序列，由 canonical 月度事实推导；"
            "不代表任何真实企业。"
        ),
        "sources": {
            fy: "fixtures/damai/manifest.json" for fy in totals
        },
        "series": {
            fy: {
                "segment_revenue": float(_d(t["revenue"] * _UNIT_TO_MN)),
                "adjusted_ebita": float(
                    _d(t["operating_profit"] * _UNIT_TO_MN * _EBITA_UPLIFT)
                ),
            }
            for fy, t in totals.items()
        },
    }

    def _volume_millions(family_id: str, fy: str) -> float:
        revenue = totals[fy].get(f"family:{family_id}", Decimal("0"))
        orders = revenue / _ORDER_UNIT_PRICE
        shipments = orders * _SHIPMENTS_PER_ORDER
        return float(_d(shipments / Decimal("1000000")))

    analysis_fy = "FY2026"
    analysis_total = totals[analysis_fy]["revenue"]
    share = {
        family.family_id: float(
            _d(totals[analysis_fy].get(f"family:{family.family_id}", Decimal("0"))
               / analysis_total)
        )
        for family in BUSINESS_FAMILIES
    }
    operating_metrics: dict[str, Any] = {
        "sample": "damai_operating_metrics",
        "source_ref": "fixtures/damai/manifest.json",
        "periods": ["FY2025", "FY2026"],
        "operating_volume": {
            "unit": "百万件",
            "international_parcels": {
                fy: _volume_millions("international_cross_border", fy) for fy in totals
            },
            "china_orders_fulfilled": {
                fy: _volume_millions("china_logistics", fy) for fy in totals
            },
        },
        "business_line_revenue_share": {
            "international_logistics": share["international_cross_border"],
            "china_logistics": share["china_logistics"],
            "technology_and_other_services": share["tech_and_other"],
        },
        "network_snapshot": {
            "as_of": "2026-08-31",
            "note": "synthetic 演示快照：业务单元 4 个、区域网络 6 个、产品线 8 条",
        },
    }
    return {
        "segment_series": segment_series,
        "operating_metrics": operating_metrics,
    }


__all__ = ["build_damai_operations_payloads"]
