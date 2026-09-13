"""Financial Facts Contract V2 显式适配器测试（S01 Task 4，TDD 红灯先行）。

规格：docs/40_specs/financial-facts/financial-facts-contract-v2.md（approved）。
要点：V1 公开事实无损适配；canonical 内部事实身份缺失即失败、禁止制造默认值；
不提供会丢字段的通用 V2→V1。
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from flow_api.financial_facts_v2.adapters import (
    CanonicalBasis,
    from_canonical_row,
    from_public_v1,
)
from flow_api.financial_facts_v2.models import (
    ContractV2Violation,
    FactContext,
    Scenario,
    WorkbookLocator,
)
from flow_api.infrastructure.models.canonical import (
    FactFinancialActual,
    ManagementAccount,
    Organization,
)
from flow_api.infrastructure.models.canonical import Period as DimPeriod
from flow_api.statements.fact_contract import (
    AccountingStandard,
    ConsolidationScope,
    FinancialFact,
    MissingReason,
    Period,
    PeriodKind,
    SourceLocator,
    TimeSemantics,
    Unit,
)

SHA = "c" * 64
ENTERPRISE = UUID("12345678-1234-5678-1234-567812345678")
CYCLE = UUID("87654321-4321-8765-4321-876543218765")


def _public_fact(**overrides: object) -> FinancialFact:
    base = {
        "subject": "顺丰控股 002352.SZ",
        "original_label": "营业收入",
        "period": Period(
            start=date(2026, 1, 1), end=date(2026, 3, 31),
            kind=PeriodKind.SINGLE_QUARTER, label="2026Q1",
        ),
        "semantics": TimeSemantics.FLOW,
        "unit": Unit(currency="CNY", scale="1e3"),
        "scope": ConsolidationScope.CONSOLIDATED,
        "standard": AccountingStandard.CAS,
        "source": SourceLocator(file_sha256=SHA, page=5, table="合并利润表", row="营业收入"),
        "value": Decimal("74142121"),
    }
    base.update(overrides)
    return FinancialFact(**base)  # type: ignore[arg-type]


def _internal_context(**overrides: object) -> FactContext:
    base = {
        "module": "internal",
        "enterprise_id": ENTERPRISE,
        "analysis_cycle_id": CYCLE,
        "scenario": Scenario.ACTUAL,
        "scenario_version": "actual-v1",
        "import_version_id": uuid4(),
        "mapping_version_id": uuid4(),
        "management_basis_version": "mb-2026.01",
    }
    base.update(overrides)
    return FactContext(**base)  # type: ignore[arg-type]


def _locator(**overrides: object) -> WorkbookLocator:
    base = {
        "file_sha256": SHA,
        "workbook": "2026-01 财务包.xlsx",
        "sheet": "科目余额表",
        "cell_or_range": "B12",
    }
    base.update(overrides)
    return WorkbookLocator(**base)  # type: ignore[arg-type]


def _basis(**overrides: object) -> CanonicalBasis:
    base = {
        "unit": Unit(currency="CNY", scale="1"),
        "scope": ConsolidationScope.CONSOLIDATED,
        "standard": AccountingStandard.CAS,
        "semantics": TimeSemantics.FLOW,
    }
    base.update(overrides)
    return CanonicalBasis(**base)  # type: ignore[arg-type]


def _canonical_row() -> FactFinancialActual:
    return FactFinancialActual(
        amount=Decimal("123456.78"),
        period=DimPeriod(month_key=202601, year=2026, quarter=1, month=1),
        organization=Organization(code="HQ", name="某物流集团", level="group"),
        management_account=ManagementAccount(
            code="6001", name="主营业务收入", category="revenue"
        ),
    )


# --- Step 1：V1 公开事实无损适配 ---

def test_from_public_v1_lossless() -> None:
    fact = _public_fact()
    adapted = from_public_v1(fact, scenario_version="fy2026q1-as-reported")
    assert adapted.fact == fact  # frozen 模型逐字段相等 = 无损
    assert adapted.context.module == "public"
    assert adapted.context.scenario == Scenario.ACTUAL
    assert adapted.context.enterprise_id is None
    assert adapted.context.analysis_cycle_id is None
    assert adapted.provenance is None  # public 保留 V1 page/table/row，不伪造 workbook 定位
    assert adapted.fact.source.page == 5
    assert adapted.fact.restated is False


def test_from_public_v1_keeps_missing_and_restated() -> None:
    fact = _public_fact(value=None, missing_reason=MissingReason.NOT_DISCLOSED, restated=True)
    adapted = from_public_v1(fact, scenario_version="fy2026q1-restated")
    assert adapted.fact.value is None
    assert adapted.fact.missing_reason == MissingReason.NOT_DISCLOSED
    assert adapted.fact.restated is True


def test_from_public_v1_requires_explicit_scenario_version() -> None:
    with pytest.raises(TypeError):
        from_public_v1(_public_fact())  # type: ignore[call-arg]


# --- Step 2：canonical 适配的身份完整性（缺即失败，禁止默认值） ---

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
def test_canonical_context_missing_identity_fails(field: str) -> None:
    with pytest.raises((ValidationError, ContractV2Violation)):
        _internal_context(**{field: None})


@pytest.mark.parametrize("field", ["workbook", "sheet", "cell_or_range"])
def test_canonical_provenance_missing_field_fails(field: str) -> None:
    with pytest.raises((ValidationError, ContractV2Violation)):
        _locator(**{field: ""})


def test_canonical_provenance_bad_sha_fails() -> None:
    with pytest.raises((ValidationError, ContractV2Violation)):
        _locator(file_sha256="not-a-sha")


def test_from_canonical_row_rejects_public_context() -> None:
    public_ctx = FactContext(
        module="public", scenario=Scenario.ACTUAL, scenario_version="fy2025"
    )
    with pytest.raises(ContractV2Violation):
        from_canonical_row(
            _canonical_row(), context=public_ctx, provenance=_locator(), basis=_basis()
        )


# --- Step 3：canonical → V2 正向适配 ---

def test_from_canonical_row_builds_internal_fact() -> None:
    adapted = from_canonical_row(
        _canonical_row(), context=_internal_context(), provenance=_locator(), basis=_basis()
    )
    assert adapted.context.module == "internal"
    assert adapted.fact.subject == "某物流集团"
    assert adapted.fact.original_label == "主营业务收入"
    assert adapted.fact.value == Decimal("123456.78")
    assert adapted.fact.period.kind == PeriodKind.SINGLE_MONTH
    assert adapted.fact.period.start == date(2026, 1, 1)
    assert adapted.fact.period.end == date(2026, 1, 31)
    assert adapted.fact.unit.currency == "CNY"
    assert adapted.fact.source.file_sha256 == SHA
    assert adapted.fact.source.table == "科目余额表"
    assert adapted.fact.source.row == "B12"


def test_from_canonical_row_requires_joined_dimensions() -> None:
    row = FactFinancialActual(amount=Decimal("1"))  # 未 join period/organization/account
    with pytest.raises(ContractV2Violation):
        from_canonical_row(
            row, context=_internal_context(), provenance=_locator(), basis=_basis()
        )


# --- 不提供有损的通用 V2→V1 ---

def test_no_generic_v2_to_v1_adapter() -> None:
    import flow_api.financial_facts_v2.adapters as adapters

    assert not hasattr(adapters, "to_v1")
    assert not hasattr(adapters, "to_public_v1")
