from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

from flow_api.fixtures.generator import build_reference_package, write_canonical_package


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value: {value}")
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_float(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            assert_no_float(nested)


def test_reference_package_has_required_dimensions_and_windows() -> None:
    package = build_reference_package()

    assert package.batch.analysis_start_month == "2025-09"
    assert package.batch.analysis_end_month == "2026-08"
    assert package.batch.comparison_start_month == "2024-09"
    assert package.batch.comparison_end_month == "2025-08"
    assert len(package.periods) == 24
    assert len(package.customer_segments) == 2
    assert len(package.logistics_products) == 8
    assert len(package.organizations) >= 3
    assert len(package.regions) >= 4
    assert len(package.customers) >= 16
    assert len(package.management_accounts) >= 8
    assert len(package.scenario_versions) == 2


def test_reference_facts_have_unique_grains_and_complete_months() -> None:
    package = build_reference_package()

    operating_grains = {
        (
            row.month_key,
            row.organization_code,
            row.customer_code,
            row.logistics_product_code,
            row.region_code,
        )
        for row in package.operating_actuals
    }
    financial_grains = {
        (row.month_key, row.organization_code, row.management_account_code)
        for row in package.financial_actuals
    }
    budget_grains = {
        (
            row.month_key,
            row.organization_code,
            row.customer_segment_code,
            row.logistics_product_code,
            row.management_account_code,
            row.scenario_code,
            row.metric_code,
        )
        for row in package.monthly_budgets
    }
    ar_grains = {
        (row.month_key, row.customer_code, row.invoice_number, row.aging_bucket)
        for row in package.ar_collections
    }

    assert len(operating_grains) == len(package.operating_actuals)
    assert len(financial_grains) == len(package.financial_actuals)
    assert len(budget_grains) == len(package.monthly_budgets)
    assert len(ar_grains) == len(package.ar_collections)
    assert {row.month_key for row in package.operating_actuals} == {
        row.month_key for row in package.periods
    }
    assert {row.month_key for row in package.monthly_budgets} == {
        f"{year:04d}-{month:02d}" for year, month in ((2025, 9), (2025, 10), (2025, 11), (2025, 12))
    } | {f"2026-{month:02d}" for month in range(1, 9)}


def test_reference_relationships_and_decimal_boundaries_are_valid() -> None:
    package = build_reference_package()
    organization_codes = {row.code for row in package.organizations}
    customer_codes = {row.code for row in package.customers}
    product_codes = {row.code for row in package.logistics_products}
    region_codes = {row.code for row in package.regions}
    account_codes = {row.code for row in package.management_accounts}

    for row in package.operating_actuals:
        assert row.organization_code in organization_codes
        assert row.customer_code in customer_codes
        assert row.logistics_product_code in product_codes
        assert row.region_code in region_codes
        assert isinstance(row.revenue, Decimal)
    for row in package.financial_actuals:
        assert row.organization_code in organization_codes
        assert row.management_account_code in account_codes
    for row in package.ar_collections:
        assert row.customer_code in customer_codes

    assert_no_float(package.model_dump())


def test_generated_canonical_files_are_byte_deterministic(tmp_path: Path) -> None:
    package = build_reference_package()
    first = tmp_path / "first"
    second = tmp_path / "second"

    write_canonical_package(package, first)
    write_canonical_package(package, second)

    first_files = sorted(path.relative_to(first) for path in first.iterdir())
    second_files = sorted(path.relative_to(second) for path in second.iterdir())
    assert first_files == second_files
    for relative_path in first_files:
        assert (first / relative_path).read_bytes() == (second / relative_path).read_bytes()
