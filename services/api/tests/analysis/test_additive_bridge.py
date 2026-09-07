"""U2/C08：可加和成本桥守恒契约测试（TDD 先行）。

契约：
- 驱动拆解各分项之和必须还原总变化额（容差 0.01，与既有 Driver 对账一致）；
- 不守恒时必须显式返回残差分项（"未分配残差"），不得静默凑整或丢弃；
- 交互项按固定分配规则（本实现：比例分摊给主分项，规则写入分解说明）；
- 输入缺失（总变化额或任一分项为 None）→ 返回 None，不编造。
"""

from __future__ import annotations

from decimal import Decimal

from flow_api.analysis.deterministic import reconcile_additive_bridge


def _parts(**kwargs: Decimal) -> dict[str, Decimal]:
    return dict(kwargs)


def test_bridge_reconciles_exactly() -> None:
    result = reconcile_additive_bridge(
        total_change=Decimal("100.00"),
        parts=_parts(price=Decimal("40.00"), volume=Decimal("60.00")),
    )
    assert result.residual == Decimal("0.00")
    assert result.reconciled is True
    assert result.allocated == {"price": Decimal("40.00"), "volume": Decimal("60.00")}


def test_bridge_reports_explicit_residual_when_not_conservative() -> None:
    # 分项和 95 ≠ 总变化 100：残差 +5 必须显式出现，不得分摊掩盖
    result = reconcile_additive_bridge(
        total_change=Decimal("100.00"),
        parts=_parts(price=Decimal("40.00"), volume=Decimal("55.00")),
    )
    assert result.reconciled is False
    assert result.residual == Decimal("5.00")
    assert result.allocated == {"price": Decimal("40.00"), "volume": Decimal("55.00")}
    assert "未分配残差" in result.note


def test_residual_within_tolerance_counts_reconciled() -> None:
    result = reconcile_additive_bridge(
        total_change=Decimal("100.00"),
        parts=_parts(price=Decimal("40.005"), volume=Decimal("60.00")),
    )
    assert result.reconciled is True
    assert abs(result.residual) <= Decimal("0.01")


def test_missing_input_returns_none() -> None:
    assert (
        reconcile_additive_bridge(
            total_change=None, parts=_parts(price=Decimal("1"))
        )
        is None
    )
    assert (
        reconcile_additive_bridge(
            total_change=Decimal("1"),
            parts=_parts(price=Decimal("1"), volume=None),  # type: ignore[dict-item]
        )
        is None
    )
