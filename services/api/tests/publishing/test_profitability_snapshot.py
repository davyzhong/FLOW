from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from flow_api.publishing.profitability_snapshot import build_profitability_payload


def _row(item_id: str, *, current: str | None = None, ending: str | None = None,
         beginning: str | None = None, row_id: str = "row") -> SimpleNamespace:
    return SimpleNamespace(
        item_id=item_id,
        id=row_id,
        statement_type="合并财务报表",
        value_current=Decimal(current) if current is not None else None,
        value_end=Decimal(ending) if ending is not None else None,
        value_begin=Decimal(beginning) if beginning is not None else None,
        value_prior=None,
        page_number=3,
        page_anchor="strong",
        trace={},
    )


def test_freezes_average_balance_dupont_metrics_with_source_trace() -> None:
    payload = build_profitability_payload(
        [
            _row("is.net_profit", current="15", row_id="profit"),
            _row("is.revenue", current="100", row_id="revenue"),
            _row("bs.total_assets", ending="120", beginning="80", row_id="assets"),
            _row("bs.equity", ending="60", beginning="40", row_id="equity"),
        ],
        report_id="report-1",
    )

    metrics = payload["metrics"]
    assert metrics["roe"]["status"] == "available"
    assert Decimal(metrics["roe"]["value"]) == Decimal("0.3")
    assert Decimal(metrics["net_margin"]["value"]) == Decimal("0.15")
    assert Decimal(metrics["total_asset_turnover"]["value"]) == Decimal("1")
    assert Decimal(metrics["equity_multiplier"]["value"]) == Decimal("2")
    assert payload["consistency"]["status"] == "passed"
    assert payload["inputs"]["bs.equity:beginning"]["row_id"] == "equity"
    assert payload["inputs"]["bs.equity:beginning"]["page_number"] == 3
    assert payload["dictionary_sha256"]


def test_missing_opening_balance_does_not_substitute_closing_balance() -> None:
    payload = build_profitability_payload(
        [
            _row("is.net_profit", current="15"),
            _row("is.revenue", current="100"),
            _row("bs.total_assets", ending="120"),
            _row("bs.equity", ending="60"),
        ],
        report_id="report-2",
    )

    metrics = payload["metrics"]
    assert metrics["net_margin"]["status"] == "available"
    assert metrics["roe"]["status"] == "unavailable"
    assert metrics["total_asset_turnover"]["reason"] == "required_report_fact_missing"
    assert payload["consistency"]["status"] == "unavailable"


def test_duplicate_canonical_row_is_not_arbitrarily_selected() -> None:
    payload = build_profitability_payload(
        [
            _row("is.net_profit", current="15"),
            _row("is.revenue", current="100"),
            _row("is.revenue", current="100", row_id="duplicate"),
            _row("bs.total_assets", ending="120", beginning="80"),
            _row("bs.equity", ending="60", beginning="40"),
        ],
        report_id="report-3",
    )

    assert payload["metrics"]["net_margin"]["reason"] == "required_report_fact_missing"
    assert payload["inputs"]["is.revenue:flow"]["status"] == "ambiguous"
