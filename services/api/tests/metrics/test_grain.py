from __future__ import annotations

import importlib
from pathlib import Path
from uuid import UUID

import pytest

from flow_api.metrics.catalog import load_metric_catalog

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CATALOG = load_metric_catalog(REPOSITORY_ROOT / "config/metrics/flow_v1_metrics.yaml")
METRICS = {metric.metric_code: metric for metric in CATALOG.metrics}
IDS = {
    "organization": UUID("00000000-0000-0000-0000-000000000001"),
    "customer": UUID("00000000-0000-0000-0000-000000000002"),
    "customer_segment": UUID("00000000-0000-0000-0000-000000000003"),
    "logistics_product": UUID("00000000-0000-0000-0000-000000000004"),
    "region": UUID("00000000-0000-0000-0000-000000000005"),
}


def _grain_module():
    try:
        return importlib.import_module("flow_api.metrics.grain")
    except ModuleNotFoundError:
        pytest.fail("flow_api.metrics.grain does not exist")


def test_operating_row_projects_to_exact_allowed_grains() -> None:
    module = _grain_module()

    grains = module.project_metric_grains(METRICS["revenue"], IDS)

    assert len(grains) == 7
    assert module.MetricGrain() in grains
    assert module.MetricGrain(customer_id=IDS["customer"]) in grains
    assert module.MetricGrain(customer_segment_id=IDS["customer_segment"]) in grains
    assert module.MetricGrain(
        customer_segment_id=IDS["customer_segment"],
        logistics_product_id=IDS["logistics_product"],
    ) in grains
    assert not any(
        grain.customer_id is not None and grain.customer_segment_id is not None
        for grain in grains
    )
    assert grains == tuple(sorted(grains, key=lambda grain: grain.sort_key))


def test_budget_projection_does_not_invent_customer_or_region() -> None:
    module = _grain_module()

    grains = module.project_metric_grains(METRICS["revenue"], IDS, budget=True)

    assert len(grains) == 5
    assert not any(grain.customer_id is not None for grain in grains)
    assert not any(grain.region_id is not None for grain in grains)


def test_unsupported_grain_is_rejected() -> None:
    module = _grain_module()
    unsupported = module.MetricGrain(
        organization_id=IDS["organization"],
        customer_id=IDS["customer"],
    )

    with pytest.raises(module.UnsupportedMetricGrainError):
        module.validate_grain(METRICS["revenue"], unsupported)
