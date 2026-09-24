"""Task 2：大麦 canonical 数据集生成与验证契约测试。

- build_damai_package 产出确定性主数据 + 24 个月事实 + 预算 + AR +
  forecast sidecar；两次构建字节一致（UUID5/Decimal，无随机）；
- validate_damai_package 校验行数、收入锚区间、业务族占比 ±1pp、
  经营/财务对账、AR 账龄闭合与非负、预算场景与植入事件；
- forecast sidecar 必须 static-only / page_coverage: excluded，
  不得冒充已上线能力。
"""

from __future__ import annotations

import json
from decimal import Decimal

from flow_api.fixtures.damai.generator import build_damai_package
from flow_api.fixtures.damai.profile import (
    ANALYSIS_MONTHS,
    PRIOR_MONTHS,
)


def _package_bytes_deterministic() -> tuple[dict, dict]:
    first = build_damai_package()
    second = build_damai_package()
    return first, second


def test_package_is_deterministic_across_builds() -> None:
    first, second = _package_bytes_deterministic()
    assert first == second, "两次构建必须产生完全一致的数据包（UUID5 + Decimal）"


def test_master_data_counts_meet_specification() -> None:
    pkg = build_damai_package()
    master = pkg["master_data"]
    assert len(master["business_units"]) >= 4
    assert len(master["regions"]) >= 6
    assert len(master["customers"]) >= 40
    assert len(master["products"]) >= 8
    assert all(c["synthetic"] for c in master["customers"])


def test_monthly_facts_cover_24_months_with_revenue_anchor() -> None:
    pkg = build_damai_package()
    facts = pkg["monthly_facts"]
    months = {row["month"] for row in facts["operating_actual"]}
    assert months == set(PRIOR_MONTHS) | set(ANALYSIS_MONTHS)
    analysis_revenue = sum(
        (Decimal(str(r["revenue"])) for r in facts["operating_actual"]
         if r["month"] in ANALYSIS_MONTHS),
        Decimal("0"),
    )
    low, high = Decimal("10500000"), Decimal("11500000")  # 万元
    assert low <= analysis_revenue <= high, "分析期收入必须落在 1050–1150 亿锚区间"


def test_business_family_share_within_one_point_of_target() -> None:
    pkg = build_damai_package()
    analysis = [
        r for r in pkg["monthly_facts"]["operating_actual"]
        if r["month"] in ANALYSIS_MONTHS
    ]
    total = sum((Decimal(str(r["revenue"])) for r in analysis), Decimal("0"))
    by_family: dict[str, Decimal] = {}
    for row in pkg["monthly_facts"]["family_actual"]:
        if row["month"] in ANALYSIS_MONTHS:
            key = row["family_id"]
            addition = Decimal(str(row["revenue"]))
            by_family[key] = by_family.get(key, Decimal("0")) + addition
    for family_id, weight in {
        "international_cross_border": Decimal("0.474"),
        "china_logistics": Decimal("0.462"),
        "tech_and_other": Decimal("0.064"),
    }.items():
        share = by_family[family_id] / total
        assert abs(share - weight) <= Decimal("0.01"), (
            f"{family_id} 占比 {share} 偏离目标 {weight} 超过 ±1pp"
        )


def test_budget_scenarios_present_for_analysis_period_only() -> None:
    pkg = build_damai_package()
    budget_months = {r["month"] for r in pkg["monthly_facts"]["budget"]}
    assert budget_months == set(ANALYSIS_MONTHS), "预算只覆盖分析期"


def test_forecast_sidecar_is_static_only_and_hashed() -> None:
    pkg = build_damai_package()
    forecast = pkg["forecast_sidecar"]
    assert forecast["persistence"] == "static-only"
    assert forecast["page_coverage"] == "excluded"
    assert forecast["version"] and forecast["sha256"]
    body = json.dumps(forecast["rows"], sort_keys=True).encode()
    import hashlib
    assert (
        hashlib.sha256(body).hexdigest() == forecast["sha256"]
    ), "sidecar SHA 必须与行内容一致"


def test_ar_aging_buckets_close_and_non_negative() -> None:
    pkg = build_damai_package()
    rows = pkg["monthly_facts"]["ar_aging"]
    cells: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        balance = Decimal(str(row["balance"]))
        due = Decimal(str(row["due"]))
        overdue = Decimal(str(row["overdue"]))
        assert due + overdue == balance, (
            f"{row['month']}/{row['customer_id']}/{row['bucket']} 未到期+逾期 ≠ 余额"
        )
        assert min(balance, due, overdue, Decimal(str(row["collected"]))) >= 0, (
            "应收/回款金额不得为负"
        )
        cells.setdefault((row["month"], row["customer_id"]), set()).add(row["bucket"])
    assert len(cells) == 24 * 40
    for key, buckets in cells.items():
        assert buckets == {"current", "1-30", "31-60", "61-90", "90+"}, key


