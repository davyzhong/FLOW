"""S01 财务指标目录 F1：公式注册表 + 财务公式。

原实现是硬编码 if 链（`ratio` / `subtract` / `closing_ar_*` 逐个 if），
新增 10+ 财务公式时必须改核心逻辑。本模块改为**注册表**：

```python
@register_formula(arity=2)
def _roe(metric, a, b): ...
```

纪律：
- 每个公式是纯函数：只依赖依赖值 + MetricSpec，不触碰 DB/IO；
- 公式只做算术，不做判断（口径判断在指标目录的 business_definition 与守恒声明）；
- 除零由 calculate_ratio 统一报 zero_denominator，公式不得自行吞掉；
- 注册表在导入时构建，重复注册立即失败（避免静默覆盖）。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from decimal import Decimal

from flow_api.metrics.decimal_math import (
    CalculatedDecimal,
    MetricCalculationError,
    calculate_amount,
    calculate_ratio,
)
from flow_api.metrics.models import MetricSpec

FormulaFn = Callable[[MetricSpec, tuple[Decimal, ...]], CalculatedDecimal]
_REGISTRY: dict[str, tuple[int, FormulaFn]] = {}


def _formula(*names: str, arity: int) -> Callable[[FormulaFn], FormulaFn]:
    def decorator(fn: FormulaFn) -> FormulaFn:
        for name in names:
            if name in _REGISTRY:
                raise ValueError(f"duplicate formula registration: {name}")
            _REGISTRY[name] = (arity, fn)
        return fn

    return decorator


# ── 既有公式（原 if 链搬过来，行为逐字保持） ────────────────────────────


@_formula("subtract", arity=2)
def _subtract(metric: MetricSpec, values: tuple[Decimal, ...]) -> CalculatedDecimal:
    return calculate_amount(
        metric.metric_code,
        values[0] - values[1],
        output_scale=metric.output_scale,
    )


@_formula("ratio", arity=2)
def _ratio(metric: MetricSpec, values: tuple[Decimal, ...]) -> CalculatedDecimal:
    return calculate_ratio(
        metric.metric_code,
        values[0],
        values[1],
        output_scale=metric.output_scale,
    )


@_formula("closing_ar_over_trailing_12_revenue_times_365", arity=2)
def _dso(metric: MetricSpec, values: tuple[Decimal, ...]) -> CalculatedDecimal:
    return calculate_ratio(
        metric.metric_code,
        values[0],
        values[1],
        multiplier=Decimal("365"),
        output_scale=metric.output_scale,
    )


# ── S01 F1 新增：财务公式 ─────────────────────────────────────────────


@_formula("sum_dependencies", arity=-1)
def _sum_dependencies(metric: MetricSpec, values: tuple[Decimal, ...]) -> CalculatedDecimal:
    total = Decimal("0")
    for value in values:
        total += value
    return calculate_amount(metric.metric_code, total, output_scale=metric.output_scale)


@_formula("ratio_times_100", arity=2)
def _ratio_percent(metric: MetricSpec, values: tuple[Decimal, ...]) -> CalculatedDecimal:
    """百分比口径：分子/分母 × 100（如毛利率 = 毛利/营业收入）。"""
    return calculate_ratio(
        metric.metric_code,
        values[0],
        values[1],
        multiplier=Decimal("100"),
        output_scale=metric.output_scale,
    )


@_formula("product", arity=-1)
def _product(metric: MetricSpec, values: tuple[Decimal, ...]) -> CalculatedDecimal:
    """连乘（杜邦三因子、CCC 组合等）。"""
    result = Decimal("1")
    for value in values:
        result *= value
    return calculate_amount(metric.metric_code, result, output_scale=metric.output_scale)


@_formula("annualize_ratio", arity=2)
def _annualize_ratio(metric: MetricSpec, values: tuple[Decimal, ...]) -> CalculatedDecimal:
    """年化比率：(期间流量/平均存量) × 12，用于 YTD ROE / YTD ROA。

    dependencies = (期间流量, 平均存量)；平均存量由 aggregation=average 提供，
    缺失时由调用方报 insufficient_history（不静默用期末值，见工作包未决问题 Q2）。
    """
    return calculate_ratio(
        metric.metric_code,
        values[0],
        values[1],
        multiplier=Decimal("12"),
        output_scale=metric.output_scale,
    )


@_formula("add", arity=-1)
def _add(metric: MetricSpec, values: tuple[Decimal, ...]) -> CalculatedDecimal:
    total = Decimal("0")
    for value in values:
        total += value
    return calculate_amount(metric.metric_code, total, output_scale=metric.output_scale)


@_formula("first_of_ratio", arity=2)
def _first_of_ratio(metric: MetricSpec, values: tuple[Decimal, ...]) -> CalculatedDecimal:
    """与 ratio 等价，显式命名为 first_of_ratio 便于目录可读（应收/营业收入 等）。"""
    return calculate_ratio(
        metric.metric_code,
        values[0],
        values[1],
        output_scale=metric.output_scale,
    )


@_formula("second_of_ratio", arity=2)
def _second_of_ratio(metric: MetricSpec, values: tuple[Decimal, ...]) -> CalculatedDecimal:
    return calculate_ratio(
        metric.metric_code,
        values[1],
        values[0],
        output_scale=metric.output_scale,
    )


# ── 求值入口 ─────────────────────────────────────────────────────────


def registered_formulas() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


def evaluate_derived_metric(
    metric: MetricSpec, dependency_values: Mapping[str, Decimal]
) -> CalculatedDecimal:
    missing = [
        dependency
        for dependency in metric.dependencies
        if dependency not in dependency_values
    ]
    if missing:
        raise MetricCalculationError(
            metric.metric_code,
            "missing_dependency",
            f"{metric.metric_code} is missing dependencies: {missing}",
        )
    values = tuple(dependency_values[dependency] for dependency in metric.dependencies)
    entry = _REGISTRY.get(metric.formula)
    if entry is None:
        raise MetricCalculationError(
            metric.metric_code,
            "unsupported_formula",
            f"unsupported derived formula for {metric.metric_code}: {metric.formula}",
        )
    arity, fn = entry
    if arity >= 0 and len(values) != arity:
        raise MetricCalculationError(
            metric.metric_code,
            "formula_arity_mismatch",
            f"{metric.metric_code} formula {metric.formula} expects {arity} "
            f"dependencies, got {len(values)}",
        )
    return fn(metric, values)


__all__ = ["evaluate_derived_metric", "registered_formulas"]
