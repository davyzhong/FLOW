from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

MONEY_QUANTUM = Decimal("0.0001")
RATIO_QUANTUM = Decimal("0.000001")


class AnalysisCalculationError(ValueError):
    pass


def ensure_decimal(value: Decimal | int | str) -> Decimal:
    if isinstance(value, float):
        raise TypeError("float values are forbidden; use Decimal or decimal strings")
    if isinstance(value, Decimal):
        return value
    return Decimal(value)


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def ratio(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_UP)


def contribution_ratio(amount: Decimal, total: Decimal) -> Decimal | None:
    if total == 0:
        return None
    return ratio(amount / total)


def reconcile(calculated: Decimal, target: Decimal, tolerance: Decimal) -> Decimal:
    difference = money(calculated - target)
    if abs(difference) > tolerance:
        raise AnalysisCalculationError(
            f"bridge does not reconcile: calculated={calculated}, target={target}, "
            f"difference={difference}, tolerance={tolerance}"
        )
    return difference


__all__ = [
    "AnalysisCalculationError",
    "MONEY_QUANTUM",
    "RATIO_QUANTUM",
    "contribution_ratio",
    "ensure_decimal",
    "money",
    "ratio",
    "reconcile",
]
