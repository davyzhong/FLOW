"""U2/C06 + I12：经验阈值适用条件与口径标签契约测试（TDD 先行）。

C06：经验参考值（如流动比率"约 2"）只能作为提示——必须携带行业/主体
适用范围标注，禁止输出普适"健康/异常"硬判定。
I12：分析层引用比率（如 ROE）必须携带口径标签（分母口径等）；
未注册口径或缺失标签 → 拒绝引用（返回 None），不默认口径。
"""

from __future__ import annotations

from decimal import Decimal

from flow_api.analysis.deterministic import (
    caliber_labeled_value,
    experience_threshold_hint,
)

# ---- C06 ----


def test_experience_hint_is_hint_not_verdict() -> None:
    hint = experience_threshold_hint(
        metric_code="current_ratio",
        observed=Decimal("1.4"),
        reference=Decimal("2.0"),
        reference_note="教科书经验参考值",
        applicability="通用制造业经验；物流行业应收占比高，参考区间不同",
    )
    assert hint is not None
    assert hint.kind == "reference_hint"
    assert hint.applicability.strip()  # 非空即携带适用范围（C06 由 None 分支锁死空值）
    # 硬约束：提示对象没有任何判定性字段/词
    assert not hasattr(hint, "verdict")
    for word in ("健康", "异常", "良好", "不合格"):
        assert word not in hint.note


def test_experience_hint_requires_applicability_scope() -> None:
    # 无适用范围标注的经验值不得输出（防普适化）
    assert (
        experience_threshold_hint(
            metric_code="current_ratio",
            observed=Decimal("1.4"),
            reference=Decimal("2.0"),
            reference_note="经验值",
            applicability="",
        )
        is None
    )


# ---- I12 ----


def test_caliber_label_roundtrip() -> None:
    labeled = caliber_labeled_value(
        metric_code="roe", value=Decimal("0.0226"), caliber="average_equity"
    )
    assert labeled is not None
    assert labeled.metric_code == "roe"
    assert labeled.caliber == "average_equity"
    assert labeled.display_label == "ROE（平均净资产口径）"


def test_unknown_caliber_rejected() -> None:
    assert (
        caliber_labeled_value(
            metric_code="roe", value=Decimal("0.0226"), caliber="magic"
        )
        is None
    )


def test_metric_without_registered_calibers_rejected() -> None:
    # 未登记口径集的指标不得静默放行（需先登记口径清单）
    assert (
        caliber_labeled_value(
            metric_code="mystery_ratio", value=Decimal("1"), caliber="anything"
        )
        is None
    )
