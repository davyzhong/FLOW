from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from flow_api.data_contract.contract import load_contract
from flow_api.data_contract.parser import parse_workbook
from flow_api.data_contract.semantic import compare_semantics, semantic_snapshot
from flow_api.data_contract.workbook import render_workbook
from flow_api.fixtures.generator import build_reference_package

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONTRACT = load_contract(REPOSITORY_ROOT / "templates/excel/flow_v1_contract.yaml")


def test_package_workbook_package_has_zero_semantic_difference(tmp_path: Path) -> None:
    source = build_reference_package()
    workbook = tmp_path / "round-trip.xlsx"

    render_workbook(CONTRACT, source, workbook)
    parsed = parse_workbook(workbook, CONTRACT)

    assert semantic_snapshot(parsed) == semantic_snapshot(source)
    assert compare_semantics(source, parsed) == ()


def test_semantic_snapshot_preserves_zero_null_decimal_and_unicode() -> None:
    package = build_reference_package()
    snapshot = semantic_snapshot(package)

    budget_rows = snapshot["monthly_budgets"]
    assert any(row["customer_segment_code"] is None for row in budget_rows)
    assert all(isinstance(row["amount"], str) and "." in row["amount"] for row in budget_rows)
    assert snapshot["organizations"][0]["name"]
    assert "集团" in " ".join(row["name"] for row in snapshot["organizations"])


def test_semantic_comparison_reports_precise_paths() -> None:
    source = build_reference_package()
    changed_row = source.operating_actuals[0].model_copy(
        update={"revenue": source.operating_actuals[0].revenue + Decimal("1.0000")}
    )
    changed = source.model_copy(
        update={"operating_actuals": (changed_row,) + source.operating_actuals[1:]}
    )

    differences = compare_semantics(source, changed)

    assert len(differences) == 1
    assert "operating_actuals" in differences[0]
    assert "revenue" in differences[0]
