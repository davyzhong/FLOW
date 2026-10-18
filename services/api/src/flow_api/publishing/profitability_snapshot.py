"""在客观财报冻结时生成可追溯的盈利能力指标载荷。"""

from __future__ import annotations

import hashlib
from decimal import Decimal, DivisionByZero, InvalidOperation
from pathlib import Path
from typing import Any

import yaml

from flow_api.infrastructure.models.statement import StatementNormalizedItem

_METRIC_CODES = (
    "roe",
    "net_margin",
    "total_asset_turnover",
    "equity_multiplier",
)
_EPSILON = Decimal("0.00000001")


def _dictionary_path() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "config/metrics/metric_dictionary_v1_1.yaml"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("指标字典 config/metrics/metric_dictionary_v1_1.yaml 未找到")


def _row_value(row: StatementNormalizedItem, *names: str) -> Decimal | None:
    for name in names:
        value = getattr(row, name, None)
        if value is not None:
            return Decimal(str(value))
    return None


def build_profitability_payload(
    rows: list[StatementNormalizedItem], *, report_id: str
) -> dict[str, Any]:
    """按字典四个杜邦指标公式计算一次，并将来源值与口径随快照冻结。"""

    dictionary_path = _dictionary_path()
    dictionary_text = dictionary_path.read_text(encoding="utf-8")
    dictionary = yaml.safe_load(dictionary_text)
    definitions = {
        entry["metric_code"]: entry
        for entry in dictionary.get("metrics_general", [])
        if isinstance(entry, dict) and entry.get("metric_code") in _METRIC_CODES
    }
    by_item: dict[str, list[StatementNormalizedItem]] = {}
    for row in rows:
        if row.item_id:
            by_item.setdefault(row.item_id, []).append(row)

    def resolve(item_id: str, kind: str) -> tuple[Decimal | None, dict[str, Any]]:
        candidates = by_item.get(item_id, [])
        if len(candidates) != 1:
            return None, {"item_id": item_id, "status": "ambiguous" if candidates else "missing"}
        row = candidates[0]
        value_names = ("value_current", "value_end") if kind == "flow" else (
            ("value_end", "value_current") if kind == "ending" else ("value_begin", "value_prior")
        )
        value = _row_value(row, *value_names)
        trace = row.trace if isinstance(row.trace, dict) else {}
        return value, {
            "item_id": item_id,
            "statement_type": row.statement_type,
            "item_name": getattr(row, "item_name", None),
            "value": str(value) if value is not None else None,
            "role": kind,
            "page_number": getattr(row, "page_number", None) or trace.get("page_number"),
            "page_anchor": getattr(row, "page_anchor", None) or trace.get("page_anchor"),
        }

    inputs: dict[str, Decimal | None] = {}
    trace: dict[str, Any] = {}
    for item_id, kind in (
        ("is.net_profit", "flow"),
        ("is.revenue", "flow"),
        ("bs.total_assets", "ending"),
        ("bs.total_assets", "beginning"),
        ("bs.equity", "ending"),
        ("bs.equity", "beginning"),
    ):
        value, item_trace = resolve(item_id, kind)
        inputs[f"{item_id}:{kind}"] = value
        trace[f"{item_id}:{kind}"] = item_trace

    def average(item_id: str) -> Decimal | None:
        beginning = inputs[f"{item_id}:beginning"]
        ending = inputs[f"{item_id}:ending"]
        if beginning is None or ending is None:
            return None
        return (beginning + ending) / Decimal(2)

    revenue = inputs["is.revenue:flow"]
    net_profit = inputs["is.net_profit:flow"]
    avg_assets = average("bs.total_assets")
    avg_equity = average("bs.equity")
    operands = {
        "roe": (net_profit, avg_equity),
        "net_margin": (net_profit, revenue),
        "total_asset_turnover": (revenue, avg_assets),
        "equity_multiplier": (avg_assets, avg_equity),
    }
    metrics: dict[str, Any] = {}
    for code, (numerator, denominator) in operands.items():
        definition = definitions.get(code)
        reason = None
        if definition is None:
            reason = "metric_definition_missing"
        elif numerator is None or denominator is None:
            reason = "required_report_fact_missing"
        elif denominator == 0:
            reason = "zero_denominator"
        if reason:
            metrics[code] = {
                "status": "unavailable",
                "reason": reason,
                "value": None,
                "unit": definition.get("unit") if definition else None,
                "formula": definition.get("formula_text") if definition else None,
                "definition_id": code,
                "definition_version": dictionary.get("dictionary_id"),
                "report_id": report_id,
            }
            continue
        assert definition is not None
        try:
            value = numerator / denominator  # type: ignore[operator]
        except (DivisionByZero, InvalidOperation):
            value = None
        if value is None or not value.is_finite():
            metrics[code] = {
                "status": "unavailable", "reason": "invalid_result", "value": None,
                "unit": definition["unit"], "formula": definition["formula_text"],
                "definition_id": code, "definition_version": dictionary["dictionary_id"],
                "report_id": report_id,
            }
        else:
            metrics[code] = {
                "status": "available", "reason": None, "value": str(value),
                "unit": definition["unit"], "formula": definition["formula_text"],
                "definition_id": code, "definition_version": dictionary["dictionary_id"],
                "report_id": report_id,
            }

    consistency: dict[str, Any]
    if all(metrics[code]["status"] == "available" for code in _METRIC_CODES):
        product = (
            Decimal(metrics["net_margin"]["value"])
            * Decimal(metrics["total_asset_turnover"]["value"])
            * Decimal(metrics["equity_multiplier"]["value"])
        )
        roe = Decimal(metrics["roe"]["value"])
        difference = abs(product - roe)
        consistency = {
            "status": "passed" if difference <= _EPSILON else "failed",
            "difference": str(difference),
            "tolerance": str(_EPSILON),
        }
    else:
        consistency = {"status": "unavailable", "difference": None, "tolerance": str(_EPSILON)}

    return {
        "dictionary_id": dictionary.get("dictionary_id"),
        "dictionary_sha256": hashlib.sha256(dictionary_text.encode("utf-8")).hexdigest(),
        "report_id": report_id,
        "metrics": metrics,
        "inputs": trace,
        "consistency": consistency,
    }


__all__ = ["build_profitability_payload"]
