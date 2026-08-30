from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from flow_api.data_contract.contract import load_contract
from flow_api.fixtures.generator import build_reference_package
from flow_api.intake.detector import profile_workbook
from flow_api.intake.mapping import MappingProposal, load_aliases, propose_mapping
from flow_api.intake.quality import evaluate_quality

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONTRACT = load_contract(REPOSITORY_ROOT / "templates/excel/flow_v1_contract.yaml")
ALIASES = load_aliases(REPOSITORY_ROOT / "config/intake/flow_v1_aliases.yaml")
NONSTANDARD = REPOSITORY_ROOT / "fixtures/workbooks/external_logistics_nonstandard_v1.xlsx"


def _proposal() -> MappingProposal:
    return propose_mapping(profile_workbook(NONSTANDARD), CONTRACT, ALIASES)


def test_reference_package_has_no_blocking_quality_or_reconciliation_issue() -> None:
    report = evaluate_quality(build_reference_package(), CONTRACT, _proposal())

    assert report.blocking_issues == ()
    assert report.publishable
    assert all(issue.code != "reconciliation_outside_tolerance" for issue in report.issues)


def test_missing_required_mapping_duplicate_grain_and_broken_relation_block() -> None:
    proposal = _proposal()
    operating_mapping = proposal.get_sheet("operating_actual")
    proposal = replace(
        proposal,
        sheets=tuple(
            replace(sheet, unresolved_required_fields=("revenue",))
            if sheet.target_sheet_id == "operating_actual"
            else sheet
            for sheet in proposal.sheets
        ),
    )
    package = build_reference_package()
    first = package.operating_actuals[0]
    broken = first.model_copy(update={"customer_code": "UNKNOWN_CUSTOMER"})
    package = package.model_copy(
        update={"operating_actuals": (broken,) + package.operating_actuals[1:] + (broken,)}
    )

    report = evaluate_quality(package, CONTRACT, proposal)
    codes = {issue.code for issue in report.blocking_issues}

    assert "missing_required_mapping" in codes
    assert "duplicate_grain" in codes
    assert "broken_required_relation" in codes
    assert not report.publishable
    assert operating_mapping.target_sheet_id == "operating_actual"


def test_business_anomalies_and_low_confidence_mapping_are_confirmable_warnings() -> None:
    proposal = _proposal()
    operating = proposal.get_sheet("operating_actual")
    assert operating.get_field("revenue").confidence == "high"
    proposal = replace(
        proposal,
        sheets=tuple(
            replace(
                sheet,
                fields=tuple(
                    replace(
                        field,
                        confidence="low",
                        score=0.55,
                        requires_confirmation=True,
                    )
                    if field.target_field_id == "revenue"
                    else field
                    for field in sheet.fields
                ),
            )
            if sheet.target_sheet_id == "operating_actual"
            else sheet
            for sheet in proposal.sheets
        ),
    )
    package = build_reference_package()
    first = package.operating_actuals[0].model_copy(
        update={"order_count": Decimal("0.0000"), "revenue": Decimal("-1.0000")}
    )
    package = package.model_copy(
        update={"operating_actuals": (first,) + package.operating_actuals[1:]}
    )

    report = evaluate_quality(package, CONTRACT, proposal)
    warning_codes = {issue.code for issue in report.warning_issues}

    assert "low_confidence_mapping" in warning_codes
    assert "unexpected_negative" in warning_codes
    assert "revenue_without_orders" in warning_codes
    assert all(issue.repair_suggestion for issue in report.issues)


def test_quality_issue_order_is_deterministic() -> None:
    first = evaluate_quality(build_reference_package(), CONTRACT, _proposal())
    second = evaluate_quality(build_reference_package(), CONTRACT, _proposal())

    assert first == second
