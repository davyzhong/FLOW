from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from flow_api.data_contract.contract import load_contract
from flow_api.intake.transforms import TransformError, apply_transform, load_transform_rules

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONTRACT = load_contract(REPOSITORY_ROOT / "templates/excel/flow_v1_contract.yaml")
RULES = load_transform_rules(REPOSITORY_ROOT / "config/intake/flow_v1_transforms.yaml")


@pytest.mark.parametrize(
    ("sheet_id", "field_id", "raw", "expected", "rule_id"),
    [
        ("operating_actual", "month_key", "2026年08月", "2026-08", "normalize_month"),
        ("operating_actual", "month_key", "2026/08", "2026-08", "normalize_month"),
        (
            "operating_actual",
            "revenue",
            "1,234,567.8901",
            Decimal("1234567.8901"),
            "parse_decimal",
        ),
        ("customer_master", "credit_term_days", " 30 ", 30, "parse_integer"),
        ("customer_master", "customer_name", "  客户Ａ  ", "客户A", "normalize_text"),
        (
            "analysis_batch",
            "generated_at",
            "2026-08-30T00:00:00Z",
            datetime.fromisoformat("2026-08-30T00:00:00+00:00"),
            "parse_datetime",
        ),
        ("monthly_budget", "customer_segment_code", "  ", None, "normalize_null"),
    ],
)
def test_versioned_transform_rules_are_pure_and_typed(
    sheet_id: str, field_id: str, raw: object, expected: object, rule_id: str
) -> None:
    field = CONTRACT.get_sheet(sheet_id).get_field(field_id)
    result = apply_transform(RULES.for_field(field), field, raw)

    assert result.value == expected
    assert result.rule_id == rule_id
    assert result.rule_version == 1
    assert result.raw_value == raw
    assert result.status in {"unchanged", "transformed"}


def test_lossy_or_ambiguous_numeric_conversion_is_rejected() -> None:
    field = CONTRACT.get_sheet("operating_actual").get_field("revenue")

    with pytest.raises(TransformError, match="decimal"):
        apply_transform(RULES.for_field(field), field, "1.2万元")

    with pytest.raises(TransformError, match="scale"):
        apply_transform(RULES.for_field(field), field, "1.23456")
