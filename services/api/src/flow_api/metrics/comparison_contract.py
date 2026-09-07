"""比较合同（P02，订正 C16/C17）：比较前提不满足时给出类型化原因。

规则（tests/metrics/test_comparison_contract.py 有正反例）：
- 币种、合并范围、期间类型、重述版本必须一致；存量与流量期间必须对齐；
- 预算比较必须显式指定预算版本；预算粒度必须与实际同粒度（禁止重复联接放大）；
- 预算为零或负数时不输出完成率（无意义且误导），返回类型化原因；
- 任何不可比都不返回 0、不静默退回其他期间。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True, slots=True)
class Incomparable:
    """类型化不可比原因；调用方据此渲染解释性空状态。"""

    code: str
    message: str


PeriodType = Literal["month", "ytd", "trailing_12"]
MeasureKind = Literal["flow", "stock"]


@dataclass(frozen=True, slots=True)
class ComparisonContext:
    currency: str
    scope: str
    period_type: PeriodType
    restatement_version: str
    measure_kind: MeasureKind
    granularity: str = "consolidated"


def comparability_issues(
    actual: ComparisonContext, comparison: ComparisonContext
) -> tuple[Incomparable, ...]:
    issues: list[Incomparable] = []
    if actual.currency != comparison.currency:
        issues.append(
            Incomparable(
                "currency_mismatch",
                f"币种不一致（{actual.currency} vs {comparison.currency}）",
            )
        )
    if actual.scope != comparison.scope:
        issues.append(
            Incomparable(
                "scope_mismatch",
                f"合并范围不一致（{actual.scope} vs {comparison.scope}）",
            )
        )
    if actual.period_type != comparison.period_type:
        message = (
            f"期间类型不一致（{actual.period_type} vs {comparison.period_type}）；"
            "单月/累计不可直接比较"
        )
        issues.append(Incomparable("period_misalignment", message))
    if actual.restatement_version != comparison.restatement_version:
        message = (
            f"重述版本不一致（{actual.restatement_version} vs "
            f"{comparison.restatement_version}）；默认取重述版，缺失时显式声明"
        )
        issues.append(Incomparable("restatement_version_mismatch", message))
    if actual.measure_kind != comparison.measure_kind:
        message = (
            f"存量与流量混比（{actual.measure_kind} vs {comparison.measure_kind}）；"
            "期间语义不同"
        )
        issues.append(Incomparable("stock_flow_mixing", message))
    return tuple(issues)


def budget_completion_rate(
    actual: Decimal, budget: Decimal, *, budget_version: str | None,
    actual_granularity: str = "consolidated", budget_granularity: str = "consolidated",
) -> Decimal | Incomparable:
    """预算完成率：前提不满足返回类型化原因，不返回 0 或伪比率。

    - 未指定预算版本 → budget_version_missing；
    - 预算粒度与实际粒度不一致 → budget_grain_mismatch（禁止重复联接放大）；
    - 预算为零或负数 → nonpositive_budget（完成率无意义且误导）。
    """

    if budget_version is None or not budget_version.strip():
        return Incomparable("budget_version_missing", "未指定预算版本，实际与哪一版目标不可比")
    if actual_granularity != budget_granularity:
        return Incomparable(
            "budget_grain_mismatch",
            f"预算粒度（{budget_granularity}）与实际粒度（{actual_granularity}）不一致，"
            "禁止重复联接放大分母或分子",
        )
    if budget == 0 or budget < 0:
        return Incomparable(
            "nonpositive_budget",
            "预算为零或为负，完成率无意义且误导；请改用差额（variance）展示",
        )
    return actual / budget


__all__ = [
    "ComparisonContext",
    "Incomparable",
    "budget_completion_rate",
    "comparability_issues",
]
