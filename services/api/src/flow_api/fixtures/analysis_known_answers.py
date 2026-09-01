from __future__ import annotations

import json
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

import yaml

MONEY = Decimal("0.0001")
SIX = Decimal("0.000001")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _six(value: Decimal) -> Decimal:
    return value.quantize(SIX, rounding=ROUND_HALF_UP)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _decimal(row: dict[str, Any], field: str) -> Decimal:
    return Decimal(str(row[field]))


def _sum(rows: list[dict[str, Any]], field: str) -> Decimal:
    return sum((_decimal(row, field) for row in rows), start=Decimal("0"))


def _driver(code: str, amount: Decimal) -> dict[str, str]:
    return {"code": code, "amount": str(_money(amount))}


def _result(impact: Decimal, drivers: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "status": "complete",
        "impact_amount": str(_money(impact)),
        "drivers": drivers,
    }


def _revenue_vpm(
    analysis: list[dict[str, Any]], comparison: list[dict[str, Any]]
) -> dict[str, Any]:
    by_product_1: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_product_0: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in analysis:
        by_product_1[str(row["logistics_product_code"])].append(row)
    for row in comparison:
        by_product_0[str(row["logistics_product_code"])].append(row)
    products = sorted(set(by_product_0) | set(by_product_1))
    q0 = {code: _sum(by_product_0[code], "order_count") for code in products}
    q1 = {code: _sum(by_product_1[code], "order_count") for code in products}
    r0 = {code: _sum(by_product_0[code], "revenue") for code in products}
    r1 = {code: _sum(by_product_1[code], "revenue") for code in products}
    total_q0 = sum(q0.values(), start=Decimal("0"))
    total_q1 = sum(q1.values(), start=Decimal("0"))
    total_r0 = sum(r0.values(), start=Decimal("0"))
    total_r1 = sum(r1.values(), start=Decimal("0"))
    base_price = total_r0 / total_q0
    volume = (total_q1 - total_q0) * base_price
    mix = sum(
        (q1[code] * (r0[code] / q0[code] - base_price) for code in products),
        start=Decimal("0"),
    )
    price = sum(
        (
            q1[code] * (r1[code] / q1[code] - r0[code] / q0[code])
            for code in products
        ),
        start=Decimal("0"),
    )
    return _result(
        total_r1 - total_r0,
        [_driver("volume", volume), _driver("mix", mix), _driver("price", price)],
    )


def _fulfillment_rve(
    analysis: list[dict[str, Any]], comparison: list[dict[str, Any]]
) -> dict[str, Any]:
    o0 = _sum(comparison, "order_count")
    o1 = _sum(analysis, "order_count")
    shipments0 = _sum(comparison, "shipment_count")
    shipments1 = _sum(analysis, "shipment_count")
    cost0 = sum(
        (
            _decimal(row, "warehousing_cost")
            + _decimal(row, "transportation_cost")
            + _decimal(row, "other_direct_cost")
            for row in comparison
        ),
        start=Decimal("0"),
    )
    cost1 = sum(
        (
            _decimal(row, "warehousing_cost")
            + _decimal(row, "transportation_cost")
            + _decimal(row, "other_direct_cost")
            for row in analysis
        ),
        start=Decimal("0"),
    )
    shipments_per_order0 = shipments0 / o0
    shipments_per_order1 = shipments1 / o1
    cost_per_shipment0 = cost0 / shipments0
    cost_per_shipment1 = cost1 / shipments1
    volume = (o1 - o0) * shipments_per_order0 * cost_per_shipment0
    efficiency = o1 * (shipments_per_order1 - shipments_per_order0) * cost_per_shipment0
    rate = o1 * shipments_per_order1 * (cost_per_shipment1 - cost_per_shipment0)
    return _result(
        cost1 - cost0,
        [
            _driver("volume", volume),
            _driver("efficiency", efficiency),
            _driver("rate", rate),
        ],
    )


