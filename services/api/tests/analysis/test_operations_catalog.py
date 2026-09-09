"""经营轨主题目录测试（O1，D050/OP 方法论）。

- 六主题板块按 OP-4 信息架构注册（先总体后细分 board_slot 递增）；
- metric_refs 全部在指标字典登记，不得另建第二套口径；
- 数据可得性分层是第一原则：L2/L3 主题不得挂财报 facts 口径，
  财报期可用层下返回 not_applicable + typed 原因，不返回 0；
- 业务事件簿为一等公民合同：常规/增量投入分账规则必带。
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from flow_api.analysis.operations_catalog import (
    load_operations_catalog,
    theme_availability,
    validate_metric_refs,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
CATALOG_PATH = REPO_ROOT / "config/operations/operations_track_v1.yaml"
DICTIONARY_PATH = REPO_ROOT / "config/metrics/metric_dictionary_v1.yaml"

SIX_THEMES = {
    "growth_quality",
    "revenue_structure",
    "cost_structure",
    "profit_quality",
    "users_channels",
    "operational_efficiency",
}


def _catalog():
    return load_operations_catalog(CATALOG_PATH)


def _registered_codes() -> set[str]:
    data = yaml.safe_load(DICTIONARY_PATH.read_text(encoding="utf-8"))
    codes: set[str] = set()
    for group_key in ("metrics_general", "metrics_logistics"):
        for item in data.get(group_key, []):
            codes.add(item["metric_code"])
    return codes


def test_catalog_loads_with_six_board_themes_in_overall_first_order() -> None:
    catalog = _catalog()
    assert catalog.catalog_id == "flow.analysis.operations_track.v1"
    assert catalog.decision_ref == "D050"
    assert {t.theme_id for t in catalog.themes} == SIX_THEMES
    slots = [t.board_slot for t in sorted(catalog.themes, key=lambda t: t.board_slot)]
    assert slots == sorted(slots) and len(set(slots)) == len(slots), "board_slot 唯一且递增"
    # 总体结果指标板块在前、解释性板块在后（OP-4：核心指标在前解释指标在后）
    first = min(catalog.themes, key=lambda t: t.board_slot)
    assert first.theme_id == "growth_quality"


def test_metric_refs_all_registered_in_dictionary() -> None:
    catalog = _catalog()
    unknown = validate_metric_refs(catalog, _registered_codes())
    assert unknown == [], f"经营轨不得引用未登记口径: {unknown}"


def test_duplicate_theme_id_rejected(tmp_path: Path) -> None:
    data = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    data["themes"].append(dict(data["themes"][0]))
    dup_path = tmp_path / "dup.yaml"
    dup_path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValidationError, match="theme_id"):
        load_operations_catalog(dup_path)


def test_invalid_availability_rejected(tmp_path: Path) -> None:
    data = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    data["themes"][0]["availability"] = "whenever_we_feel_like"
    bad_path = tmp_path / "bad.yaml"
    bad_path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_operations_catalog(bad_path)


def test_internal_only_theme_may_not_reference_financial_formula() -> None:
    catalog = _catalog()
    users = next(t for t in catalog.themes if t.theme_id == "users_channels")
    assert users.availability in {"internal_process", "internal_events"}
    assert users.metric_refs == (), "L2+ 主题不得挂财报 facts 口径（无量价数据不生成量价桥）"


def test_theme_availability_returns_typed_not_applicable_for_missing_layers() -> None:
    catalog = _catalog()
    report_only = {"financial_report"}
    users = next(t for t in catalog.themes if t.theme_id == "users_channels")
    state = theme_availability(users, available_layers=report_only)
    assert state["status"] == "not_applicable"
    assert state["reason"] == "internal_data_required"

    growth = next(t for t in catalog.themes if t.theme_id == "growth_quality")
    state = theme_availability(growth, available_layers=report_only)
    assert state["status"] == "available"
    # L3 增强主题在全层可得时才可用
    state = theme_availability(growth, available_layers={"financial_report", "internal_events"})
    assert state["status"] == "available"


def test_event_book_contract_carries_separation_rule() -> None:
    catalog = _catalog()
    assert catalog.event_book.availability == "internal_events"
    joined = "\n".join(catalog.event_book.rules)
    assert "常规投入" in joined and "增量投入" in joined, "业务事件簿必须分账规则"
    field_names = {f.field_name for f in catalog.event_book.fields}
    assert {"event_type", "period", "incremental_spend"} <= field_names


def test_dupont_theme_must_carry_caliber_note() -> None:
    catalog = _catalog()
    profit = next(t for t in catalog.themes if t.theme_id == "profit_quality")
    assert "dupont" in profit.primitives
    assert profit.caliber_note, "杜邦引用必须携带口径标注（D01/U2-I12 纪律）"
    assert "净利润总额口径" in profit.caliber_note
