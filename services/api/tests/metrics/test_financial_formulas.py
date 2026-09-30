"""S01 财务指标目录 F1：公式注册表 + 财务公式单测。

覆盖：
- 注册表机制：已注册公式可枚举；重复注册失败；未注册公式报 unsupported_formula
- arity 校验：依赖数不符报 formula_arity_mismatch
- 财务公式算术：ratio_times_100 / product / annualize_ratio / sum_dependencies / add
- 零回归：既有公式（ratio / subtract / closing_ar_*）行为逐字保持
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from flow_api.metrics.decimal_math import MetricCalculationError
from flow_api.metrics.formulas import evaluate_derived_metric, registered_formulas
from flow_api.metrics.models import MetricSpec


def _spec(
    code: str = "m",
    *,
    formula: str = "ratio",
    deps: tuple[str, ...] = ("a", "b"),
    unit: str = "percent",
    aggregation: str = "average",
    scale: int = 4,
) -> MetricSpec:
    return MetricSpec(
        metric_code=code,
        version=1,
        name="测试指标",
        business_definition="测试",
        formula=formula,
        dependencies=deps,
        aggregation=aggregation,  # type: ignore[arg-type]
        time_behavior="flow",
        unit=unit,  # type: ignore[arg-type]
        output_scale=scale,
        allowed_dimension_sets=(("organization",),),
    )


# ── 注册表机制 ────────────────────────────────────────────────────


def test_registry_lists_known_formulas() -> None:
    names = registered_formulas()
    for expected in (
        "ratio",
        "subtract",
        "closing_ar_over_trailing_12_revenue_times_365",
        "ratio_times_100",
        "product",
        "annualize_ratio",
        "sum_dependencies",
        "add",
    ):
        assert expected in names


def test_unsupported_formula_raises() -> None:
    spec = _spec(formula="no_such_formula")
    with pytest.raises(MetricCalculationError) as exc:
        evaluate_derived_metric(spec, {"a": Decimal("1"), "b": Decimal("2")})
    assert exc.value.code == "unsupported_formula"


def test_arity_mismatch_raises() -> None:
    spec = _spec(formula="ratio", deps=("a", "b", "c"))
    with pytest.raises(MetricCalculationError) as exc:
        evaluate_derived_metric(spec, {"a": Decimal("1"), "b": Decimal("2"), "c": Decimal("3")})
    assert exc.value.code == "formula_arity_mismatch"


def test_missing_dependency_raises() -> None:
    spec = _spec(formula="ratio", deps=("a", "b"))
    with pytest.raises(MetricCalculationError) as exc:
        evaluate_derived_metric(spec, {"a": Decimal("1")})
    assert exc.value.code == "missing_dependency"


# ── 既有公式零回归 ────────────────────────────────────────────────


def test_ratio_unchanged() -> None:
    spec = _spec(formula="ratio", unit="ratio", aggregation="ratio")
    got = evaluate_derived_metric(spec, {"a": Decimal("30"), "b": Decimal("120")})
    assert got.exact_value == Decimal("0.25")


def test_subtract_unchanged() -> None:
    spec = _spec(formula="subtract", unit="CNY", aggregation="sum")
    got = evaluate_derived_metric(spec, {"a": Decimal("100"), "b": Decimal("30")})
    assert got.exact_value == Decimal("70")


def test_dso_formula_unchanged() -> None:
    spec = _spec(
        formula="closing_ar_over_trailing_12_revenue_times_365", unit="day", aggregation="ratio"
    )
    got = evaluate_derived_metric(spec, {"a": Decimal("1200"), "b": Decimal("12000")})
    # 1200/12000*365 = 36.5
    assert got.exact_value == Decimal("36.5")


# ── 财务公式 ──────────────────────────────────────────────────────


def test_ratio_times_100_is_percent() -> None:
    spec = _spec(formula="ratio_times_100", unit="percent", deps=("gross", "revenue"))
    got = evaluate_derived_metric(
        spec, {"gross": Decimal("38458"), "revenue": Decimal("126895")}
    )
    # 38458/126895*100 = 30.3069...（ROUND_HALF_UP 到 4 位）
    assert got.exact_value == Decimal("30.3069")


def test_product_is_multiplication() -> None:
    spec = _spec(
        formula="product", unit="percent", deps=("net_margin", "turnover", "equity_multiplier")
    )
    got = evaluate_derived_metric(
        spec,
        {
            "net_margin": Decimal("0.076"),
            "turnover": Decimal("0.71"),
            "equity_multiplier": Decimal("2.33"),
        },
    )
    # 0.076*0.71*2.33 = 0.12572...（ROE 12.6% 的量级）
    assert got.exact_value == Decimal("0.1257")


def test_annualize_ratio_multiplies_by_12() -> None:
    spec = _spec(formula="annualize_ratio", unit="percent", deps=("period_flow", "avg_stock"))
    got = evaluate_derived_metric(
        spec, {"period_flow": Decimal("967.4"), "avg_stock": Decimal("10000")}
    )
    # 967.4/10000*12 = 1.16088
    assert got.exact_value == Decimal("1.1609")


def test_sum_dependencies_variadic() -> None:
    spec = _spec(
        formula="sum_dependencies", unit="CNY", aggregation="sum", deps=("a", "b", "c", "d")
    )
    got = evaluate_derived_metric(
        spec,
        {"a": Decimal("1"), "b": Decimal("2"), "c": Decimal("3"), "d": Decimal("4")},
    )
    assert got.exact_value == Decimal("10")


def test_add_variadic() -> None:
    spec = _spec(formula="add", unit="CNY", aggregation="sum", deps=("a", "b", "c"))
    got = evaluate_derived_metric(
        spec, {"a": Decimal("10.5"), "b": Decimal("20.25"), "c": Decimal("0.25")}
    )
    assert got.exact_value == Decimal("31")


def test_first_and_second_of_ratio() -> None:
    a = _spec(formula="first_of_ratio", unit="ratio", aggregation="ratio", deps=("num", "den"))
    got_a = evaluate_derived_metric(a, {"num": Decimal("1"), "den": Decimal("4")})
    assert got_a.exact_value == Decimal("0.25")
    # second_of_ratio：values[1] / values[0]，故 num/den
    b = _spec(formula="second_of_ratio", unit="ratio", aggregation="ratio", deps=("den", "num"))
    got_b = evaluate_derived_metric(b, {"den": Decimal("1"), "num": Decimal("4")})
    assert got_b.exact_value == Decimal("4")


def test_zero_denominator_still_raises() -> None:
    spec = _spec(formula="ratio_times_100", unit="percent")
    with pytest.raises(MetricCalculationError) as exc:
        evaluate_derived_metric(spec, {"a": Decimal("1"), "b": Decimal("0")})
    assert exc.value.code == "zero_denominator"


# ── 新枚举值可用性 ────────────────────────────────────────────────


@pytest.mark.parametrize("unit", ["percent", "multiple", "percentage_point"])
def test_financial_units_accepted(unit: str) -> None:
    spec = _spec(unit=unit)
    assert spec.unit == unit


def test_average_aggregation_accepted() -> None:
    spec = _spec(aggregation="average")
    assert spec.aggregation == "average"


def test_conservation_law_optional() -> None:
    spec = MetricSpec(
        metric_code="roe",
        version=1,
        name="ROE",
        business_definition="净利润 / 平均所有者权益",
        formula="ratio_times_100",
        dependencies=("net_profit", "avg_equity"),
        aggregation="average",
        time_behavior="flow",
        unit="percent",
        output_scale=4,
        allowed_dimension_sets=(("organization",),),
        conservation_law="roe_identity",
    )
    assert spec.conservation_law == "roe_identity"


def test_conservation_law_defaults_to_none() -> None:
    assert _spec().conservation_law is None
