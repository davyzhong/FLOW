"""统一指标身份与可执行定义绑定（C02）。

把指标库 v1 的 55 个指标绑定到执行器：
- engine：迁移自 flow.metrics.logistics.v1 的 15 个物流指标，由指标引擎（库内目录）执行；
- facts：公式全部为受支持算子且引用的报表项目均已登记，由报表事实 AST 求值器执行；
- narrative：暂不支持执行（缺失取数或算子），如实记录原因。

绑定是叙述定义与可执行定义的唯一判定来源；不含执行数值。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml

DICTIONARY_PATH = Path("config/metrics/metric_dictionary_v1.yaml")
ALIAS_MAP_PATH = Path("config/statements/item_alias_map_v1.yaml")

SUPPORTED_OPS = {"identity", "avg", "prior", "div", "sub", "add", "mul", "sum"}


class ExecutionKind(StrEnum):
    ENGINE = "engine"
    FACTS = "facts"
    NARRATIVE = "narrative"


@dataclass(frozen=True, slots=True)
class MetricBinding:
    metric_code: str
    name: str
    collection: str
    kind: ExecutionKind
    executor: str | None
    reason: str | None


def _load(path: Path) -> dict[str, Any]:
    for root in (Path.cwd(), *Path.cwd().parents):
        full = root / path
        if full.is_file():
            data: dict[str, Any] = yaml.safe_load(full.read_text())
            return data
    raise FileNotFoundError(f"配置不存在：{path}")


def _formula_refs(node: Any) -> tuple[set[str], set[str]]:
    """返回（报表项目引用集合, 算子集合）。"""

    refs: set[str] = set()
    ops: set[str] = set()
    if isinstance(node, dict):
        op = node.get("op")
        if op:
            ops.add(str(op))
        for arg in node.get("args", []):
            sub_refs, sub_ops = _formula_refs(arg)
            refs |= sub_refs
            ops |= sub_ops
    elif isinstance(node, str) and node.startswith(("bs.", "is.", "cf.", "mpm.")):
        refs.add(node)
    return refs, ops


def _registered_item_ids(dictionary: dict[str, Any], alias_map: dict[str, Any]) -> set[str]:
    ids = set(dictionary.get("report_items", {}).keys())
    for company in alias_map.get("companies", {}).values():
        for section in (company.get("statements") or {}).values():
            for key, target in (section.get("map") or {}).items():
                if isinstance(target, str):
                    ids.add(target)
                elif isinstance(target, dict):
                    # {sum: [...]} 组合映射取合成 item_id；{item: x, abs: true} 取显式 item
                    explicit = target.get("item")
                    ids.add(str(explicit) if explicit else str(key).lstrip("_"))
    return ids


def build_execution_binding(
    dictionary_path: Path = DICTIONARY_PATH,
    alias_map_path: Path = ALIAS_MAP_PATH,
) -> list[MetricBinding]:
    dictionary = _load(dictionary_path)
    alias_map = _load(alias_map_path)
    item_ids = _registered_item_ids(dictionary, alias_map)

    bindings: list[MetricBinding] = []
    for collection, entries in (
        ("general", dictionary.get("metrics_general", [])),
        ("logistics", dictionary.get("metrics_logistics", [])),
    ):
        for entry in entries:
            code = entry["metric_code"]
            if str(entry.get("migrates_from", "")).startswith("flow.metrics.logistics.v1"):
                bindings.append(
                    MetricBinding(
                        metric_code=code,
                        name=entry["name"],
                        collection=collection,
                        kind=ExecutionKind.ENGINE,
                        executor="metrics 引擎（库内目录 metric_catalog_document）",
                        reason=None,
                    )
                )
                continue
            refs, ops = _formula_refs(entry.get("formula"))
            missing_items = sorted(refs - item_ids)
            unsupported_ops = sorted(ops - SUPPORTED_OPS)
            if not missing_items and not unsupported_ops:
                bindings.append(
                    MetricBinding(
                        metric_code=code,
                        name=entry["name"],
                        collection=collection,
                        kind=ExecutionKind.FACTS,
                        executor="报表事实 AST 求值器（extraction/normalization 链）",
                        reason=None,
                    )
                )
            else:
                reasons = []
                if missing_items:
                    reasons.append(f"取数项目未登记：{'、'.join(missing_items)}")
                if unsupported_ops:
                    reasons.append(f"算子暂不支持：{'、'.join(unsupported_ops)}")
                bindings.append(
                    MetricBinding(
                        metric_code=code,
                        name=entry["name"],
                        collection=collection,
                        kind=ExecutionKind.NARRATIVE,
                        executor=None,
                        reason="；".join(reasons),
                    )
                )
    return bindings


def coverage_summary(bindings: list[MetricBinding]) -> dict[str, int]:
    summary = {kind.value: 0 for kind in ExecutionKind}
    for binding in bindings:
        summary[binding.kind.value] += 1
    summary["total"] = len(bindings)
    return summary


__all__ = [
    "ExecutionKind",
    "MetricBinding",
    "SUPPORTED_OPS",
    "build_execution_binding",
    "coverage_summary",
]
