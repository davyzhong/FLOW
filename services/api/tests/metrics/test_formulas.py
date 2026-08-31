from __future__ import annotations

import importlib
from decimal import Decimal
from pathlib import Path

import pytest

from flow_api.metrics.catalog import load_metric_catalog

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CATALOG = load_metric_catalog(REPOSITORY_ROOT / "config/metrics/flow_v1_metrics.yaml")
METRICS = {metric.metric_code: metric for metric in CATALOG.metrics}


def _formula_module():
    try:
        return importlib.import_module("flow_api.metrics.formulas")
    except ModuleNotFoundError:
        pytest.fail("flow_api.metrics.formulas does not exist")


def test_declared_subtraction_and_ratio_formulas_use_dependency_order() -> None:
    module = _formula_module()

    gross_profit = module.evaluate_derived_metric(
        METRICS["gross_profit"],
        {"revenue": Decimal("100.0000"), "direct_cost": Decimal("65.0000")},
    )
    gross_margin = module.evaluate_derived_metric(
        METRICS["gross_margin"],
        {"gross_profit": gross_profit.exact_value, "revenue": Decimal("100.0000")},
    )

    assert gross_profit.exact_value == Decimal("35.0000")
    assert gross_profit.persisted_value == Decimal("35.0000")
    assert gross_margin.exact_value == Decimal("0.350000")
    assert gross_margin.persisted_value == Decimal("0.3500")


def test_cash_conversion_and_dso_formulas_are_exact() -> None:
    module = _formula_module()

    cash_conversion = module.evaluate_derived_metric(
        METRICS["cash_conversion"],
        {
            "operating_cash_flow": Decimal("4941609.8078"),
            "operating_profit": Decimal("6708895.8378"),
        },
    )
    dso = module.evaluate_derived_metric(
        METRICS["dso"],
        {
            "ar_balance": Decimal("3620569.1952"),
            "revenue": Decimal("26300990.4095"),
        },
    )

    assert cash_conversion.exact_value == Decimal("0.736576")
    assert dso.exact_value == Decimal("50.245551")


def test_formula_requires_every_declared_dependency() -> None:
    module = _formula_module()

    with pytest.raises(module.MetricCalculationError) as error:
        module.evaluate_derived_metric(
            METRICS["gross_margin"], {"gross_profit": Decimal("35")}
        )

    assert error.value.code == "missing_dependency"
    assert error.value.metric_code == "gross_margin"
