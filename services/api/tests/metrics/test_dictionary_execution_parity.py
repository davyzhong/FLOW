"""指标库统一身份与可执行定义（C02）测试。

- 55 项指标全部绑定执行器（引擎/事实 AST/叙述），无遗漏；
- 事实路径对等：同一指标同输入，脚本引擎与独立参照求值器结果一致；
- 覆盖清单与生成文档一致（覆盖清单即 docs 产物，不允许漂移）。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

from flow_api.metric_library_store.binding import (
    ExecutionKind,
    build_execution_binding,
    coverage_summary,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
FACTS_PATH = REPO_ROOT / "docs/implementation/p5/statement_facts.yaml"
COVERAGE_DOC = REPO_ROOT / "docs/implementation/objective-analysis/metric-execution-coverage.md"


def _load_script_engine():
    spec = importlib.util.spec_from_file_location(
        "p5_query_facts", REPO_ROOT / "scripts/p5_query_facts.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["p5_query_facts"] = module
    spec.loader.exec_module(module)
    return module


def _reference_eval(node, metrics, items):
    """独立参照求值器：与 scripts/p5_query_facts.py 不同实现路径。"""

    if isinstance(node, (int, float)):
        return float(node)
    if isinstance(node, str):
        if node.startswith(("bs.", "is.", "cf.", "mpm.")):
            return items[node]
        return _reference_eval(metrics[node]["formula"], metrics, items)
    op, args = node["op"], node["args"]
    if op == "identity":
        return _reference_eval(args[0], metrics, items)
    if op == "avg":
        return (items[f"{args[0]}@end"] + items[f"{args[0]}@open"]) / 2
    if op == "prior":
        return items[f"{args[0]}@prior"]
    values = [_reference_eval(a, metrics, items) for a in args]
    if op == "div":
        return values[0] / values[1]
    if op == "sub":
        return values[0] - values[1]
    if op == "add":
        return sum(values)
    if op == "mul":
        result = 1.0
        for value in values:
            result *= value
        return result
    raise ValueError(op)


def test_all_55_metrics_bound() -> None:
    bindings = build_execution_binding()
    assert len(bindings) == 55
    summary = coverage_summary(bindings)
    assert summary["engine"] == 15
    assert summary["facts"] + summary["engine"] + summary["narrative"] == 55
    narrative = [b for b in bindings if b.kind == ExecutionKind.NARRATIVE]
    for binding in narrative:
        assert binding.reason, "叙述定义必须如实给出缺失原因"


def test_coverage_doc_in_sync() -> None:
    bindings = build_execution_binding()
    doc = COVERAGE_DOC.read_text()
    summary = coverage_summary(bindings)
    assert f"facts（事实 AST）：{summary['facts']}" in doc
    for binding in bindings:
        assert binding.metric_code in doc, f"覆盖清单缺少 {binding.metric_code}"


def test_facts_engine_parity_on_sf() -> None:
    module = _load_script_engine()
    facts_doc = yaml.safe_load(FACTS_PATH.read_text())
    dictionary = yaml.safe_load(
        (REPO_ROOT / "config/metrics/metric_dictionary_v1.yaml").read_text()
    )
    engine = module.Engine(facts_doc, dictionary)

    company, period = "sf_002352", "2026Q1"
    for code in ("gross_margin", "debt_asset_ratio", "current_ratio"):
        via_engine = engine.ev_metric(code, company, period)
        metrics = {m["metric_code"]: m for m in dictionary["metrics_general"]}
        # 独立参照路径：按引擎同一默认角色规则装配（bs.*→end，其余→cur）
        items: dict[str, float] = {}
        for fact in facts_doc["facts"]:
            if fact["company"] != company or fact["period"] != period:
                continue
            default_role = "end" if fact["item_id"].startswith("bs.") else "cur"
            if fact["role"] == default_role:
                items[fact["item_id"]] = float(fact["value"])
            items[f"{fact['item_id']}@{fact['role']}"] = float(fact["value"])
        # prior 角色：bs.* 用 open，其余用 prev_yoy（与引擎一致）
        for key in list(items):
            if "@" in key:
                continue
            if key.startswith("bs."):
                items[f"{key}@prior"] = items.get(f"{key}@open", items[key])
            else:
                items[f"{key}@prior"] = items.get(f"{key}@prev_yoy", items[key])
        reference = _reference_eval(metrics[code]["formula"], metrics, items)
        assert abs(via_engine - reference) < 1e-9, f"{code} 双路径不一致"
        assert via_engine is not None
