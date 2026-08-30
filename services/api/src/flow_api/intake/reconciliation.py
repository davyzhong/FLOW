from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from flow_api.data_contract.records import CanonicalPackage

MONEY_QUANTUM = Decimal("0.0001")
DIRECT_COST_ACCOUNTS = {
    "WAREHOUSING_COST",
    "TRANSPORTATION_COST",
    "OTHER_DIRECT_COST",
}


@dataclass(frozen=True, slots=True)
class ReconciliationCheck:
    code: str
    passed: bool
    expected_value: Decimal
    actual_value: Decimal
    difference: Decimal
    tolerance: Decimal
    details: str


def _check(
    code: str,
    operating_value: Decimal,
    financial_value: Decimal,
    tolerance: Decimal,
    details: str,
) -> ReconciliationCheck:
    expected = operating_value.quantize(MONEY_QUANTUM)
    actual = financial_value.quantize(MONEY_QUANTUM)
    difference = (expected - actual).quantize(MONEY_QUANTUM)
    normalized_tolerance = tolerance.quantize(MONEY_QUANTUM)
    return ReconciliationCheck(
        code=code,
        passed=abs(difference) <= normalized_tolerance,
        expected_value=expected,
        actual_value=actual,
        difference=difference,
        tolerance=normalized_tolerance,
        details=details,
    )


def reconcile(
    package: CanonicalPackage, tolerance: Decimal = Decimal("0.01")
) -> tuple[ReconciliationCheck, ...]:
    operating_revenue = sum((row.revenue for row in package.operating_actuals), Decimal(0))
    financial_revenue = sum(
        (
            row.amount
            for row in package.financial_actuals
            if row.management_account_code == "REVENUE"
        ),
        Decimal(0),
    )
    operating_direct_cost = sum(
        (
            row.warehousing_cost + row.transportation_cost + row.other_direct_cost
            for row in package.operating_actuals
        ),
        Decimal(0),
    )
    financial_direct_cost = sum(
        (
            row.amount
            for row in package.financial_actuals
            if row.management_account_code in DIRECT_COST_ACCOUNTS
        ),
        Decimal(0),
    )
    return (
        _check(
            "operating_to_financial_revenue",
            operating_revenue,
            financial_revenue,
            tolerance,
            "经营实际营业收入合计应等于财务实际 REVENUE 合计。",
        ),
        _check(
            "operating_to_financial_direct_cost",
            operating_direct_cost,
            financial_direct_cost,
            tolerance,
            "经营实际三类直接成本合计应等于财务实际直接成本科目合计。",
        ),
    )
