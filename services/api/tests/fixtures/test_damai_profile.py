"""Task 1：大麦物流演示画像契约测试（D052 方案 B / 规格 v1.1 §3）。

- 24 个连续月（对比期 2024-09~2025-08 + 分析期 2025-09~2026-08）；
- 分析期收入目标 1050–1150 亿（万元计），毛利率 9%–11%；
- 业务族权重合计恰为 1（Decimal）；结构数量满足规格下限；
- 全部实体 synthetic：客户为匿名编号，不得出现真实公司名；
- enterprise 复用固定 bootstrap UUID（当前授权契约：整库单企业）。
"""

from __future__ import annotations

from decimal import Decimal

from flow_api.fixtures.damai.profile import (
    ANALYSIS_MONTHS,
    BUSINESS_FAMILIES,
    BUSINESS_UNITS,
    CUSTOMERS,
    DAMAI_BOOTSTRAP_ENTERPRISE_ID,
    DAMAI_PROFILE_V1,
    PRIOR_MONTHS,
    PRODUCTS,
    REGIONS,
)


def test_24_continuous_months_prior_then_analysis() -> None:
    assert len(PRIOR_MONTHS) == 12 and len(ANALYSIS_MONTHS) == 12
    all_months = PRIOR_MONTHS + ANALYSIS_MONTHS
    assert all_months[0] == "2024-09" and all_months[-1] == "2026-08"
    # 连续性：逐月递增无缺口
    year_month = [tuple(int(x) for x in m.split("-")) for m in all_months]
    assert len(year_month) == 24
    # 相邻配对长度差 1 是设计意图；先断言长度再关闭 strict 检查
    assert len(year_month) >= 2
    pairs = zip(year_month, year_month[1:], strict=False)  # noqa: B905
    for (y1, m1), (y2, m2) in pairs:
        delta = (y2 - y1) * 12 + (m2 - m1)
        assert delta == 1, f"期间不连续: {y1}-{m1:02d} -> {y2}-{m2:02d}"


def test_revenue_and_margin_targets_within_anchors() -> None:
    low, high = DAMAI_PROFILE_V1.annual_revenue_target
    assert Decimal("10500000") <= low < high <= Decimal("11500000"), (
        "分析期收入目标（万元）必须落在 1050–1150 亿锚区间"
    )
    gm_low, gm_high = DAMAI_PROFILE_V1.gross_margin_target
    assert Decimal("0.09") <= gm_low < gm_high <= Decimal("0.11")


def test_business_family_weights_sum_to_exactly_one() -> None:
    weights = {f.family_id: f.target_weight for f in BUSINESS_FAMILIES}
    assert set(weights) == {
        "international_cross_border",
        "china_logistics",
        "tech_and_other",
    }
    total = sum(weights.values(), Decimal("0"))
    assert total == Decimal("1"), f"权重合计必须精确为 1，实际 {total}"
    for family_id, weight in weights.items():
        assert Decimal("0.45") <= weight <= Decimal("0.49") or family_id == "tech_and_other"


def test_structure_counts_meet_specification_minimums() -> None:
    assert len(BUSINESS_UNITS) >= 4
    assert len(REGIONS) >= 6
    assert len(CUSTOMERS) >= 40
    assert len(PRODUCTS) >= 8
    assert len(set(CUSTOMERS)) == len(CUSTOMERS), "客户不得重复"


def test_all_entities_are_synthetic() -> None:
    assert DAMAI_PROFILE_V1.synthetic is True
    banned = ("顺丰", "京东", "菜鸟", "中通", "圆通", "韵达", "阿里", "腾讯", "华为")
    for customer in CUSTOMERS:
        for name in banned:
            assert name not in customer, f"客户名不得出现真实公司名: {customer}"
    synthetic_marked = (
        "synthetic" in DAMAI_PROFILE_V1.enterprise_name.lower()
        or "synthetic" in DAMAI_PROFILE_V1.disclosure_note
    )
    assert synthetic_marked


def test_enterprise_reuses_bootstrap_uuid() -> None:
    assert str(DAMAI_BOOTSTRAP_ENTERPRISE_ID) == (
        "00000000-0000-0000-0000-00000000d001"
    ), "必须复用固定 bootstrap enterprise（授权契约：整库单企业）"


def test_six_planted_analysis_events_present() -> None:
    kinds = {event.kind for event in DAMAI_PROFILE_V1.planted_events}
    assert {
        "peak_volume_price_pressure",
        "domestic_efficiency_gain",
        "major_customer_ar_deterioration",
        "region_revenue_below_budget",
        "profit_cash_divergence",
        "mix_shift_margin_change",
    } <= kinds
    assert len(DAMAI_PROFILE_V1.planted_events) >= 6


# ---------------------------------------------------------------------------
# Task A1 红灯：全量数据合同——主数据归属与明细维度声明
# （规格 §3.3；先于实现写断言，禁止先改实现后补断言）
# ---------------------------------------------------------------------------


def test_four_customer_segments_declared() -> None:
    """客群必须达到 4 个（当前仅 canonical 层单个 DM_SYNTH 聚合客群）。"""
    segments = DAMAI_PROFILE_V1.customer_segments
    assert len(segments) == 4, f"客群必须为 4 个，实际 {len(segments)}"
    assert len(set(segments)) == 4


def test_every_customer_has_fixed_segment_region_credit_term() -> None:
    """40 客户每个都固定客群、主区域与信用期（spec §3.3 主数据映射）。"""
    assignments = DAMAI_PROFILE_V1.customer_assignments
    assert len(assignments) == 40
    for customer_id, assign in assignments.items():
        assert assign["segment"] in DAMAI_PROFILE_V1.customer_segments
        assert assign["primary_region"] in REGIONS
        assert isinstance(assign["credit_term_days"], int)
        assert 0 < assign["credit_term_days"] <= 120


def test_every_product_has_fixed_family_and_business_unit() -> None:
    """8 产品每个都固定业务族与业务单元。"""
    assignments = DAMAI_PROFILE_V1.product_assignments
    assert len(assignments) == 8
    family_ids = {f.family_id for f in BUSINESS_FAMILIES}
    for product_id, assign in assignments.items():
        assert assign["family_id"] in family_ids
        assert assign["business_unit"] in BUSINESS_UNITS
