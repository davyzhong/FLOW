"""四层覆盖率测试（P02，订正 C11）：登记/可执行/源数据覆盖/展示启用 分开计数。"""

from __future__ import annotations

from flow_api.metric_library_store.coverage import four_layer_coverage


def test_layers_are_counted_separately_with_entailment() -> None:
    report = four_layer_coverage(
        registered_codes={"a", "b", "c", "d", "e"},
        executable_codes={"a", "b", "d"},
        source_covered_codes={"a", "b"},  # d 可执行但源数据未覆盖
        display_enabled_codes={"a"},  # 仅 a 走通全部四层
    )
    assert report.summary == {
        "registered": 5, "executable": 3, "source_covered": 2, "display_enabled": 1,
        "total": 5,
    }
    by_code = {row.metric_code: row for row in report.rows}
    assert by_code["d"].executable and not by_code["d"].source_covered
    assert by_code["c"].registered and not by_code["c"].executable
    assert by_code["a"].display_enabled


def test_display_enabled_without_registration_is_clamped_down() -> None:
    """展示启用但未登记：按低层截断，不虚报高层。"""

    report = four_layer_coverage(
        registered_codes=set(),
        executable_codes=set(),
        source_covered_codes={"x"},
        display_enabled_codes={"x"},
    )
    row = report.rows[0]
    assert not row.registered and not row.executable
    assert not row.source_covered and not row.display_enabled
    assert report.summary["display_enabled"] == 0


def test_summary_not_flat() -> None:
    """禁止只有总数：summary 必须分列四层。"""

    report = four_layer_coverage(set(), set(), set(), set())
    assert report.summary["total"] == 0
    assert set(report.summary) == {
        "registered", "executable", "source_covered", "display_enabled", "total",
    }
