"""U2/C07：CAGR 间隔数契约测试（TDD 先行）。

契约：n 年复合增长率 = (期末/期初)^(1/(n−1)) − 1，除数为**期数减一**；
期数不足（n<2）返回 None 而非编造；端点为零/负导致无意义时返回 None。
反例锁定：除以 n（而非 n−1）的常见错误实现必须失败。
"""

from __future__ import annotations

from decimal import Decimal

from flow_api.analysis.deterministic import compound_annual_growth_rate


def test_two_year_cagr_uses_n_minus_one() -> None:
    # 100 → 121：两年一个增长期，CAGR = 21%（不是 (121/100)^(1/2)−1 ≈ 10%——那是除以 n 的错值）
    rate = compound_annual_growth_rate(Decimal("121"), Decimal("100"), periods=2)
    assert rate == Decimal("0.210000")


def test_four_points_three_periods_cagr() -> None:
    # 100 → 133.1：四个年度点、三个增长期（1.1³），CAGR = 10%/期
    rate = compound_annual_growth_rate(Decimal("133.1"), Decimal("100"), periods=4)
    assert rate == Decimal("0.100000")
    # 反例锁定：误除以 n（4）会得 ≈7.44%，测试防的就是这种实现
    wrong = Decimal("1.331") ** (Decimal(1) / Decimal(4)) - Decimal(1)
    assert abs(rate - wrong.quantize(Decimal("0.000001"))) > Decimal("0.02")


def test_declining_is_negative() -> None:
    # 100 → 81：三个年度点、两个增长期（0.9²），CAGR = −10%
    rate = compound_annual_growth_rate(Decimal("81"), Decimal("100"), periods=3)
    assert rate == Decimal("-0.100000")


def test_insufficient_periods_returns_none() -> None:
    assert compound_annual_growth_rate(Decimal("120"), Decimal("100"), periods=1) is None
    assert compound_annual_growth_rate(Decimal("120"), Decimal("100"), periods=0) is None


def test_zero_or_negative_endpoints_return_none() -> None:
    # 期初为零/负、期末为负：比率无业务含义，拒绝计算（D049：不补造）
    assert compound_annual_growth_rate(Decimal("120"), Decimal("0"), periods=3) is None
    assert compound_annual_growth_rate(Decimal("-5"), Decimal("100"), periods=3) is None
    assert compound_annual_growth_rate(Decimal("5"), Decimal("-100"), periods=3) is None


def test_negative_endpoint_ratio_rejected() -> None:
    # 期末/期初符号不同 → 负数开方无实数意义
    assert compound_annual_growth_rate(Decimal("-121"), Decimal("100"), periods=2) is None