def _profit_results(
    analysis: list[dict[str, Any]],
    comparison: list[dict[str, Any]],
    financial: list[dict[str, Any]],
    revenue_result: dict[str, Any],
    analysis_months: set[str],
    comparison_months: set[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    cost_fields = ("warehousing_cost", "transportation_cost", "other_direct_cost")
    r0 = _sum(comparison, "revenue")
    r1 = _sum(analysis, "revenue")
    cost0 = {field: _sum(comparison, field) for field in cost_fields}
    cost1 = {field: _sum(analysis, field) for field in cost_fields}
    gp0 = r0 - sum(cost0.values(), start=Decimal("0"))
    gp1 = r1 - sum(cost1.values(), start=Decimal("0"))
    gross_drivers = [
        _driver(f"revenue_{item['code']}", Decimal(item["amount"]))
        for item in revenue_result["drivers"]
    ] + [
        _driver("warehousing_cost", -(cost1["warehousing_cost"] - cost0["warehousing_cost"])),
        _driver(
            "transportation_cost",
            -(cost1["transportation_cost"] - cost0["transportation_cost"]),
        ),
        _driver(
            "other_direct_cost",
            -(cost1["other_direct_cost"] - cost0["other_direct_cost"]),
        ),
    ]
    gross = _result(gp1 - gp0, gross_drivers)

    def financial_total(code: str, months: set[str]) -> Decimal:
        return sum(
            (
                _decimal(row, "amount")
                for row in financial
                if row["month_key"] in months and row["management_account_code"] == code
            ),
            start=Decimal("0"),
        )

    op0 = financial_total("OPERATING_PROFIT", comparison_months)
    op1 = financial_total("OPERATING_PROFIT", analysis_months)
    opex0 = financial_total("OPERATING_EXPENSE", comparison_months)
    opex1 = financial_total("OPERATING_EXPENSE", analysis_months)
    operating = _result(
        op1 - op0,
        gross_drivers + [_driver("operating_expense", -(opex1 - opex0))],
    )
    return gross, operating


def _ar_cash(
    ar_rows: list[dict[str, Any]], analysis_end: str, comparison_end: str
) -> dict[str, Any]:
    current = [row for row in ar_rows if row["month_key"] == analysis_end]
    prior = [row for row in ar_rows if row["month_key"] == comparison_end]
    buckets = sorted(
        {str(row["aging_bucket"]) for row in current + prior}
    )
    current_by_bucket = {
        bucket: _sum(
            [row for row in current if row["aging_bucket"] == bucket],
            "receivable_balance",
        )
        for bucket in buckets
    }
    prior_by_bucket = {
        bucket: _sum([row for row in prior if row["aging_bucket"] == bucket], "receivable_balance")
        for bucket in buckets
    }
    current_ar = sum(current_by_bucket.values(), start=Decimal("0"))
    prior_ar = sum(prior_by_bucket.values(), start=Decimal("0"))
    impact = -(current_ar - prior_ar)
    drivers = [
        _driver(
            f"aging_{bucket.lower().replace('+', '_plus').replace('-', '_')}",
            -(current_by_bucket[bucket] - prior_by_bucket[bucket]),
        )
        for bucket in buckets
    ]
    return _result(impact, drivers)


def _finding_rank(
    results: dict[str, dict[str, Any]], policy: dict[str, Any]
) -> tuple[list[str], list[str]]:
    mapping = {
        "revenue_vpm": ("revenue_growth", "positive"),
        "fulfillment_cost_rve": ("fulfillment_cost_increase", "positive"),
        "gross_profit_bridge": ("gross_profit_deterioration", "negative"),
        "operating_profit_bridge": ("operating_profit_deterioration", "negative"),
        "ar_cash_impact": ("ar_cash_deterioration", "negative"),
    }
    weights = {key: Decimal(str(value)) for key, value in policy["ranking_weights"].items()}
    scored: list[tuple[str, Decimal, Decimal]] = []
    for code, result in results.items():
        finding_type, direction = mapping[code]
        impact = Decimal(result["impact_amount"])
        threshold = Decimal(str(policy["qualification_materiality"][finding_type]))
        direction_passed = (direction == "positive" and impact > 0) or (
            direction == "negative" and impact < 0
        )
        if not direction_passed or abs(impact) < threshold:
            continue
        high = Decimal(str(policy["high_materiality_amount"][finding_type]))
        materiality = _six(min(abs(impact) / high, Decimal("1")) * Decimal("100"))
        persistence = Decimal("50.000000")
        evidence = Decimal("100.000000")
        relevance = _six(Decimal(str(policy["management_relevance"][finding_type])))
        total = _six(
            _six(materiality * weights["materiality"])
            + _six(persistence * weights["persistence"])
            + _six(evidence * weights["evidence_completeness"])
            + _six(relevance * weights["management_relevance"])
        )
        scored.append((finding_type, total, abs(impact)))
    scored.sort(key=lambda item: (-item[1], -item[2], item[0]))
    return [item[0] for item in scored], [str(item[1]) for item in scored]


def build_analysis_known_answers(repository_root: Path) -> dict[str, Any]:
    canonical = repository_root / "fixtures/canonical"
    periods = _read_jsonl(canonical / "periods.jsonl")
    operating = _read_jsonl(canonical / "operating_actuals.jsonl")
    financial = _read_jsonl(canonical / "financial_actuals.jsonl")
    ar_rows = _read_jsonl(canonical / "ar_collections.jsonl")
    analysis_months = {
        str(row["month_key"]) for row in periods if row["window"] == "analysis"
    }
    comparison_months = {
        str(row["month_key"]) for row in periods if row["window"] == "comparison"
    }
    analysis = [row for row in operating if row["month_key"] in analysis_months]
    comparison = [row for row in operating if row["month_key"] in comparison_months]
    revenue = _revenue_vpm(analysis, comparison)
    fulfillment = _fulfillment_rve(analysis, comparison)
    gross, operating_profit = _profit_results(
        analysis,
        comparison,
        financial,
        revenue,
        analysis_months,
        comparison_months,
    )
    ar_cash = _ar_cash(ar_rows, max(analysis_months), max(comparison_months))
    results = {
        "revenue_vpm": revenue,
        "fulfillment_cost_rve": fulfillment,
        "gross_profit_bridge": gross,
        "operating_profit_bridge": operating_profit,
        "ar_cash_impact": ar_cash,
    }
    policy_path = repository_root / "services/api/config/analysis/flow-logistics-v1.yaml"
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    if not isinstance(policy, dict):
        raise ValueError("analysis policy root must be a mapping")
    ranking, scores = _finding_rank(results, policy)
    return {
        "definition": "flow.analysis.logistics.v1",
        "results": results,
        "finding_rank": ranking,
        "finding_scores": scores,
        "story_predicates": {
            "revenue_growth": Decimal(revenue["impact_amount"]) > 0,
            "fulfillment_cost_increase": Decimal(fulfillment["impact_amount"]) > 0,
            "operating_profit_deterioration": Decimal(
                operating_profit["impact_amount"]
            )
            < 0,
            "ar_cash_deterioration": Decimal(ar_cash["impact_amount"]) < 0,
        },
    }


__all__ = ["build_analysis_known_answers"]
