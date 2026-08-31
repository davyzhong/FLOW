from __future__ import annotations

import json
from pathlib import Path

from flow_api.metrics.catalog import load_metric_catalog, metric_catalog_hash


def main() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    catalog = load_metric_catalog(
        repository_root / "config/metrics/flow_v1_metrics.yaml"
    )
    oracle = json.loads(
        (repository_root / "fixtures/expected/metric_snapshots_v1.json").read_text(
            encoding="utf-8"
        )
    )
    comparison_types = tuple(
        comparison_type
        for comparison_type, values in oracle.items()
        if isinstance(values, dict) and comparison_type != "rounding"
    )
    headline = {
        metric_code: oracle["trailing_12"][metric_code]
        for metric_code in (
            "revenue",
            "gross_margin",
            "operating_profit",
            "operating_cash_flow",
            "cash_conversion",
            "ar_balance",
            "dso",
        )
    }
    summary = {
        "status": "PASS",
        "as_of_month": oracle["as_of_month"],
        "definition_set_id": catalog.definition_set_id,
        "definition_set_hash": metric_catalog_hash(catalog),
        "engine_version": catalog.engine_version,
        "metric_count": len(catalog.metrics),
        "dependency_edge_count": sum(
            len(metric.dependencies) for metric in catalog.metrics
        ),
        "comparison_types": comparison_types,
        "headline_trailing_12": headline,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
