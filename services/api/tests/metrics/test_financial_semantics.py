"""财务语义规则（C03）测试：每条规则正反例。"""

from __future__ import annotations

from decimal import Decimal

import pytest

from flow_api.metrics.financial_semantics import (
    SemanticsError,
    TypedUncomputable,
    aggregate_ratio,
    annualize,
    assert_same_currency,
    assert_same_scope,
    average_of_ratios_forbidden,
    balance_value,
    prefer_restated,
    safe_divide,
    sum_quarters_to_annual,
    ytd_to_single_quarter,
)

D = Decimal


def test_balance_policy_explicit() -> None:
    assert balance_value(D("100"), D("90"), "period_end") == D("100")
    assert balance_value(D("100"), D("90"), "average") == D("95")
    assert balance_value(D("100"), None, "average") is None
    with pytest.raises(SemanticsError):
        balance_value(D("100"), D("90"), "implicit")  # type: ignore[arg-type]


def test_quarter_annual_flow_conversions() -> None:
    assert sum_quarters_to_annual([D("1"), D("2"), D("3"), D("4")]) == D("10")
    assert sum_quarters_to_annual([D("1"), None, D("3"), D("4")]) is None
    assert sum_quarters_to_annual([D("1"), D("2")]) is None
    # 累计转单季：Q2 单季 = 上半年累计 − Q1 累计
    assert ytd_to_single_quarter(D("100"), D("60")) == D("40")


def test_annualize_forbidden_by_default() -> None:
    with pytest.raises(SemanticsError, match="禁止年化"):
        annualize(D("25"), 1)
    assert annualize(D("25"), 1, policy="linear_x4") == D("100")
    with pytest.raises(SemanticsError):
        annualize(D("25"), 5, policy="linear_x4")


def test_safe_divide_typed_reasons() -> None:
    assert safe_divide(D("1"), D("2")) == D("0.5")
    zero = safe_divide(D("1"), D("0"))
    assert isinstance(zero, TypedUncomputable) and zero.code == "zero_denominator"
    missing = safe_divide(None, D("2"))
    assert isinstance(missing, TypedUncomputable) and missing.code == "missing_operand"
    negative = safe_divide(D("1"), D("-2"))
    assert isinstance(negative, TypedUncomputable) and negative.code == "negative_denominator"


def test_ratio_aggregation_sums_parts_first() -> None:
    # 分子分母先汇总再相除
    result = aggregate_ratio([D("10"), D("30")], [D("100"), D("100")])
    assert result == D("0.2")
    # 缺任一输入则缺失
    assert isinstance(aggregate_ratio([D("10"), None], [D("100"), D("100")]), TypedUncomputable)
    # 比率求平均被禁止
    with pytest.raises(SemanticsError, match="禁止对比率求平均"):
        average_of_ratios_forbidden()


def test_currency_and_scope_guards() -> None:
    assert_same_currency("CNY", "CNY")
    with pytest.raises(SemanticsError, match="不做汇率换算"):
        assert_same_currency("CNY", "HKD")
    with pytest.raises(SemanticsError, match="拒绝合并"):
        assert_same_scope("consolidated", "parent")


def test_restated_comparison_prefers_restated_keeps_original() -> None:
    assert prefer_restated(D("120"), D("100")) == D("120")
    assert prefer_restated(None, D("100")) == D("100")
