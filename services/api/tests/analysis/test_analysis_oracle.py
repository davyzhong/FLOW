import json
from decimal import Decimal
from pathlib import Path

from flow_api.fixtures.analysis_known_answers import build_analysis_known_answers

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
ORACLE_PATH = REPOSITORY_ROOT / "fixtures/expected/analysis_results_v1.json"


def test_committed_analysis_oracle_matches_independent_canonical_calculation() -> None:
    committed = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
    calculated = build_analysis_known_answers(REPOSITORY_ROOT)

    assert calculated == committed
    assert set(committed["results"]) == {
        "revenue_vpm",
        "fulfillment_cost_rve",
        "gross_profit_bridge",
        "operating_profit_bridge",
        "ar_cash_impact",
    }
    for result in committed["results"].values():
        driver_total = sum(
            (Decimal(item["amount"]) for item in result["drivers"]), start=Decimal("0")
        )
        assert abs(driver_total - Decimal(result["impact_amount"])) <= Decimal("0.01")
    assert committed["story_predicates"] == {
        "revenue_growth": True,
        "fulfillment_cost_increase": True,
        "operating_profit_deterioration": True,
        "ar_cash_deterioration": True,
    }
    assert "ar_cash_deterioration" in committed["finding_rank"][:3]
    assert "operating_profit_deterioration" in committed["finding_rank"]
