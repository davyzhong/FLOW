from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from flow_api.fixtures.generator import build_reference_package
from flow_api.fixtures.known_answers import calculate_known_answers, write_known_answers

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
KNOWN_ANSWERS_PATH = REPOSITORY_ROOT / "fixtures/expected/known_answers.json"


def test_known_answers_cover_headlines_slices_and_reconciliation() -> None:
    answers = calculate_known_answers(build_reference_package())

    assert set(answers["headline_totals"]) == {"analysis", "comparison", "budget"}
    for window in ("analysis", "comparison"):
        assert {
            "orders",
            "shipments",
            "revenue",
            "direct_cost",
            "gross_profit",
            "gross_margin",
            "operating_expense",
            "operating_profit",
            "operating_cash_flow",
            "cash_conversion",
        }.issubset(answers["headline_totals"][window])
    assert set(answers["revenue_slices"]) == {
        "by_segment",
        "by_product",
        "by_organization",
        "by_region",
        "by_month",
    }
    assert answers["reconciliation"]["operating_to_financial_revenue"]["difference"] == "0.0000"
    assert answers["reconciliation"]["operating_to_financial_direct_cost"]["difference"] == "0.0000"


def test_known_business_story_is_machine_checkable() -> None:
    answers = calculate_known_answers(build_reference_package())
    story = answers["story_predicates"]

    assert story == {
        "revenue_yoy_positive": True,
        "key_account_orders_yoy_negative": True,
        "domestic_orders_yoy_positive": True,
        "gross_margin_final_quarter_down": True,
        "transport_cost_per_order_final_quarter_up": True,
        "cash_conversion_below_one": True,
        "overdue_ar_concentrated": True,
        "growth_product_below_budget_margin": True,
        "operating_profit_final_quarter_below_budget": True,
    }


def test_headline_answers_are_frozen_exactly() -> None:
    answers = calculate_known_answers(build_reference_package())

    assert answers["headline_totals"]["analysis"] == {
        "orders": "192891.9451",
        "shipments": "628827.7397",
        "revenue": "26300990.4095",
        "direct_cost": "17346032.7562",
        "gross_profit": "8954957.6533",
        "gross_margin": "0.340480",
        "operating_expense": "2246061.8155",
        "operating_profit": "6708895.8378",
        "operating_cash_flow": "4941609.8078",
        "cash_conversion": "0.736576",
    }
    assert answers["headline_totals"]["comparison"]["revenue"] == "23944356.3138"
    assert answers["headline_totals"]["budget"]["OPERATING_PROFIT"] == "7106684.9539"
    assert answers["final_quarter"]["operating_profit_gap"] == "-651579.5664"
    assert answers["final_month_ar"]["overdue_amount"] == "1293530.5934"


def test_final_month_ar_totals_equal_bucket_and_customer_slices() -> None:
    answers = calculate_known_answers(build_reference_package())
    ar = answers["final_month_ar"]

    bucket_balance = sum(
        (Decimal(value) for value in ar["receivable_balance_by_bucket"].values()),
        start=Decimal("0"),
    )
    customer_balance = sum(
        (Decimal(value) for value in ar["receivable_balance_by_customer"].values()),
        start=Decimal("0"),
    )
    assert bucket_balance == Decimal(ar["receivable_balance"])
    assert customer_balance == Decimal(ar["receivable_balance"])


def test_committed_known_answers_are_exact_and_deterministic(tmp_path: Path) -> None:
    package = build_reference_package()
    expected = calculate_known_answers(package)
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    write_known_answers(package, first)
    write_known_answers(package, second)

    assert first.read_bytes() == second.read_bytes()
    assert json.loads(first.read_text(encoding="utf-8")) == expected
    assert json.loads(KNOWN_ANSWERS_PATH.read_text(encoding="utf-8")) == expected
