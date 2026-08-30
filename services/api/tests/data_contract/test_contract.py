from pathlib import Path

import pytest
from pydantic import ValidationError

from flow_api.data_contract.contract import load_contract
from flow_api.data_contract.models import FieldContract, SheetContract, WorkbookContract

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_PATH = REPOSITORY_ROOT / "templates/excel/flow_v1_contract.yaml"

EXPECTED_SHEETS = (
    "00_填写说明",
    "01_分析批次",
    "02_经营实际",
    "03_财务实际",
    "04_月度预算",
    "05_应收回款",
    "06_客户主数据",
    "07_物流产品",
    "08_组织与区域",
    "09_管理科目",
)


def test_flow_v1_contract_has_exact_core_sheets() -> None:
    contract = load_contract(CONTRACT_PATH)

    assert contract.contract_version == "flow.excel.v1"
    assert tuple(sheet.sheet_name for sheet in contract.sheets) == EXPECTED_SHEETS
    assert contract.get_sheet("operating_actual").sheet_name == "02_经营实际"


def test_fields_are_stable_unique_and_well_formed() -> None:
    contract = load_contract(CONTRACT_PATH)

    for sheet in contract.sheets:
        field_ids = [field.field_id for field in sheet.fields]
        assert len(field_ids) == len(set(field_ids))
        assert all(field_id.isidentifier() and field_id.islower() for field_id in field_ids)
        assert set(sheet.grain).issubset(field_ids)
        for field in sheet.fields:
            assert field.description
            assert not (field.required and field.nullable)


def test_fact_contracts_cover_phase_one_canonical_values() -> None:
    contract = load_contract(CONTRACT_PATH)

    expected_values = {
        "operating_actual": {
            "order_count",
            "shipment_count",
            "revenue",
            "warehousing_cost",
            "transportation_cost",
            "other_direct_cost",
        },
        "financial_actual": {"amount"},
        "monthly_budget": {"metric_code", "amount"},
        "ar_collection": {
            "receivable_balance",
            "due_amount",
            "overdue_amount",
            "collected_amount",
        },
    }

    for sheet_id, field_ids in expected_values.items():
        sheet = contract.get_sheet(sheet_id)
        assert field_ids.issubset({field.field_id for field in sheet.fields})
        assert sheet.grain


def test_foreign_keys_reference_existing_fields() -> None:
    contract = load_contract(CONTRACT_PATH)
    targets = {
        (sheet.sheet_id, field.field_id)
        for sheet in contract.sheets
        for field in sheet.fields
    }

    for sheet in contract.sheets:
        for field in sheet.fields:
            if field.foreign_key is not None:
                assert (field.foreign_key.sheet_id, field.foreign_key.field_id) in targets


def test_decimal_fields_declare_unit_and_scale() -> None:
    contract = load_contract(CONTRACT_PATH)

    decimal_fields = [
        field
        for sheet in contract.sheets
        for field in sheet.fields
        if field.data_type == "decimal"
    ]
    assert decimal_fields
    assert all(field.unit for field in decimal_fields)
    assert all(field.scale is not None for field in decimal_fields)


def test_models_reject_required_nullable_and_duplicate_identifiers() -> None:
    with pytest.raises(ValidationError):
        FieldContract(
            field_id="amount",
            display_name="金额",
            data_type="decimal",
            required=True,
            nullable=True,
            description="非法字段",
            unit="CNY",
            scale=4,
        )

    field = FieldContract(
        field_id="code",
        display_name="编码",
        data_type="string",
        required=True,
        nullable=False,
        description="稳定编码",
    )
    sheet = SheetContract(
        sheet_id="example",
        sheet_name="示例",
        purpose="测试",
        fields=(field,),
        grain=("code",),
    )
    with pytest.raises(ValidationError):
        WorkbookContract(
            contract_version="flow.excel.v1",
            workbook_name="重复工作表",
            sheets=(sheet, sheet),
        )
