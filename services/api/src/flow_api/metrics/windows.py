from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ComparisonType = Literal[
    "actual_month",
    "actual_ytd",
    "budget_month",
    "budget_ytd",
    "budget_variance",
    "budget_variance_pct",
    "prior_year_month",
    "prior_year_ytd",
    "yoy_variance",
    "yoy_variance_pct",
    "trailing_12",
]
WindowComparisonType = Literal[
    "actual_month",
    "actual_ytd",
    "budget_month",
    "budget_ytd",
    "prior_year_month",
    "prior_year_ytd",
    "trailing_12",
]


@dataclass(frozen=True, slots=True)
class MetricWindow:
    comparison_type: WindowComparisonType
    as_of_month: int
    included_months: frozenset[int]


@dataclass(frozen=True, slots=True)
class WindowUnavailable:
    comparison_type: WindowComparisonType
    code: Literal["missing_periods"]
    missing_months: frozenset[int]


def _shift_month(month_key: int, offset: int) -> int:
    year, month = divmod(month_key, 100)
    if month < 1 or month > 12:
        raise ValueError(f"invalid month key: {month_key}")
    absolute = year * 12 + month - 1 + offset
    shifted_year, shifted_month = divmod(absolute, 12)
    return shifted_year * 100 + shifted_month + 1


def _month_range(start: int, end: int) -> frozenset[int]:
    if start > end:
        raise ValueError("month range start must not exceed end")
    months: set[int] = set()
    current = start
    while current <= end:
        months.add(current)
        current = _shift_month(current, 1)
    return frozenset(months)


def _candidate_windows(as_of_month: int) -> tuple[MetricWindow, ...]:
    year = as_of_month // 100
    actual_month = frozenset({as_of_month})
    actual_ytd = _month_range(year * 100 + 1, as_of_month)
    prior_as_of = _shift_month(as_of_month, -12)
    prior_ytd = _month_range((year - 1) * 100 + 1, prior_as_of)
    return (
        MetricWindow("actual_month", as_of_month, actual_month),
        MetricWindow("actual_ytd", as_of_month, actual_ytd),
        MetricWindow("budget_month", as_of_month, actual_month),
        MetricWindow("budget_ytd", as_of_month, actual_ytd),
        MetricWindow("prior_year_month", as_of_month, frozenset({prior_as_of})),
        MetricWindow("prior_year_ytd", as_of_month, prior_ytd),
        MetricWindow(
            "trailing_12",
            as_of_month,
            _month_range(_shift_month(as_of_month, -11), as_of_month),
        ),
    )


def metric_windows(periods: tuple[int, ...], as_of_month: int) -> tuple[MetricWindow, ...]:
    available = frozenset(periods)
    if as_of_month not in available:
        raise ValueError(f"as-of month is unavailable: {as_of_month}")
    return tuple(
        window
        for window in _candidate_windows(as_of_month)
        if window.included_months <= available
    )


def window_unavailability(
    periods: tuple[int, ...], as_of_month: int
) -> tuple[WindowUnavailable, ...]:
    available = frozenset(periods)
    if as_of_month not in available:
        raise ValueError(f"as-of month is unavailable: {as_of_month}")
    return tuple(
        WindowUnavailable(
            comparison_type=window.comparison_type,
            code="missing_periods",
            missing_months=window.included_months - available,
        )
        for window in _candidate_windows(as_of_month)
        if not window.included_months <= available
    )
