"""财务语义：期间、范围、精度与异常（C03）。

规则（每条在 tests/metrics/test_financial_semantics.py 有正反例）：
- 余额口径必须显式：期末或平均（(期初+期末)/2），禁止隐式混用；
- 单季与累计的转换只在流量且期间链完整时允许；累计转单季需要减除其余季度；
- 年化默认禁止（单季未年化），显式年化必须携带政策标记；
- 零分母/负权益/币种或合并范围不一致 → typed 原因，不返回伪造值；
- 比率聚合先汇总分子分母再相除，禁止对比率求平均；
- 不做汇率换算（汇率是分析层显式输入）；
- 重述比较默认取重述版，原版本可查询。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


class SemanticsError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


BalancePolicy = Literal["period_end", "average"]


def balance_value(
    end: Decimal | None, open_: Decimal | None, policy: BalancePolicy
) -> Decimal | None:
    """余额取值：period_end 用期末；average 用（期初+期末）/2，任一侧缺失则缺失。"""

    if policy == "period_end":
        return end
    if policy == "average":
        if end is None or open_ is None:
            return None
        return (end + open_) / 2
    raise SemanticsError("unknown_balance_policy", f"未知余额口径：{policy}")


def sum_quarters_to_annual(quarters: list[Decimal | None]) -> Decimal | None:
    """四个单季流量加总为年度；缺任何一季则缺失（不补零）。"""

    if len(quarters) != 4 or any(q is None for q in quarters):
        return None
    total = Decimal(0)
    for quarter in quarters:
        total += quarter  # type: ignore[operator]
    return total


def ytd_to_single_quarter(ytd_current: Decimal, ytd_prior_quarters: Decimal) -> Decimal:
    """累计转单季：本期单季 = 累计本期 − 累计上季末（仅限同一财年内的流量）。"""

    return ytd_current - ytd_prior_quarters


def annualize(flow_value: Decimal, quarters_covered: int, *, policy: str = "never") -> Decimal:
    """年化默认禁止；显式 policy='linear_x4' 时按 4/已覆盖季度数放大。"""

    if policy == "never":
        raise SemanticsError(
            "annualization_forbidden",
            "默认禁止年化（单季未年化）；确需年化必须显式指定政策并标注",
        )
    if policy != "linear_x4":
        raise SemanticsError("unknown_annualize_policy", f"未知年化政策：{policy}")
    if not 1 <= quarters_covered <= 4:
        raise SemanticsError("invalid_quarters", f"季度数非法：{quarters_covered}")
    return flow_value * Decimal(4) / Decimal(quarters_covered)


@dataclass(frozen=True, slots=True)
class TypedUncomputable:
    code: str
    message: str


def safe_divide(
    numerator: Decimal | None, denominator: Decimal | None
) -> Decimal | TypedUncomputable:
    """除法守卫：零分母与缺失返回 typed 原因，不伪造数值。"""

    if numerator is None or denominator is None:
        return TypedUncomputable("missing_operand", "分子或分母缺失，不可计算")
    if denominator == 0:
        return TypedUncomputable("zero_denominator", "分母为零，比率无意义")
    if denominator < 0:
        return TypedUncomputable(
            "negative_denominator", "分母为负（如负权益），比率符号失真，需人工解读"
        )
    return numerator / denominator


def aggregate_ratio(
    numerators: list[Decimal | None], denominators: list[Decimal | None]
) -> Decimal | TypedUncomputable:
    """比率聚合：先汇总分子分母再相除；禁止对比率求平均。缺失传染。"""

    if any(v is None for v in numerators) or any(v is None for v in denominators):
        return TypedUncomputable("missing_operand", "聚合输入存在缺失，不可计算")
    numerator = sum((n for n in numerators if n is not None), Decimal(0))
    denominator = sum((d for d in denominators if d is not None), Decimal(0))
    return safe_divide(numerator, denominator)


def average_of_ratios_forbidden() -> None:
    """对比率求平均是口径错误；本函数存在即禁止，调用即抛错。"""

    raise SemanticsError(
        "ratio_average_forbidden", "禁止对比率求平均：聚合应先汇总分子分母再相除"
    )


def assert_same_currency(currency_a: str, currency_b: str) -> None:
    if currency_a != currency_b:
        raise SemanticsError(
            "currency_mismatch",
            f"币种不一致（{currency_a} vs {currency_b}）；本系统不做汇率换算",
        )


def assert_same_scope(scope_a: str, scope_b: str) -> None:
    if scope_a != scope_b:
        raise SemanticsError(
            "scope_mismatch", f"合并范围不一致（{scope_a} vs {scope_b}），拒绝合并比较"
        )


def prefer_restated(restated: Decimal | None, original: Decimal | None) -> Decimal | None:
    """重述比较：默认取重述版；重述缺失时回退原版。原版永不被覆盖。"""

    return restated if restated is not None else original


__all__ = [
    "SemanticsError",
    "TypedUncomputable",
    "aggregate_ratio",
    "annualize",
    "assert_same_currency",
    "assert_same_scope",
    "average_of_ratios_forbidden",
    "balance_value",
    "prefer_restated",
    "safe_divide",
    "sum_quarters_to_annual",
    "ytd_to_single_quarter",
]
