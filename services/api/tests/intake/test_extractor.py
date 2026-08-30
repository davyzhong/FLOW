from __future__ import annotations

import hashlib
from decimal import Decimal
from pathlib import Path

from flow_api.data_contract.contract import load_contract
from flow_api.data_contract.semantic import compare_semantics
from flow_api.fixtures.generator import build_reference_package
from flow_api.intake.detector import profile_workbook
from flow_api.intake.extractor import ExtractedCandidate, extract_candidate_package
from flow_api.intake.mapping import load_aliases, propose_mapping
from flow_api.intake.transforms import load_transform_rules

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONTRACT = load_contract(REPOSITORY_ROOT / "templates/excel/flow_v1_contract.yaml")
ALIASES = load_aliases(REPOSITORY_ROOT / "config/intake/flow_v1_aliases.yaml")
RULES = load_transform_rules(REPOSITORY_ROOT / "config/intake/flow_v1_transforms.yaml")
STANDARD = REPOSITORY_ROOT / "fixtures/workbooks/flow_standard_v1.xlsx"
NONSTANDARD = REPOSITORY_ROOT / "fixtures/workbooks/external_logistics_nonstandard_v1.xlsx"


def _extract(path: Path) -> ExtractedCandidate:
    profile = profile_workbook(path)
    mapping = propose_mapping(profile, CONTRACT, ALIASES)
    return extract_candidate_package(path, profile, mapping, CONTRACT, RULES)


def test_standard_and_nonstandard_sources_produce_identical_canonical_semantics() -> None:
    expected = build_reference_package()
    standard = _extract(STANDARD)
    external = _extract(NONSTANDARD)

    assert compare_semantics(expected, standard.package) == ()
    assert compare_semantics(expected, external.package) == ()
    assert compare_semantics(standard.package, external.package) == ()


def test_external_extraction_retains_cell_level_before_after_lineage() -> None:
    extracted = _extract(NONSTANDARD)

    month = next(
        item
        for item in extracted.lineage
        if item.source_sheet == "业务明细"
        and item.source_row == 4
        and item.target_field_id == "month_key"
    )
    assert month.source_column == "L"
    assert month.raw_value == "2024年09月"
    assert month.transformed_value == "2024-09"
    assert month.rule_id == "normalize_month"
    assert month.status == "transformed"

    comma_amount = next(
        item
        for item in extracted.lineage
        if item.target_field_id == "revenue"
        and isinstance(item.raw_value, str)
        and "," in item.raw_value
    )
    assert isinstance(comma_amount.transformed_value, Decimal)
    assert comma_amount.rule_id == "parse_decimal"
    assert comma_amount.status == "transformed"


def test_extraction_does_not_change_source_bytes() -> None:
    before = hashlib.sha256(NONSTANDARD.read_bytes()).hexdigest()

    extracted = _extract(NONSTANDARD)

    assert extracted.source_sha256 == before
    assert hashlib.sha256(NONSTANDARD.read_bytes()).hexdigest() == before
    assert extracted.failed_lineage == ()
