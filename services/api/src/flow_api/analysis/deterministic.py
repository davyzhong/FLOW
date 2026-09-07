"""确定性分析原语（U2/原 P03）。

只做数学分解与守恒检查，不做业务归因（D049：数学贡献不冒充因果）。
全部使用 Decimal；无业务含义的输入返回 None 而非编造（C07/C08）。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, localcontext

_Q = Decimal("0.000001")


@dataclass(frozen=True, slots=True)
class LinkageReviewPrompt:
    """I09 联动提示：只陈述增速偏差事实并引导复核，不作因果断言（C14）。"""

    kind: str  # 恒为 "linkage_review"
    period_label: str
    receivable_growth: Decimal
    revenue_growth: Decimal
    gap: Decimal
    prompt: str


def growth_linkage_check(
    *,
    receivable_growth: Decimal | None,
    revenue_growth: Decimal | None,
    period_label: str,
) -> LinkageReviewPrompt | None:
    """应收增速与收入增速联看（I09）。

    仅当同期间两增速齐备且应收增速高于收入增速时输出复核提示；
    提示语为事实陈述（两增速与差距），不含回款恶化/风险类因果用语。
    """

    if receivable_growth is None or revenue_growth is None:
        return None
    if receivable_growth <= revenue_growth:
        return None
    gap = (receivable_growth - revenue_growth).quantize(_Q)
    receivable_text = f"{(receivable_growth * 100):.2f}%"
    revenue_text = f"{(revenue_growth * 100):.2f}%"
    prompt = (
        f"{period_label} 应收增速 {receivable_text} 高于收入增速 {revenue_text}"
        f"（差距 {gap * 100:.2f}%）；两项趋势存在偏离，建议复核应收与收入的期间口径及构成。"
    )
    return LinkageReviewPrompt(
        kind="linkage_review",
        period_label=period_label,
        receivable_growth=receivable_growth,
        revenue_growth=revenue_growth,
        gap=gap,
        prompt=prompt,
    )


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


__all__ = ["LinkageReviewPrompt", "compound_annual_growth_rate", "growth_linkage_check"]
