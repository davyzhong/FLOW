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
    for row in pkg["monthly_facts"]["ar_aging"]:
        buckets = (
            Decimal(str(row["b_current"]))
            + Decimal(str(row["b_31_60"]))
            + Decimal(str(row["b_61_90"]))
            + Decimal(str(row["b_90_plus"]))
        )
        outstanding = Decimal(str(row["ar_outstanding"]))
        assert buckets == outstanding, f"{row['month']} 账龄桶之和 ≠ 应收余额"
        assert min(
            buckets, outstanding, Decimal(str(row["collected"]))
        ) >= 0, "应收/回款金额不得为负"


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
