from __future__ import annotations

from pathlib import Path

from flow_api.data_contract.contract import load_contract
from flow_api.intake.detector import profile_workbook
from flow_api.intake.mapping import load_aliases, propose_mapping

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONTRACT = load_contract(REPOSITORY_ROOT / "templates/excel/flow_v1_contract.yaml")
ALIASES = load_aliases(REPOSITORY_ROOT / "config/intake/flow_v1_aliases.yaml")
STANDARD = REPOSITORY_ROOT / "fixtures/workbooks/flow_standard_v1.xlsx"
NONSTANDARD = REPOSITORY_ROOT / "fixtures/workbooks/external_logistics_nonstandard_v1.xlsx"


def test_standard_workbook_maps_by_stable_ids_without_confirmation() -> None:
    proposal = propose_mapping(profile_workbook(STANDARD), CONTRACT, ALIASES)

    operating = proposal.get_sheet("operating_actual")
    revenue = operating.get_field("revenue")
    assert operating.source_sheet == "02_经营实际"
    assert revenue.source_header == "营业收入"
    assert revenue.method == "stable_field_id"
    assert revenue.score == 1.0
    assert revenue.confidence == "high"
    assert not revenue.requires_confirmation
    assert not operating.unresolved_required_fields
    assert not proposal.unresolved_sheet_ids
    assert proposal.mapping_hash == propose_mapping(
        profile_workbook(STANDARD), CONTRACT, ALIASES
    ).mapping_hash


def test_nonstandard_workbook_maps_all_required_fields_by_registered_aliases() -> None:
    proposal = propose_mapping(profile_workbook(NONSTANDARD), CONTRACT, ALIASES)

    assert len(proposal.sheets) == 9
    assert proposal.unresolved_sheet_ids == ()
    assert all(not sheet.unresolved_required_fields for sheet in proposal.sheets)
    operating = proposal.get_sheet("operating_actual")
    customer = operating.get_field("customer_code")
    assert operating.source_sheet == "业务明细"
    assert customer.source_header == "客户编号"
    assert customer.method == "registered_alias"
    assert customer.confidence == "high"
    assert customer.rationale
    assert "数据备注" in operating.ignored_source_headers


def test_instruction_sheet_is_not_required_for_external_intake() -> None:
    proposal = propose_mapping(profile_workbook(NONSTANDARD), CONTRACT, ALIASES)

    assert "instructions" not in proposal.unresolved_sheet_ids
    assert all(sheet.target_sheet_id != "instructions" for sheet in proposal.sheets)
