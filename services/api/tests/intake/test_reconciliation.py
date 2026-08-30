from __future__ import annotations

from decimal import Decimal

from flow_api.fixtures.generator import build_reference_package
from flow_api.intake.reconciliation import reconcile


def test_reference_operating_and_financial_facts_reconcile_exactly() -> None:
    checks = {check.code: check for check in reconcile(build_reference_package())}

    assert checks["operating_to_financial_revenue"].passed
    assert checks["operating_to_financial_revenue"].difference == Decimal("0.0000")
    assert checks["operating_to_financial_direct_cost"].passed
    assert checks["operating_to_financial_direct_cost"].difference == Decimal("0.0000")


def test_reconciliation_outside_explicit_tolerance_fails() -> None:
    package = build_reference_package()
    revenue_row = next(
        row for row in package.financial_actuals if row.management_account_code == "REVENUE"
    )
    changed_row = revenue_row.model_copy(update={"amount": revenue_row.amount + Decimal("0.02")})
    changed = package.model_copy(
        update={
            "financial_actuals": tuple(
            changed_row if row.record_id == revenue_row.record_id else row
            for row in package.financial_actuals
            )
        }
    )

    check = next(
        item
        for item in reconcile(changed, tolerance=Decimal("0.01"))
        if item.code == "operating_to_financial_revenue"
    )
    assert not check.passed
    assert check.difference == Decimal("-0.0200")
    assert check.tolerance == Decimal("0.0100")
