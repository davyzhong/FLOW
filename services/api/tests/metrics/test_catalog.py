from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CATALOG_PATH = REPOSITORY_ROOT / "config/metrics/flow_v1_metrics.yaml"
EXPECTED_METRICS = {
    "ar_balance",
    "cash_conversion",
    "collection_rate",
    "cost_per_order",
    "direct_cost",
    "dso",
    "fulfilled_units",
    "fulfillment_cost_rate",
    "gross_margin",
    "gross_profit",
    "operating_cash_flow",
    "operating_profit",
    "orders",
    "revenue",
    "revenue_per_order",
}


def _catalog_module():
    try:
        return importlib.import_module("flow_api.metrics.catalog")
    except ModuleNotFoundError:
        pytest.fail("flow_api.metrics.catalog does not exist")


def test_flow_v1_catalog_freezes_exact_metric_identity_and_dependencies() -> None:
    module = _catalog_module()
    assert CATALOG_PATH.is_file(), "versioned metric catalog is not committed"

    catalog = module.load_metric_catalog(CATALOG_PATH)

    assert catalog.definition_set_id == "flow.metrics.logistics.v1"
    assert catalog.engine_version == "flow.metrics.engine.v1"
    assert {metric.metric_code for metric in catalog.metrics} == EXPECTED_METRICS
    assert len({(metric.metric_code, metric.version) for metric in catalog.metrics}) == 15
    assert all(metric.version == 1 for metric in catalog.metrics)
    assert module.topological_metric_order(catalog)[-1] == "dso"


def test_catalog_has_explicit_aggregation_time_and_dimension_rules() -> None:
    module = _catalog_module()
    catalog = module.load_metric_catalog(CATALOG_PATH)
    metrics = {metric.metric_code: metric for metric in catalog.metrics}

    assert metrics["revenue"].aggregation == "sum"
    assert metrics["revenue"].time_behavior == "flow"
    assert ("customer_segment", "logistics_product") in metrics[
        "revenue"
    ].allowed_dimension_sets
    assert metrics["ar_balance"].aggregation == "closing_balance"
    assert metrics["ar_balance"].time_behavior == "balance"
    assert metrics["ar_balance"].allowed_dimension_sets == (
        (),
        ("customer",),
        ("customer_segment",),
    )
    assert metrics["gross_margin"].aggregation == "ratio"
    assert metrics["gross_margin"].dependencies == ("gross_profit", "revenue")
    assert metrics["dso"].formula == "closing_ar_over_trailing_12_revenue_times_365"


def test_catalog_fingerprint_is_deterministic() -> None:
    module = _catalog_module()
    first = module.load_metric_catalog(CATALOG_PATH)
    second = module.load_metric_catalog(CATALOG_PATH)

    assert module.metric_catalog_hash(first) == module.metric_catalog_hash(second)
    assert (
        module.metric_catalog_hash(first)
        == "4214ae85339eb7495defb69f1d59fdddec5e3183d5d4ba64c966be9f53270b38"
    )
    assert hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest() == (
        "705ee41b938d8496b870cb60f662bf14629299ed77351343792bbc07f5a22916"
    )


@pytest.mark.parametrize(
    ("dependencies", "expected_message"),
    [
        ({"revenue": ["unknown_metric"]}, "unknown dependencies"),
        ({"revenue": ["direct_cost"], "direct_cost": ["revenue"]}, "contains a cycle"),
    ],
)
def test_catalog_rejects_unknown_or_cyclic_dependencies(
    dependencies: dict[str, list[str]], expected_message: str
) -> None:
    module = _catalog_module()
    payload = module.load_metric_catalog(CATALOG_PATH).model_dump(mode="json")
    for metric in payload["metrics"]:
        if metric["metric_code"] in dependencies:
            metric["dependencies"] = dependencies[metric["metric_code"]]

    with pytest.raises(ValueError, match=expected_message):
        module.MetricCatalog.model_validate(payload)
