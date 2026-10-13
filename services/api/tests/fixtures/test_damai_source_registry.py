"""大麦演示来源事实登记门禁（路线图队首子步骤：机器可读来源登记）。

校验四件事：
1. 登记结构完整：逐条事实有来源、页锚、单位、期间；fact_id 唯一；
2. 原件血缘真实：登记 SHA 与本地原件一致，页锚文本在物理页在场；
3. 关键披露值正确：与审计记录中的原件值逐条相等（防抽取/登记漂移）；
4. 无来源假设全部有处置：现行合成参数（利息 65%、折旧 10%、负债/现金流拆分）
   必须在 unavailable 有登记条目，不得存在未登记假设。
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
REGISTRY_PATH = REPOSITORY_ROOT / "config/damai/source_facts_v1.yaml"
BUILDER_PATH = REPOSITORY_ROOT / "scripts/build_damai_source_registry.py"
PDF_CNAIAO = (
    REPOSITORY_ROOT
    / "docs/knowledge-base/02_research/original/p5_samples/cainiao_private"
    / "Cainiao_application_proof_20230926.pdf"
)

REQUIRED_UNAVAILABLE_IDS = (
    "U-CN-FY2026-STANDALONE",
    "U-CN-FY2024PLUS-FULL-STATEMENTS",
    "U-CN-VOLUME-FINE-GRAINS",
    "U-DM-INTEREST-SPLIT",
    "U-DM-DEPRECIATION-ESTIMATE",
    "U-DM-DEBT-AP-COMPOSITION",
    "U-DM-CASHFLOW-SPLIT",
)

# 与审计记录（2026-10-12 来源基线审计）一致的原件关键值
ANCHOR_VALUES: tuple[tuple[str, str, object, object], ...] = (
    ("合并利润表", "FY2023", "收入", 77799675),
    ("合并利润表", "FY2023", "毛利", 8146656),
    ("合并利润表", "FY2022", "收入", 66866916),
    ("合并利润表", "FY2021", "收入", 52732812),
    ("合并资产负债表", "FY2023", "资产总计", 71850931),
    ("合并资产负债表", "FY2023", "权益及负债总额", 71850931),
    ("合并现金流量表", "FY2023", "年末现金及现金等价物", 8784404),
)


def _load_registry() -> dict:
    return yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_damai_source_registry", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_registry_schema_and_provenance_complete() -> None:
    registry = _load_registry()
    assert registry["registry_id"] == "flow.damai_source_facts.v1"
    assert set(registry["layers"]) == {
        "disclosed_fact",
        "derived_value",
        "demo_detail",
        "test_fixture",
    }
    fact_ids = [fact["fact_id"] for fact in registry["facts"]]
    assert len(fact_ids) == len(set(fact_ids)), "fact_id 必须唯一"
    for fact in registry["facts"]:
        assert fact["source"] in registry["sources"], fact["fact_id"]
        assert fact["layer"] == "disclosed_fact"
        assert fact["value"] is not None
        assert fact["unit"]
        assert fact["period"]
    for unavailable in registry["unavailable"]:
        assert unavailable["reason"], unavailable["unavailable_id"]


def test_source_pdf_sha_matches_local_original() -> None:
    registry = _load_registry()
    source = registry["sources"]["CNAI-IPO-2023"]
    assert source["sha256"] == hashlib.sha256(PDF_CNAIAO.read_bytes()).hexdigest()
    assert source["pages_total"] > 600
    for name, page in source["statement_pages"].items():
        assert page > 400, f"{name} 页锚异常"
    anchors = source["text_anchor_pages"]
    assert all(entry["anchor_verified"] for entry in anchors.values())


@pytest.mark.parametrize(("statement", "period", "item", "expected"), ANCHOR_VALUES)
def test_anchor_disclosed_values_match_audit(
    statement: str, period: str, item: str, expected: object
) -> None:
    registry = _load_registry()
    matches = [
        fact
        for fact in registry["facts"]
        if fact["statement"] == statement
        and fact["period"] == period
        and fact["item_zh"] == item
    ]
    assert len(matches) == 1, f"{statement}/{period}/{item} 应恰好登记一条"
    assert matches[0]["value"] == expected
    assert matches[0]["page"]["physical"] > 0


def test_segment_and_volume_anchor_values() -> None:
    by_id = {fact["fact_id"]: fact for fact in _load_registry()["facts"]}
    assert by_id["CN-SEG-FY2025-SEGMENT_REVENUE"]["value"] == 101272
    assert by_id["CN-SEG-FY2025-ADJUSTED_EBITA"]["value"] == 302
    assert by_id["CN-SEG-FY2024-SEGMENT_REVENUE"]["value"] == 99020
    assert by_id["CN-OPS-FY2023-INTERNATIONAL_PARCELS"]["value"] == 1519
    assert by_id["CN-OPS-FY2023-CHINA_ORDERS_FULFILLED"]["value"] == 2311
    assert by_id["CN-OPS-FY2023-INTERNATIONAL_PARCELS"]["page_verification"] == "verified"


def test_no_source_assumptions_all_have_disposition() -> None:
    unavailable_ids = {entry["unavailable_id"] for entry in _load_registry()["unavailable"]}
    missing = set(REQUIRED_UNAVAILABLE_IDS) - unavailable_ids
    assert not missing, f"无来源假设缺少处置登记：{sorted(missing)}"


def test_demo_layers_and_fixtures_declared() -> None:
    registry = _load_registry()
    assert registry["demo_layers"], "演示明细层必须显式登记"
    for layer in registry["demo_layers"]:
        assert layer["layer"] == "demo_detail"
        assert layer["reconciliation"]
    assert registry["test_fixtures"], "测试建制必须显式登记"


def test_registry_matches_deterministic_rebuild() -> None:
    builder = _load_builder()
    texts = builder.pdf_page_texts(PDF_CNAIAO)
    assert builder._dump(builder.build_registry(texts)) == REGISTRY_PATH.read_text(
        encoding="utf-8"
    ), "登记与确定性重建不一致：请运行 scripts/build_damai_source_registry.py 重新生成"
