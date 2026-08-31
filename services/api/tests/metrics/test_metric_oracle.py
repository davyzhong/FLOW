from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
ORACLE_PATH = REPOSITORY_ROOT / "fixtures/expected/metric_snapshots_v1.json"


def _assert_no_float(value: Any) -> None:
    assert not isinstance(value, float)
    if isinstance(value, dict):
        for child in value.values():
            _assert_no_float(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_float(child)


def test_metric_oracle_is_committed_and_uses_decimal_strings() -> None:
    assert ORACLE_PATH.is_file(), "metric snapshot oracle is not committed"
    payload = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))

    assert payload["definition_set_id"] == "flow.metrics.logistics.v1"
    assert payload["as_of_month"] == "2026-08"
    assert payload["rounding"] == {"amount": 4, "quantity": 4, "ratio": 6, "day": 6}
    assert set(payload["actual_ytd"]) == {
        "ar_balance",
        "cash_conversion",
        "collection_rate",
        "cost_per_order",
        "direct_cost",
        "dso",
        "fulfilled_units",
        "fulfillment_cost_rate",
        "gross_margin",
        "gross_profit",
        "operating_cash_flow",
        "operating_profit",
        "orders",
        "revenue",
        "revenue_per_order",
    }
    _assert_no_float(payload)
    assert hashlib.sha256(ORACLE_PATH.read_bytes()).hexdigest() == (
        "86447cee7249d9f1d8fa4a31253bd35cd53307888f97916e0d6711c91657e6b8"
    )
