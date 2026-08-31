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
    payload = json.dumps(
        catalog.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
