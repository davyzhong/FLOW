from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

MetricCalculationErrorCode = Literal[
    "float_rejected",
    "missing_dependency",
    "unsupported_formula",
    "zero_denominator",
]
PERSISTED_SCALE = 4


class MetricCalculationError(ValueError):
    def __init__(
        self, metric_code: str, code: MetricCalculationErrorCode, message: str
    ) -> None:
        super().__init__(message)
        self.metric_code = metric_code
        self.code = code


@dataclass(frozen=True, slots=True)
class CalculatedDecimal:
    exact_value: Decimal
    persisted_value: Decimal
    output_scale: int
    rounding: str = "ROUND_HALF_UP"


def _quantum(scale: int) -> Decimal:
    if scale < 0:
        raise ValueError("decimal scale cannot be negative")
    return Decimal(1).scaleb(-scale)


def _require_decimal(metric_code: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise MetricCalculationError(
            metric_code,
            "float_rejected",
            f"{metric_code} accepts Decimal values only, received {type(value).__name__}",
        )
    return value


def decimal_sum(values: Iterable[Decimal], *, scale: int = 4) -> Decimal:
    total = Decimal("0")
    for value in values:
        total += _require_decimal("decimal_sum", value)
    return total.quantize(_quantum(scale), rounding=ROUND_HALF_UP)


def calculate_amount(
    metric_code: str, value: Decimal, *, output_scale: int = 4
) -> CalculatedDecimal:
    decimal_value = _require_decimal(metric_code, value)
    exact_value = decimal_value.quantize(_quantum(output_scale), rounding=ROUND_HALF_UP)
    return CalculatedDecimal(
        exact_value=exact_value,
        persisted_value=exact_value.quantize(
            _quantum(PERSISTED_SCALE), rounding=ROUND_HALF_UP
        ),
        output_scale=output_scale,
    )


def calculate_ratio(
    metric_code: str,
    numerator: Decimal,
    denominator: Decimal,
    *,
    multiplier: Decimal = Decimal("1"),
    output_scale: int = 6,
) -> CalculatedDecimal:
    decimal_numerator = _require_decimal(metric_code, numerator)
    decimal_denominator = _require_decimal(metric_code, denominator)
    decimal_multiplier = _require_decimal(metric_code, multiplier)
    if decimal_denominator == 0:
        raise MetricCalculationError(
            metric_code,
            "zero_denominator",
            f"{metric_code} denominator cannot be zero",
        )
    return calculate_amount(
        metric_code,
        decimal_numerator / decimal_denominator * decimal_multiplier,
        output_scale=output_scale,
    )
