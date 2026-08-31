from __future__ import annotations

import json
from pathlib import Path

from flow_api.data_contract.contract import load_contract
from flow_api.data_contract.workbook import render_workbook, workbook_semantic_fingerprint
from flow_api.fixtures.generator import build_reference_package, write_canonical_package
from flow_api.fixtures.known_answers import write_known_answers

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_PATH = REPOSITORY_ROOT / "templates/excel/flow_v1_contract.yaml"
COMMITTED_CANONICAL = REPOSITORY_ROOT / "fixtures/canonical"
COMMITTED_ANSWERS = REPOSITORY_ROOT / "fixtures/expected/known_answers.json"
COMMITTED_METRIC_ORACLE = REPOSITORY_ROOT / "fixtures/expected/metric_snapshots_v1.json"
COMMITTED_WORKBOOK = REPOSITORY_ROOT / "fixtures/workbooks/flow_standard_v1.xlsx"
CONTRACT_DOCUMENTATION = REPOSITORY_ROOT / "docs/data-contract/flow-v1.md"


def test_committed_phase_two_artifacts_regenerate_semantically(tmp_path: Path) -> None:
    contract = load_contract(CONTRACT_PATH)
    package = build_reference_package()
    generated_canonical = tmp_path / "canonical"
    generated_answers = tmp_path / "known_answers.json"
    generated_workbook = tmp_path / "flow_standard_v1.xlsx"

    write_canonical_package(package, generated_canonical)
    write_known_answers(package, generated_answers)
    render_workbook(contract, package, generated_workbook)

    committed_files = sorted(path.name for path in COMMITTED_CANONICAL.iterdir())
    generated_files = sorted(path.name for path in generated_canonical.iterdir())
    assert committed_files == generated_files
    for filename in committed_files:
        assert (COMMITTED_CANONICAL / filename).read_bytes() == (
            generated_canonical / filename
        ).read_bytes()
    assert COMMITTED_ANSWERS.read_bytes() == generated_answers.read_bytes()
    assert workbook_semantic_fingerprint(COMMITTED_WORKBOOK) == workbook_semantic_fingerprint(
        generated_workbook
    )


def test_documentation_covers_every_sheet_grain_and_boundary() -> None:
    contract = load_contract(CONTRACT_PATH)
    documentation = CONTRACT_DOCUMENTATION.read_text(encoding="utf-8")

    for sheet in contract.sheets:
        assert sheet.sheet_name in documentation
        assert sheet.sheet_id in documentation
        for field_id in sheet.grain:
            assert f"`{field_id}`" in documentation
    for required_term in (
        "flow.excel.v1",
        "稳定字段 ID",
        "数据中间层",
        "阻断错误",
        "确认警告",
        "空值",
        "经营财务对账",
        "Phase 3",
        "make test-data-contract",
    ):
        assert required_term in documentation


def test_manifest_counts_match_known_answers() -> None:
    manifest = json.loads((COMMITTED_CANONICAL / "manifest.json").read_text())
    known_answers = json.loads(COMMITTED_ANSWERS.read_text())

    assert manifest["contract_version"] == "flow.excel.v1"
    assert (
        manifest["files"]["operating_actuals.jsonl"]["row_count"]
        == known_answers["row_counts"]["operating_actuals"]
    )
    assert (
        manifest["files"]["financial_actuals.jsonl"]["row_count"]
        == known_answers["row_counts"]["financial_actuals"]
    )


def test_metric_oracle_is_anchored_to_phase_two_known_answers() -> None:
    known_answers = json.loads(COMMITTED_ANSWERS.read_text())
    metric_oracle = json.loads(COMMITTED_METRIC_ORACLE.read_text())

    assert metric_oracle["as_of_month"] == known_answers["windows"]["analysis"][1]
    assert (
        metric_oracle["trailing_12"]["revenue"]
        == known_answers["headline_totals"]["analysis"]["revenue"]
    )
    assert (
        metric_oracle["trailing_12"]["gross_margin"]
        == known_answers["headline_totals"]["analysis"]["gross_margin"]
    )
    assert (
        metric_oracle["trailing_12"]["operating_cash_flow"]
        == known_answers["headline_totals"]["analysis"]["operating_cash_flow"]
    )
    assert (
        metric_oracle["actual_month"]["ar_balance"]
        == known_answers["final_month_ar"]["receivable_balance"]
    )
