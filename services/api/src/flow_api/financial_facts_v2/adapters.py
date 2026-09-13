"""Financial Facts Contract V2 显式适配器（S01 Task 4）。

规格：docs/40_specs/financial-facts/financial-facts-contract-v2.md（approved）。

- `from_public_v1`：V1 公开事实无损适配为 V2（public profile，保留 page/table/row 定位）；
- `from_canonical_row`：canonical 内部事实行适配为 V2（internal profile）；
  context/provenance 必须由持久化 join 得到并完整冻结后传入，本模块不从单条
  canonical row 猜测身份，也不为缺失字段制造默认值；
- 不提供任何会丢字段的通用 V2→V1 反向适配（规格 §5 不变量 2）。
"""

from __future__ import annotations

import calendar
from datetime import date
from typing import Any

from flow_api.financial_facts_v2.models import (
    ContractV2Violation,
    FactContext,
    FinancialFactV2,
    Scenario,
    WorkbookLocator,
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
from flow_api.statements.models import FrozenModel


class CanonicalBasis(FrozenModel):
    """canonical 行的批次级口径（来自持久化配置，不从单行猜测）。"""

    unit: Unit
    scope: ConsolidationScope
    standard: AccountingStandard
    semantics: TimeSemantics


def from_public_v1(fact: FinancialFact, *, scenario_version: str) -> FinancialFactV2:
    """V1 公开披露事实 → V2 public 事实（无损：原 fact 对象整体保留）。

    scenario_version 必须由调用方显式给出（如 as-reported / restated 批次标签），
    不推断、不默认。
    """

    context = FactContext(
        module="public",
        scenario=Scenario.ACTUAL,
        scenario_version=scenario_version,
    )
    return FinancialFactV2(fact=fact, context=context, provenance=None)


def _require_joined(row: Any, attrs: tuple[str, ...]) -> None:
    missing = [name for name in attrs if getattr(row, name, None) is None]
    if missing:
        raise ContractV2Violation(
            f"canonical 行缺少持久化 join 维度：{', '.join(missing)}（不从单行猜测身份）"
        )


def from_canonical_row(
    row: Any, *, context: FactContext, provenance: WorkbookLocator, basis: CanonicalBasis
) -> FinancialFactV2:
    """canonical 内部事实行（如 FactFinancialActual，已 join 维度）→ V2 internal 事实。

    - context 必须是完整冻结的 internal FactContext（模型层已强校验，此处再断言）；
    - provenance 必须是完整 WorkbookLocator（含 64 位 SHA）；
    - 期间由 dim_period 的 year/month 构造 single_month 区间。
    """

    if context.module != "internal":
        raise ContractV2Violation("canonical 行只能适配为 internal 事实")
    if (
        context.enterprise_id is None
        or context.analysis_cycle_id is None
        or context.import_version_id is None
        or context.mapping_version_id is None
        or context.management_basis_version is None
    ):
        raise ContractV2Violation("internal context 身份不完整（禁止制造默认值）")

    _require_joined(row, ("period", "organization", "management_account"))

    year, month = row.period.year, row.period.month
    last_day = calendar.monthrange(year, month)[1]
    period = Period(
        start=date(year, month, 1),
        end=date(year, month, last_day),
        kind=PeriodKind.SINGLE_MONTH,
        label=f"{year}-{month:02d}",
    )
    fact = FinancialFact(
        subject=row.organization.name,
        original_label=row.management_account.name,
        period=period,
        semantics=basis.semantics,
        unit=basis.unit,
        scope=basis.scope,
        standard=basis.standard,
        source=SourceLocator(
            file_sha256=provenance.file_sha256,
            table=provenance.sheet,
            row=provenance.cell_or_range,
        ),
        value=row.amount,
    )
    return FinancialFactV2(fact=fact, context=context, provenance=provenance)


__all__ = ["CanonicalBasis", "from_canonical_row", "from_public_v1"]
