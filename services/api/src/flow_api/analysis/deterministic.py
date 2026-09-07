"""确定性分析原语（U2/原 P03）。

只做数学分解与守恒检查，不做业务归因（D049：数学贡献不冒充因果）。
全部使用 Decimal；无业务含义的输入返回 None 而非编造（C07/C08）。
"""

from __future__ import annotations

from decimal import Context, Decimal, localcontext

_Q = Decimal("0.000001")


def compound_annual_growth_rate(
    end_value: Decimal, begin_value: Decimal, *, periods: int
) -> Decimal | None:
    """复合年增长率 = (期末/期初)^(1/(periods−1)) − 1。

    periods 为年度点数；除数为期数减一（C07 契约，tests/analysis/test_cagr.py 锁定）。
    periods < 2、期初 ≤ 0、期末 < 0 或期末/期初 ≤ 0 时返回 None。
    """

    if periods < 2:
        return None
    if begin_value <= 0 or end_value < 0:
        return None
    ratio = end_value / begin_value
    if ratio < 0:
        return None
    exponent = Decimal(1) / Decimal(periods - 1)
    with localcontext(Context(prec=28)):
        growth = Decimal(ratio) ** exponent - Decimal(1)
    return growth.quantize(_Q)


__all__ = ["compound_annual_growth_rate"]
