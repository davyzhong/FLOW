"""U2/I09：应收与收入增速联动提示契约测试（TDD 先行）。

契约（C14：相关性≠原因）：
- 两指标必须同期间（同为年度流量口径）才可联看；
- 应收增速 > 收入增速时输出"联动提示"，提示语只陈述偏差事实并引导复核，
  不得包含回款恶化/信用风险等因果断言；
- 差距不成立（应收增速 ≤ 收入增速）或任一输入缺失/期间不一致 → 不输出提示。
"""

from __future__ import annotations

from decimal import Decimal

from flow_api.analysis.deterministic import growth_linkage_check


def _prompt_keywords_forbidden(text: str) -> bool:
    forbidden = ("恶化", "风险", "导致", "因为", "说明回款", "质量下降")
    return any(word in text for word in forbidden)


def test_receivable_growing_faster_yields_review_prompt() -> None:
    result = growth_linkage_check(
        receivable_growth=Decimal("0.31"),
        revenue_growth=Decimal("0.12"),
        period_label="2026H1",
    )
    assert result is not None
    assert result.kind == "linkage_review"
    assert result.period_label == "2026H1"
    assert result.gap == Decimal("0.19")
    # 提示语：陈述偏差 + 引导复核，无因果断言
    assert "复核" in result.prompt
    assert "31.00%" in result.prompt and "12.00%" in result.prompt
    assert not _prompt_keywords_forbidden(result.prompt)


def test_aligned_growth_no_prompt() -> None:
    assert (
        growth_linkage_check(
            receivable_growth=Decimal("0.12"),
            revenue_growth=Decimal("0.12"),
            period_label="2026H1",
        )
        is None
    )
    assert (
        growth_linkage_check(
            receivable_growth=Decimal("0.05"),
            revenue_growth=Decimal("0.20"),
            period_label="2026H1",
        )
        is None
    )


def test_missing_input_no_prompt() -> None:
    assert (
        growth_linkage_check(
            receivable_growth=None, revenue_growth=Decimal("0.12"), period_label="2026H1"
        )
        is None
    )
    assert (
        growth_linkage_check(
            receivable_growth=Decimal("0.31"), revenue_growth=None, period_label="2026H1"
        )
        is None
    )
