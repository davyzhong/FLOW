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


@dataclass(frozen=True, slots=True)
class AdditiveBridgeResult:
    """C08 可加和桥守恒结果：分项和 vs 总变化额，残差显式。"""

    reconciled: bool
    total_change: Decimal
    allocated: dict[str, Decimal]
    residual: Decimal
    note: str


_TOLERANCE = Decimal("0.01")


def reconcile_additive_bridge(
    *,
    total_change: Decimal | None,
    parts: dict[str, Decimal | None],
) -> AdditiveBridgeResult | None:
    """可加和驱动拆解守恒检查（C08）。

    分项之和与总变化额的差（容差 0.01）作为「未分配残差」显式返回；
    不做静默分摊或凑整；任一输入缺失返回 None。
    """

    if total_change is None:
        return None
    if any(value is None for value in parts.values()):
        return None
    allocated = {name: value for name, value in parts.items() if value is not None}
    parts_sum = sum(allocated.values(), Decimal("0"))
    residual = (total_change - parts_sum).quantize(Decimal("0.01"))
    reconciled = abs(residual) <= _TOLERANCE
    if reconciled:
        note = f"分项之和 {parts_sum} 对总变化额 {total_change} 守恒（容差 0.01）"
    else:
        note = (
            f"分项之和 {parts_sum} ≠ 总变化额 {total_change}，"
            f"未分配残差 {residual} 显式列示，禁止静默凑整"
        )
    return AdditiveBridgeResult(
        reconciled=reconciled,
        total_change=total_change,
        allocated=allocated,
        residual=residual,
        note=note,
    )



# ---- C06：经验参考值只能作提示 ----


@dataclass(frozen=True, slots=True)
class ExperienceThresholdHint:
    """C06 经验参考提示：无判定字段，必须携带适用范围。"""

    kind: str  # 恒为 "reference_hint"
    metric_code: str
    observed: Decimal
    reference: Decimal
    reference_note: str
    applicability: str
    note: str


def experience_threshold_hint(
    *,
    metric_code: str,
    observed: Decimal,
    reference: Decimal,
    reference_note: str,
    applicability: str,
) -> ExperienceThresholdHint | None:
    """经验参考值提示（C06）。

    只输出"观察值 vs 参考值 + 适用范围"的事实性提示；
    无适用范围标注（普适化）返回 None；永不输出健康/异常判定。
    """

    if not applicability.strip():
        return None
    note = (
        f"{metric_code} 观察值 {observed}，参考值 {reference}"
        f"（{reference_note}）；该参考值适用范围：{applicability}，"
        f"仅作对照提示，不构成判定。"
    )
    return ExperienceThresholdHint(
        kind="reference_hint",
        metric_code=metric_code,
        observed=observed,
        reference=reference,
        reference_note=reference_note,
        applicability=applicability,
        note=note,
    )


# ---- I12：口径标签强制 ----

# 已登记口径集：指标 → {口径码: 展示标签}。新增指标口径先登记再引用。
REGISTERED_CALIBERS: dict[str, dict[str, str]] = {
    "roe": {
        "average_equity": "ROE（平均净资产口径）",
        "closing_equity": "ROE（期末净资产口径）",
        "weighted_average": "ROE（加权平均口径，证监会披露口径）",
    },
    "dso_days": {
        "days_360": "DSO（360 天口径）",
        "days_365": "DSO（365 天口径）",
    },
}


@dataclass(frozen=True, slots=True)
class CaliberLabeledValue:
    """I12 口径标签值：分析层引用比率必须携带。"""

    metric_code: str
    value: Decimal
    caliber: str
    display_label: str


def caliber_labeled_value(
    *, metric_code: str, value: Decimal, caliber: str
) -> CaliberLabeledValue | None:
    """带口径标签的比率值（I12）。

    仅当指标已登记口径集且口径码注册时返回；否则拒绝（None），
    不做默认口径静默回退。
    """

    labels = REGISTERED_CALIBERS.get(metric_code)
    if not labels:
        return None
    display = labels.get(caliber)
    if display is None:
        return None
    return CaliberLabeledValue(
        metric_code=metric_code, value=value, caliber=caliber, display_label=display
    )


__all__ = [
    "AdditiveBridgeResult",
    "CaliberLabeledValue",
    "ExperienceThresholdHint",
    "LinkageReviewPrompt",
    "caliber_labeled_value",
    "compound_annual_growth_rate",
    "experience_threshold_hint",
    "growth_linkage_check",
    "reconcile_additive_bridge",
]