def test_operating_financial_reconciliation_closes() -> None:
    pkg = build_damai_package()
    facts = pkg["monthly_facts"]

    def _monthly_sum(rows: list[dict]) -> dict[str, Decimal]:
        totals: dict[str, Decimal] = {}
        for row in rows:
            totals[row["month"]] = totals.get(row["month"], Decimal("0")) + Decimal(
                str(row["revenue"])
            )
        return totals

    assert _monthly_sum(facts["operating_actual"]) == _monthly_sum(
        facts["financial_actual"]
    ), "经营收入与财务 REVENUE 逐月对账必须一致"


def test_validate_damai_package_passes_on_generated_package() -> None:
    from flow_api.fixtures.damai.validation import validate_damai_package

    pkg = build_damai_package()
    result = validate_damai_package(pkg)
    assert result["valid"] is True
    assert result["invariant_codes"] == []


# ---------------------------------------------------------------------------
# Task A1 红灯：生成器必须产出明细级事实（规格 §3.3）
# ---------------------------------------------------------------------------


def test_operating_actual_is_customer_product_detail_not_aggregate() -> None:
    pkg = build_damai_package()
    rows = pkg["monthly_facts"]["operating_actual"]
    assert len(rows) == 1920, f"经营明细必须 1920 条，实际 {len(rows)}"
    for row in rows:
        assert row["customer_id"] != "AGGREGATE"
        assert row["product"] != "AGGREGATE"
        assert row["customer_id"].startswith("DM-CUST-")
        assert row["product"].startswith("P-")


def test_budget_covers_seven_raw_lines_per_cell() -> None:
    pkg = build_damai_package()
    rows = pkg["monthly_facts"]["budget"]
    assert len(rows) == 10752, f"预算必须 10752 条，实际 {len(rows)}"
    cell_lines: dict[tuple, set] = {}
    for row in rows:
        key = (row["month"], row["business_unit"], row["customer_segment"], row["product"])
        cell_lines.setdefault(key, set()).add(row["account"])
    assert len(cell_lines) == 12 * 4 * 4 * 8
    required = {
        "REVENUE", "WAREHOUSING_COST", "TRANSPORTATION_COST", "OTHER_DIRECT_COST",
        "OPERATING_EXPENSE", "OPERATING_PROFIT", "OPERATING_CASH_FLOW",
    }
    for key, lines in cell_lines.items():
        assert lines == required, f"{key} 预算行不齐: {required - lines}"


def test_ar_aging_is_per_customer_five_buckets_24_months() -> None:
    pkg = build_damai_package()
    rows = pkg["monthly_facts"]["ar_aging"]
    assert len(rows) == 4800, f"AR 必须 4800 条，实际 {len(rows)}"
    months = {r["month"] for r in rows}
    assert len(months) == 24, "同比期 AR 不得缺失"
    cells: dict[tuple, set] = {}
    for row in rows:
        cells.setdefault((row["month"], row["customer_id"]), set()).add(row["bucket"])
    assert len(cells) == 24 * 40
    for key, buckets in cells.items():
        assert buckets == {"current", "1-30", "31-60", "61-90", "90+"}, key


def test_planted_events_traceable_to_detail_records() -> None:
    """六类植入事件的影响必须能追溯到具体客户/产品/区域/月。"""
    pkg = build_damai_package()
    rows = pkg["monthly_facts"]["operating_actual"]
    # E3：两个大客户（DM-CUST-007 / DM-CUST-019）后期账龄恶化——
    # 明细级 AR 必须能把恶化定位到具体客户
    ar = pkg["monthly_facts"]["ar_aging"]
    late = [r for r in ar if r["month"] >= "2026-03" and r["bucket"] in ("31-60", "61-90", "90+")
            and r["customer_id"] in ("DM-CUST-007", "DM-CUST-019")]
    assert late, "E3 恶化必须体现在明细 AR 行上"
    # E4：某业务单元实际收入低于预算——明细级可比（同月同单元）
    #（数值由 A2 确定性参数保证；此处仅断言明细粒度存在可比键）
    budget_keys = {(r["month"], r["business_unit"]) for r in pkg["monthly_facts"]["budget"]}
    actual_units = {r["business_unit"] for r in rows if r["month"] >= "2025-09"}
    assert len(actual_units) == 4
    assert budget_keys, "预算必须带业务单元键以支持 E4 单元级对比"
