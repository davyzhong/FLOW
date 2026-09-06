from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter

from flow_api.api.schemas.metric_library import (
    AccountingFoundation,
    MetricEntry,
    MetricLibraryResponse,
    ReportItem,
)

router = APIRouter(prefix="/metric-library", tags=["metric-library"])

METRIC_LIBRARY_PATHS = (
    Path("config/metrics/metric_dictionary_v0.yaml"),
    Path("config/metrics/accounting_foundation_v0.yaml"),
)


def resolve_metric_library_root(module_path: Path = Path(__file__)) -> Path:
    resolved_module_path = module_path.resolve()
    candidates = (resolved_module_path.parent, *resolved_module_path.parents)
    for candidate in candidates:
        if all((candidate / relative_path).is_file() for relative_path in METRIC_LIBRARY_PATHS):
            return candidate
    raise RuntimeError(f"FLOW metric library datasets not found from {resolved_module_path}")


@lru_cache
def load_metric_library() -> MetricLibraryResponse:
    root = resolve_metric_library_root()
    dictionary: dict[str, Any] = yaml.safe_load((root / METRIC_LIBRARY_PATHS[0]).read_text())
    foundation: dict[str, Any] = yaml.safe_load((root / METRIC_LIBRARY_PATHS[1]).read_text())

    metrics = [
        MetricEntry(collection="general", **entry) for entry in dictionary["metrics_general"]
    ] + [
        MetricEntry(collection="logistics", **entry) for entry in dictionary["metrics_logistics"]
    ]
    return MetricLibraryResponse(
        dictionary_id=dictionary["dictionary_id"],
        status=dictionary["status"],
        decision_ref=dictionary["decision_ref"],
        created=str(dictionary["created"]),
        standards_scope=list(dictionary["standards_scope"]),
        domains=dict(dictionary["domains"]),
        report_items=[
            ReportItem(item_id=item_id, **names)
            for item_id, names in dictionary["report_items"].items()
        ],
        metrics=metrics,
        relations=dictionary["relations"],
        accounting=AccountingFoundation(**foundation),
    )


@router.get("", response_model=MetricLibraryResponse)
def get_metric_library() -> MetricLibraryResponse:
    """只读返回指标库与会计基础数据集（v0 草案，D040）。"""
    return load_metric_library()


__all__ = ["load_metric_library", "router"]
