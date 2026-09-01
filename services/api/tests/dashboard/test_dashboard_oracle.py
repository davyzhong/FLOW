from __future__ import annotations

import json
from pathlib import Path

from flow_api.fixtures.dashboard_known_answers import build_dashboard_known_answers

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
ORACLE_PATH = REPOSITORY_ROOT / "fixtures/expected/dashboard_overview_v1.json"


def test_committed_dashboard_oracle_matches_independent_inputs() -> None:
    committed = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
    calculated = build_dashboard_known_answers(REPOSITORY_ROOT)

    assert committed == calculated
    assert [card["metric_code"] for card in committed["metric_cards"]] == [
        "orders",
        "revenue",
        "revenue_per_order",
        "gross_margin",
        "fulfillment_cost_rate",
        "operating_profit",
        "ar_balance",
        "operating_cash_flow",
    ]
    assert committed["profit_bridge"]["impact"]["exact_value"] == "-77484.3599"
    assert [finding["finding_type"] for finding in committed["findings"]] == [
        "fulfillment_cost_increase",
        "revenue_growth",
        "ar_cash_deterioration",
        "operating_profit_deterioration",
    ]
    assert committed["margin_matrix"]["comparison_label"] == "同比"
