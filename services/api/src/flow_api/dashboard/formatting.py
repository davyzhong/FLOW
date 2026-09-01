from __future__ import annotations

from decimal import Decimal

from flow_api.dashboard.models import DashboardValue, SemanticDirection


def _decimal(value: Decimal | str) -> Decimal:
    if isinstance(value, float):
        raise TypeError("float values are forbidden in dashboard formatting")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, str):
        return Decimal(value)
    raise TypeError("dashboard values must be Decimal or decimal strings")


def available_value(
    value: Decimal | str,
    *,
    direction: SemanticDirection = "neutral",
) -> DashboardValue:
    exact = _decimal(value)
    display = str(exact)
    return DashboardValue(
        status="available",
        exact_value=exact,
        display_value=display,
        semantic_direction=direction,
    )


def comparison_value(value: Decimal | str, *, inverse: bool = False) -> DashboardValue:
    exact = _decimal(value)
    if exact == 0:
        direction: SemanticDirection = "neutral"
    else:
        favorable = exact > 0
        if inverse:
            favorable = not favorable
        direction = "positive" if favorable else "negative"
    return available_value(exact, direction=direction)


def unavailable_value(code: str, message: str) -> DashboardValue:
    return DashboardValue(
        status="unavailable",
        exact_value=None,
        display_value="—",
        semantic_direction="neutral",
        unavailable_code=code,
        unavailable_message=message,
    )


__all__ = ["available_value", "comparison_value", "unavailable_value"]
