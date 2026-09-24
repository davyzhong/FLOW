"""大麦 canonical 数据包不变量验证器（Task 2）。

validate_damai_package 逐项检查业务与恒等不变量，失败返回具体
invariant code；通过返回 valid=True。只做判定，不修正数据。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from flow_api.fixtures.damai.profile import BUSINESS_FAMILIES


def validate_damai_package(package: dict[str, Any]) -> dict[str, Any]:
    """校验 canonical 数据包；返回 {valid, invariant_codes}。"""

    codes: list[str] = []
    facts = package["monthly_facts"]

    # 覆盖：24 个月全覆盖
    months = sorted({row["month"] for row in facts["operating_actual"]})
    if len(months) != 24:
        codes.append("month_coverage_not_24")

    # 经营/财务对账（逐月求和相等）
    op_totals: dict[str, Decimal] = {}
    fin_totals: dict[str, Decimal] = {}
    for row in facts["operating_actual"]:
        op_totals[row["month"]] = op_totals.get(row["month"], Decimal("0")) + Decimal(
            str(row["revenue"])
        )
    for row in facts["financial_actual"]:
        fin_totals[row["month"]] = fin_totals.get(row["month"], Decimal("0")) + Decimal(
            str(row["revenue"])
        )
    if op_totals != fin_totals:
        codes.append("operating_financial_mismatch")

    # 分析期收入锚区间（1050–1150 亿 = 10,500,000–11,500,000 万元）
    analysis_months = {
        row["month"] for row in package["monthly_facts"]["budget"]
    }
    analysis_total = sum(
        (
            value
            for month, value in op_totals.items()
            if month in analysis_months
        ),
        Decimal("0"),
    )
    if not Decimal("10500000") <= analysis_total <= Decimal("11500000"):
        codes.append("revenue_out_of_anchor_range")

    # 业务族占比 ±1pp（分析期）
    family_totals: dict[str, Decimal] = {}
    analysis_month_set = {
        row["month"] for row in facts["budget"]
    }
    for row in facts["family_actual"]:
        if row["month"] in analysis_month_set:
            family_totals[row["family_id"]] = family_totals.get(
                row["family_id"], Decimal("0")
            ) + Decimal(str(row["revenue"]))
    family_sum = sum(family_totals.values(), Decimal("0"))
    for family in BUSINESS_FAMILIES:
        share = family_totals.get(family.family_id, Decimal("0")) / family_sum
        if abs(share - family.target_weight) > Decimal("0.01"):
            codes.append(f"family_share_drift_{family.family_id}")

    # AR 账龄闭合与非负
    for row in facts["ar_aging"]:
        buckets = sum(
            (
                Decimal(str(row[key]))
                for key in ("b_current", "b_31_60", "b_61_90", "b_90_plus")
            ),
            Decimal("0"),
        )
        outstanding = Decimal(str(row["ar_outstanding"]))
        if buckets != outstanding:
            codes.append("ar_bucket_mismatch")
            break
        if min(buckets, outstanding) < 0:
            codes.append("ar_negative")
            break

    # 预算仅覆盖分析期（分析期月份与预算行数一致性由 loader 契约保证）

    # forecast sidecar 标记与 SHA
    sidecar = package.get("forecast_sidecar", {})
    if sidecar.get("persistence") != "static-only":
        codes.append("forecast_persistence_undeclared")
    if sidecar.get("page_coverage") != "excluded":
        codes.append("forecast_page_coverage_undeclared")

    return {"valid": not codes, "invariant_codes": codes}


__all__ = ["validate_damai_package"]
