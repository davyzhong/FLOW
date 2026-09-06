"""统一财务事实契约（A02）测试：每条契约违规均有正反例。

规格：docs/superpowers/specs/financial-facts-contract.md。
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from flow_api.statements.fact_contract import (
    AccountingStandard,
    ConsolidationScope,
    FactConflictError,
    FinancialFact,
    MissingReason,
    Period,
    PeriodKind,
    PeriodMismatchError,
    SourceLocator,
    TimeSemantics,
    Unit,
    assert_comparable,
    merge_flow,
    to_base,
)

SHA = "a" * 64


def _period(kind: PeriodKind = PeriodKind.SINGLE_QUARTER) -> Period:
    if kind == PeriodKind.POINT:
        return Period(start=date(2026, 3, 31), end=date(2026, 3, 31), kind=kind, label="2026-03-31")
    if kind == PeriodKind.ANNUAL:
        return Period(start=date(2025, 1, 1), end=date(2025, 12, 31), kind=kind, label="FY2025")
    if kind == PeriodKind.YTD:
        return Period(start=date(2026, 1, 1), end=date(2026, 3, 31), kind=kind, label="2026Q1 累计")
    return Period(start=date(2026, 1, 1), end=date(2026, 3, 31), kind=kind, label="2026Q1")


def _fact(**overrides: object) -> FinancialFact:
    base = {
        "subject": "顺丰控股 002352.SZ",
        "original_label": "营业收入",
        "period": _period(),
        "semantics": TimeSemantics.FLOW,
        "unit": Unit(currency="CNY", scale="1e3"),
        "scope": ConsolidationScope.CONSOLIDATED,
        "standard": AccountingStandard.CAS,
        "source": SourceLocator(file_sha256=SHA, page=5, table="合并利润表", row="营业收入"),
        "value": Decimal("74142121"),
    }
    base.update(overrides)
    return FinancialFact(**base)  # type: ignore[arg-type]


def test_valid_fact_constructs() -> None:
    fact = _fact()
    assert fact.value == Decimal("74142121")
    assert fact.restated is False


def test_stock_fact_requires_single_date() -> None:
    ok = _fact(
        semantics=TimeSemantics.STOCK,
        period=_period(PeriodKind.POINT),
        original_label="资产总计",
    )
    assert ok.period.start == ok.period.end
    with pytest.raises(ValidationError, match="stock 事实必须是单一日期"):
        _fact(semantics=TimeSemantics.STOCK, period=_period())


def test_flow_fact_rejects_point_period() -> None:
    with pytest.raises(ValidationError, match="flow 事实不能使用 point 期间"):
        _fact(period=_period(PeriodKind.POINT))


def test_ytd_must_start_at_fiscal_year_start() -> None:
    with pytest.raises(ValidationError, match="财年首日"):
        Period(
            start=date(2026, 2, 1),
            end=date(2026, 3, 31),
            kind=PeriodKind.YTD,
            label="bad",
        )


def test_missing_value_requires_reason_and_vice_versa() -> None:
    with pytest.raises(ValidationError, match="空值不等于零"):
        _fact(value=None)
    with pytest.raises(ValidationError, match="不得携带 missing_reason"):
        _fact(missing_reason=MissingReason.NOT_DISCLOSED)
    missing = _fact(value=None, missing_reason=MissingReason.NOT_DISCLOSED)
    assert missing.value is None


def test_float_value_rejected() -> None:
    with pytest.raises(ValidationError):
        _fact(value=74142121.0)


def test_scaling_is_reversible() -> None:
    value = Decimal("74142121")
    assert to_base(to_base(value, "1e3", "1"), "1", "1e3") == value
    assert to_base(Decimal("124599558"), "1e3", "1e6") == Decimal("124599.558")
    with pytest.raises(ValidationError):
        Unit(currency="CNY", scale="1e2")


def test_merge_flow_sums_same_kind_with_scale_conversion() -> None:
    q1 = _fact(value=Decimal("1000"))
    q2 = _fact(value=Decimal("2"), unit=Unit(currency="CNY", scale="1e6"))
    total = merge_flow((q1, q2))
    assert total == Decimal("3000")


def test_merge_flow_missing_is_contagious() -> None:
    q1 = _fact(value=Decimal("1000"))
    q2 = _fact(value=None, missing_reason=MissingReason.NOT_DISCLOSED)
    assert merge_flow((q1, q2)) is None


def test_merge_flow_rejects_stock_and_mixed_kinds() -> None:
    stock = _fact(semantics=TimeSemantics.STOCK, period=_period(PeriodKind.POINT))
    with pytest.raises(FactConflictError, match="时点余额"):
        merge_flow((stock, stock))
    with pytest.raises(PeriodMismatchError):
        merge_flow((_fact(), _fact(period=_period(PeriodKind.ANNUAL))))


def test_merge_rejects_scope_currency_standard_conflicts() -> None:
    with pytest.raises(FactConflictError, match="合并范围冲突"):
        merge_flow((_fact(), _fact(scope=ConsolidationScope.PARENT)))
    with pytest.raises(FactConflictError, match="币种冲突"):
        merge_flow((_fact(), _fact(unit=Unit(currency="HKD", scale="1e3"))))
    with pytest.raises(FactConflictError, match="准则冲突"):
        merge_flow((_fact(), _fact(standard=AccountingStandard.IFRS)))


def test_single_quarter_not_comparable_with_ytd() -> None:
    with pytest.raises(PeriodMismatchError, match="单季/累计不可误混"):
        assert_comparable(_fact(), _fact(period=_period(PeriodKind.YTD)))
    assert_comparable(_fact(), _fact())


def test_source_locator_requires_sub_file_position() -> None:
    with pytest.raises(ValidationError, match="至少提供一项定位"):
        SourceLocator(file_sha256=SHA)
    with pytest.raises(ValidationError, match="SHA-256"):
        SourceLocator(file_sha256="not-a-sha", page=1)


def test_restated_versions_coexist() -> None:
    original = _fact(value=Decimal("100"))
    restated = _fact(value=Decimal("120"), restated=True, caliber_note="重述后")
    assert original.restated is False and restated.restated is True
    assert original.value != restated.value
