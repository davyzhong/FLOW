from __future__ import annotations

import importlib

import pytest


def _windows_module():
    try:
        return importlib.import_module("flow_api.metrics.windows")
    except ModuleNotFoundError:
        pytest.fail("flow_api.metrics.windows does not exist")


def _months(start_year: int, start_month: int, count: int) -> tuple[int, ...]:
    result = []
    year, month = start_year, start_month
    for _ in range(count):
        result.append(year * 100 + month)
        month += 1
        if month == 13:
            year += 1
            month = 1
    return tuple(result)


def test_fixture_windows_separate_calendar_ytd_from_trailing_12() -> None:
    module = _windows_module()
    periods = _months(2024, 9, 24)

    windows = {
        window.comparison_type: window
        for window in module.metric_windows(periods, as_of_month=202608)
    }

    assert windows["actual_month"].included_months == frozenset({202608})
    assert windows["actual_ytd"].included_months == frozenset(
        202600 + month for month in range(1, 9)
    )
    assert windows["prior_year_month"].included_months == frozenset({202508})
    assert windows["prior_year_ytd"].included_months == frozenset(
        202500 + month for month in range(1, 9)
    )
    assert windows["trailing_12"].included_months == frozenset(_months(2025, 9, 12))
    assert windows["budget_month"].included_months == frozenset({202608})
    assert windows["budget_ytd"].included_months == windows["actual_ytd"].included_months


def test_january_ytd_contains_only_january() -> None:
    module = _windows_module()
    periods = _months(2025, 1, 13)
    windows = {
        window.comparison_type: window
        for window in module.metric_windows(periods, as_of_month=202601)
    }

    assert windows["actual_ytd"].included_months == frozenset({202601})
    assert windows["prior_year_ytd"].included_months == frozenset({202501})
    assert len(windows["trailing_12"].included_months) == 12


def test_missing_prior_year_is_omitted_with_typed_reason() -> None:
    module = _windows_module()
    periods = _months(2026, 1, 8)

    windows = module.metric_windows(periods, as_of_month=202608)
    unavailable = module.window_unavailability(periods, as_of_month=202608)

    assert "prior_year_month" not in {window.comparison_type for window in windows}
    assert "prior_year_ytd" not in {window.comparison_type for window in windows}
    reasons = {item.comparison_type: item for item in unavailable}
    assert reasons["prior_year_month"].code == "missing_periods"
    assert reasons["prior_year_ytd"].missing_months == frozenset(
        202500 + month for month in range(1, 9)
    )
    assert "trailing_12" in reasons
