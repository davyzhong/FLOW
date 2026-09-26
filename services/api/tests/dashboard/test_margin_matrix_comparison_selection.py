from flow_api.dashboard.service import _select_margin_comparison_type


def test_margin_matrix_prefers_comparison_with_more_published_cells() -> None:
    assert _select_margin_comparison_type(budget_count=10, yoy_count=8) == (
        "budget_variance_month",
        "预算",
    )
    assert _select_margin_comparison_type(budget_count=8, yoy_count=10) == (
        "yoy_variance_month",
        "同比",
    )


def test_margin_matrix_prefers_budget_when_coverage_is_tied() -> None:
    assert _select_margin_comparison_type(budget_count=8, yoy_count=8) == (
        "budget_variance_month",
        "预算",
    )


def test_margin_matrix_reports_unavailable_when_no_comparison_cells_exist() -> None:
    assert _select_margin_comparison_type(budget_count=0, yoy_count=0) == (
        "yoy_variance_month",
        "不可用",
    )
