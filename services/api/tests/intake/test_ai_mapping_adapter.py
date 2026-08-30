from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from flow_api.data_contract.contract import load_contract
from flow_api.intake.ai_mapping import (
    AIMappingSuggestion,
    InvalidAISuggestionError,
    apply_ai_suggestions,
)
from flow_api.intake.detector import profile_workbook
from flow_api.intake.mapping import load_aliases, propose_mapping

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONTRACT = load_contract(REPOSITORY_ROOT / "templates/excel/flow_v1_contract.yaml")
ALIASES = load_aliases(REPOSITORY_ROOT / "config/intake/flow_v1_aliases.yaml")
NONSTANDARD = REPOSITORY_ROOT / "fixtures/workbooks/external_logistics_nonstandard_v1.xlsx"


def test_ai_suggestion_can_only_fill_an_unresolved_contract_target() -> None:
    profile = profile_workbook(NONSTANDARD)
    proposal = propose_mapping(profile, CONTRACT, ALIASES)
    operating = proposal.get_sheet("operating_actual")
    without_revenue = replace(
        operating,
        fields=tuple(field for field in operating.fields if field.target_field_id != "revenue"),
        unresolved_required_fields=("revenue",),
    )
    proposal = replace(
        proposal,
        sheets=tuple(
            without_revenue if sheet.target_sheet_id == "operating_actual" else sheet
            for sheet in proposal.sheets
        ),
    )

    enriched = apply_ai_suggestions(
        proposal,
        profile,
        CONTRACT,
        (
            AIMappingSuggestion(
                source_sheet="业务明细",
                source_header="营业收入(元)",
                target_sheet_id="operating_actual",
                target_field_id="revenue",
                confidence=0.81,
                rationale="源字段名称与样例值符合营业收入口径。",
            ),
        ),
    )

    revenue = enriched.get_sheet("operating_actual").get_field("revenue")
    assert revenue.method == "ai_suggestion"
    assert revenue.requires_confirmation
    assert revenue.score == 0.81


@pytest.mark.parametrize(
    ("target_sheet", "target_field", "source_header"),
    [
        ("operating_actual", "not_a_contract_field", "营业收入(元)"),
        ("not_a_contract_sheet", "revenue", "营业收入(元)"),
        ("operating_actual", "revenue", "不存在的源字段"),
    ],
)
def test_ai_cannot_invent_contract_or_source_identifiers(
    target_sheet: str, target_field: str, source_header: str
) -> None:
    profile = profile_workbook(NONSTANDARD)
    proposal = propose_mapping(profile, CONTRACT, ALIASES)

    with pytest.raises(InvalidAISuggestionError):
        apply_ai_suggestions(
            proposal,
            profile,
            CONTRACT,
            (
                AIMappingSuggestion(
                    source_sheet="业务明细",
                    source_header=source_header,
                    target_sheet_id=target_sheet,
                    target_field_id=target_field,
                    confidence=0.8,
                    rationale="proposal",
                ),
            ),
        )
