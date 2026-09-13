"""Financial Facts Contract V2 纯领域模型测试（S01 Task 3，TDD 红灯先行）。

规格：docs/40_specs/financial-facts/financial-facts-contract-v2.md（approved）。
要点：internal 事实身份完整性强校验；float 金额拒绝；比较必须引用两个完整 V2 身份；
跨企业、单位、范围或预算版本不可比较。
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from flow_api.financial_facts_v2.models import (
    ComparisonKind,
    ContractV2Violation,
    FactContext,
    FinancialFactV2,
    Scenario,
    WorkbookLocator,
    assert_comparable_v2,
)
from flow_api.statements.fact_contract import (
    AccountingStandard,
    ConsolidationScope,
    FinancialFact,
    Period,
    PeriodKind,
    SourceLocator,
    TimeSemantics,
    Unit,
)

SHA = "b" * 64
ENTERPRISE = UUID("12345678-1234-5678-1234-567812345678")
CYCLE = UUID("87654321-4321-8765-4321-876543218765")
IMPORT_V = uuid4()
MAPPING_V = uuid4()


def _v1_fact(**overrides: object) -> FinancialFact:
    base = {
        "subject": "某物流企业",
        "original_label": "营业收入",
        "period": Period(
            start=date(2026, 1, 1), end=date(2026, 1, 31),
            kind=PeriodKind.SINGLE_MONTH, label="2026-01",
        ),
        "semantics": TimeSemantics.FLOW,
        "unit": Unit(currency="CNY", scale="1"),
        "scope": ConsolidationScope.CONSOLIDATED,
        "standard": AccountingStandard.CAS,
        "source": SourceLocator(file_sha256=SHA, table="科目余额表", row="营业收入"),
        "value": Decimal("1000.00"),
    }
    base.update(overrides)
    return FinancialFact(**base)  # type: ignore[arg-type]


def _locator(**overrides: object) -> WorkbookLocator:
    base = {
        "file_sha256": SHA,
        "workbook": "2026-01 财务包.xlsx",
        "sheet": "科目余额表",
        "cell_or_range": "B12",
    }
    base.update(overrides)
    return WorkbookLocator(**base)  # type: ignore[arg-type]


def _internal_context(**overrides: object) -> FactContext:
    base = {
        "module": "internal",
        "enterprise_id": ENTERPRISE,
        "analysis_cycle_id": CYCLE,
        "scenario": Scenario.ACTUAL,
        "scenario_version": "actual-v1",
        "import_version_id": IMPORT_V,
        "mapping_version_id": MAPPING_V,
        "management_basis_version": "mb-2026.01",
    }
    base.update(overrides)
    return FactContext(**base)  # type: ignore[arg-type]


def _public_context(**overrides: object) -> FactContext:
    base = {
        "module": "public",
        "scenario": Scenario.ACTUAL,
        "scenario_version": "fy2025",
    }
    base.update(overrides)
    return FactContext(**base)  # type: ignore[arg-type]


def _internal_fact(**ctx_overrides: object) -> FinancialFactV2:
    return FinancialFactV2(
        fact=_v1_fact(), context=_internal_context(**ctx_overrides), provenance=_locator()
    )


# --- 身份完整性（internal 缺任一字段即拒绝） ---

def test_internal_context_valid() -> None:
    ctx = _internal_context()
    assert ctx.module == "internal"
    assert ctx.enterprise_id == ENTERPRISE


@pytest.mark.parametrize(
    "field",
    [
        "enterprise_id",
        "analysis_cycle_id",
        "import_version_id",
        "mapping_version_id",
        "management_basis_version",
    ],
)
def test_internal_context_missing_identity_rejected(field: str) -> None:
    with pytest.raises((ValidationError, ContractV2Violation)):
        _internal_context(**{field: None})


def test_internal_fact_missing_provenance_rejected() -> None:
    with pytest.raises((ValidationError, ContractV2Violation)):
        FinancialFactV2(fact=_v1_fact(), context=_internal_context(), provenance=None)


def test_public_context_valid_without_enterprise() -> None:
    ctx = _public_context()
    assert ctx.enterprise_id is None and ctx.analysis_cycle_id is None


def test_public_context_with_cycle_rejected() -> None:
    with pytest.raises((ValidationError, ContractV2Violation)):
        _public_context(analysis_cycle_id=CYCLE)


# --- WorkbookLocator ---

def test_locator_valid() -> None:
    assert _locator().cell_or_range == "B12"


@pytest.mark.parametrize("bad_sha", ["xyz", "A" * 64, "b" * 63, ""])
def test_locator_bad_sha_rejected(bad_sha: str) -> None:
    with pytest.raises((ValidationError, ContractV2Violation)):
        _locator(file_sha256=bad_sha)


@pytest.mark.parametrize("field", ["workbook", "sheet", "cell_or_range"])
def test_locator_missing_field_rejected(field: str) -> None:
    with pytest.raises((ValidationError, ContractV2Violation)):
        _locator(**{field: ""})


# --- float 金额拒绝（继承 V1 StrictDecimal 纪律） ---

def test_float_value_rejected() -> None:
    with pytest.raises(ValidationError):
        _v1_fact(value=1000.0)


def test_decimal_value_accepted() -> None:
    assert _v1_fact(value=Decimal("1000.00")).value == Decimal("1000.00")


# --- 比较规则（Step 4） ---

def _month_fact(year: int, month: int, **ctx_overrides: object) -> FinancialFactV2:
    start = date(year, month, 1)
    end = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
    from datetime import timedelta

    return FinancialFactV2(
        fact=_v1_fact(
            period=Period(
                start=start, end=end - timedelta(days=1),
                kind=PeriodKind.SINGLE_MONTH, label=f"{year}-{month:02d}",
            )
        ),
        context=_internal_context(**ctx_overrides),
        provenance=_locator(),
    )


def test_yoy_comparison_ok() -> None:
    a = _month_fact(2026, 1)
    b = _month_fact(2025, 1)
    assert_comparable_v2(a, b, comparison=ComparisonKind.YOY)


def test_mom_comparison_ok() -> None:
    assert_comparable_v2(_month_fact(2026, 2), _month_fact(2026, 1), comparison=ComparisonKind.MOM)


def test_actual_vs_budget_ok_same_version() -> None:
    a = _month_fact(2026, 1)
    b = _month_fact(2026, 1, scenario=Scenario.BUDGET)
    assert_comparable_v2(a, b, comparison=ComparisonKind.ACTUAL_VS_BUDGET)


def test_cross_enterprise_not_comparable() -> None:
    a = _month_fact(2026, 1)
    b = _month_fact(2025, 1, enterprise_id=uuid4())
    with pytest.raises(ContractV2Violation):
        assert_comparable_v2(a, b, comparison=ComparisonKind.YOY)


def test_cross_unit_not_comparable() -> None:
    a = _month_fact(2026, 1)
    b = FinancialFactV2(
        fact=_v1_fact(unit=Unit(currency="USD", scale="1")),
        context=_internal_context(),
        provenance=_locator(),
    )
    with pytest.raises(ContractV2Violation):
        assert_comparable_v2(a, b, comparison=ComparisonKind.YOY)


def test_cross_scope_not_comparable() -> None:
    a = _month_fact(2026, 1)
    b = FinancialFactV2(
        fact=_v1_fact(scope=ConsolidationScope.PARENT),
        context=_internal_context(),
        provenance=_locator(),
    )
    with pytest.raises(ContractV2Violation):
        assert_comparable_v2(a, b, comparison=ComparisonKind.YOY)


def test_budget_version_mismatch_not_comparable() -> None:
    a = _month_fact(2026, 1)
    b = _month_fact(2026, 1, scenario=Scenario.BUDGET, scenario_version="budget-v2")
    with pytest.raises(ContractV2Violation):
        assert_comparable_v2(a, b, comparison=ComparisonKind.ACTUAL_VS_BUDGET)


def test_yoy_scenario_mismatch_rejected() -> None:
    a = _month_fact(2026, 1)
    b = _month_fact(2025, 1, scenario=Scenario.BUDGET)
    with pytest.raises(ContractV2Violation):
        assert_comparable_v2(a, b, comparison=ComparisonKind.YOY)
