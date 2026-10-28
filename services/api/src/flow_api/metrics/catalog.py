from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from flow_api.metrics.models import MetricCatalog


def load_metric_catalog(path: str | Path) -> MetricCatalog:
    payload: Any = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("metric catalog must be a mapping")
    return MetricCatalog.model_validate(payload)


def topological_metric_order(catalog: MetricCatalog) -> tuple[str, ...]:
    metrics = {metric.metric_code: metric for metric in catalog.metrics}
    completed: set[str] = set()
    result: list[str] = []

    def visit(metric_code: str) -> None:
        if metric_code in completed:
            return
        for dependency in metrics[metric_code].dependencies:
            visit(dependency)
        completed.add(metric_code)
        result.append(metric_code)

    for metric in catalog.metrics:
        visit(metric.metric_code)
    return tuple(result)


def metric_catalog_hash(catalog: MetricCatalog) -> str:
    catalog_data = catalog.model_dump(mode="json")
    # Schema additions with an unset optional field must not mutate the identity
    # of a published catalog. Once a conservation law is explicitly declared,
    # its value participates in the fingerprint. Same rule for the financial
    # account binding (R5): only explicitly declared bindings are identity-bearing.
    for metric in catalog_data["metrics"]:
        if metric.get("conservation_law") is None:
            metric.pop("conservation_law", None)
        if metric.get("financial_account") is None:
            metric.pop("financial_account", None)
    payload = json.dumps(
        catalog_data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
