"""O-01 语义上下文编译器单元测试：四元素映射、entry_id 透传与 codes 过滤。"""

from __future__ import annotations

from flow_api.api.schemas.metric_library import (
    AccountingFoundation,
    MetricEntry,
    MetricLibraryResponse,
    MetricRelation,
)
from flow_api.metrics.semantic_context import build_semantic_context


def _payload(*entries: MetricEntry) -> MetricLibraryResponse:
    return MetricLibraryResponse(
        dictionary_id="flow.metric_dictionary.v1",
        status="effective",
        decision_ref="D047",
        created="2026-09-05",
        standards_scope=["CAS", "IFRS"],
        domains={"profitability": "盈利能力"},
        report_items=[],
        metrics=list(entries),
        relations=[MetricRelation(relation="r", name="n", expression="e", note="nt")],
        accounting=AccountingFoundation(
            dataset_id="flow.accounting_foundation.v1",
            status="effective",
            accounts=[],
        ),
    )


def _entry(code: str, *, entry_id: str | None = None) -> MetricEntry:
    return MetricEntry(
        metric_code=code,
        name=code,
        collection="general",
        domain="profitability",
        definition=f"{code} 的定义。",
        formula_text="a ÷ b",
        formula={"op": "div", "args": ["a", "b"]},
        unit="%",
        caliber="口径说明。",
        benchmark="参考基准。",
        depends_on=["net_margin"],
        analysis_dimensions=["trend", "dupont"],
        alternative_calibers=["有息口径：…"],
        entry_id=entry_id,
    )


def test_four_element_mapping() -> None:
    context = build_semantic_context(_payload(_entry("roe", entry_id="entry-1")))
    assert context.metric_count == 1
    metric = context.metrics[0]
    assert metric.metric_code == "roe"
    assert metric.entry_id == "entry-1"
    assert metric.object.definition == "roe 的定义。"
    assert metric.dimensions == ["trend", "dupont"]
    assert metric.qualifications.caliber == "口径说明。"
    assert metric.qualifications.benchmark == "参考基准。"
    assert metric.qualifications.alternative_calibers == ["有息口径：…"]
    assert metric.value.formula_text == "a ÷ b"
    assert metric.value.unit == "%"
    assert metric.value.depends_on == ["net_margin"]


def test_yaml_only_entry_keeps_entry_id_empty_and_codes_filter() -> None:
    context = build_semantic_context(
        _payload(_entry("roe", entry_id=None), _entry("quick_ratio")),
        codes=["roe"],
    )
    assert context.metric_count == 1
    assert context.metrics[0].metric_code == "roe"
    assert context.metrics[0].entry_id is None
