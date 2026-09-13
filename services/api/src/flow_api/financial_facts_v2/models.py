"""Financial Facts Contract V2 纯领域模型（S01 Task 3）。

规格：docs/40_specs/financial-facts/financial-facts-contract-v2.md（approved）。

V2 是 V1 合同（flow_api.statements.fact_contract）的向后兼容扩展：
- V1 全部不变量原样继承（Decimal 禁 float、None≠0、缺失传染、scope/standard 不隐式合并）；
- 新增 scenario/version、enterprise/cycle、组织范围外的来源定位 WorkbookLocator、
  import/mapping/management-basis 三版本与比较期间身份；
- 合法组合：public 不带 enterprise/cycle；internal 必须身份完整。
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from flow_api.statements.fact_contract import (
    ContractViolation,
    FinancialFact,
    assert_comparable,
)
from flow_api.statements.models import FrozenModel

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ContractV2Violation(ValueError):
    """Financial Facts Contract V2 违规。"""


class Scenario(StrEnum):
    ACTUAL = "actual"
    BUDGET = "budget"
    FORECAST = "forecast"


class ComparisonKind(StrEnum):
    YOY = "yoy"  # 同比
    MOM = "mom"  # 环比
    ACTUAL_VS_BUDGET = "actual_vs_budget"  # 实际 vs 预算


class WorkbookLocator(FrozenModel):
    """内部 Excel 来源定位：64 位 SHA + workbook/sheet/cell-or-range（全部必填）。"""

    file_sha256: str
    workbook: str = Field(min_length=1)
    sheet: str = Field(min_length=1)
    cell_or_range: str = Field(min_length=1)

    @model_validator(mode="after")
    def _check_sha(self) -> WorkbookLocator:
        if not SHA256_PATTERN.fullmatch(self.file_sha256):
            raise ContractV2Violation("来源必须携带 64 位小写 SHA-256 文件哈希")
        return self


class FactContext(FrozenModel):
    """V2 事实身份上下文；internal 必须完整，public 不带企业/周期。"""

    module: Literal["public", "internal"]
    enterprise_id: UUID | None = None
    analysis_cycle_id: UUID | None = None
    scenario: Scenario
    scenario_version: str = Field(min_length=1)
    import_version_id: UUID | None = None
    mapping_version_id: UUID | None = None
    management_basis_version: str | None = None

    @model_validator(mode="after")
    def _check_combination(self) -> FactContext:
        if self.module == "internal":
            missing = [
                name
                for name, value in (
                    ("enterprise_id", self.enterprise_id),
                    ("analysis_cycle_id", self.analysis_cycle_id),
                    ("import_version_id", self.import_version_id),
                    ("mapping_version_id", self.mapping_version_id),
                    ("management_basis_version", self.management_basis_version),
                )
                if value is None
            ]
            if missing:
                raise ContractV2Violation(
                    f"internal 事实身份不完整，缺失：{', '.join(missing)}（禁止制造默认值）"
                )
        else:  # public
            if self.enterprise_id is not None or self.analysis_cycle_id is not None:
                raise ContractV2Violation("public 事实不得携带 enterprise_id/analysis_cycle_id")
        return self


class FinancialFactV2(FrozenModel):
    """V2 财务事实 = V1 事实 + V2 身份上下文 + 内部来源定位。"""

    fact: FinancialFact
    context: FactContext
    provenance: WorkbookLocator | None = None

    @model_validator(mode="after")
    def _check_provenance(self) -> FinancialFactV2:
        if self.context.module == "internal" and self.provenance is None:
            raise ContractV2Violation("internal 事实必须携带 WorkbookLocator 来源定位")
        return self


def _require_complete_identity(fact: FinancialFactV2) -> None:
    """比较前提：两侧均为完整 V2 身份（构造校验之外再显式断言，防止绕过）。"""

    ctx = fact.context
    if ctx.module == "internal" and (
        fact.provenance is None
        or ctx.enterprise_id is None
        or ctx.analysis_cycle_id is None
        or ctx.import_version_id is None
        or ctx.mapping_version_id is None
        or ctx.management_basis_version is None
    ):
        raise ContractV2Violation("比较要求两个完整 V2 身份，internal 事实身份不完整")


def assert_comparable_v2(
    a: FinancialFactV2, b: FinancialFactV2, *, comparison: ComparisonKind
) -> None:
    """V2 比较前提：两个完整身份 + 同企业 + V1 基线 + 比较类型规则。

    - 同比/环比：同 scenario 且同 scenario_version；
    - 实际 vs 预算：scenario 必须一 actual 一 budget，且 scenario_version（预算版本）一致；
    - 跨企业、单位、范围、准则、语义或期间种类一律拒绝（委托 V1 assert_comparable）。
    """

    _require_complete_identity(a)
    _require_complete_identity(b)
    if a.context.enterprise_id != b.context.enterprise_id:
        raise ContractV2Violation(
            f"跨企业不可比较：{a.context.enterprise_id} vs {b.context.enterprise_id}"
        )
    try:
        assert_comparable(a.fact, b.fact)
    except ContractViolation as exc:
        raise ContractV2Violation(f"V1 基线不可比较：{exc}") from exc

    if comparison in (ComparisonKind.YOY, ComparisonKind.MOM):
        if a.context.scenario != b.context.scenario:
            raise ContractV2Violation(
                f"同比/环比要求同情景：{a.context.scenario} vs {b.context.scenario}"
            )
        if a.context.scenario_version != b.context.scenario_version:
            raise ContractV2Violation("同比/环比要求同情景版本")
    elif comparison == ComparisonKind.ACTUAL_VS_BUDGET:
        pair = {a.context.scenario, b.context.scenario}
        if pair != {Scenario.ACTUAL, Scenario.BUDGET}:
            raise ContractV2Violation(
                f"实际预算比较要求 actual 与 budget 配对，实际为 {pair}"
            )
        if a.context.scenario_version != b.context.scenario_version:
            raise ContractV2Violation(
                f"预算版本不一致不可比较：{a.context.scenario_version} vs "
                f"{b.context.scenario_version}"
            )


__all__ = [
    "ComparisonKind",
    "ContractV2Violation",
    "FactContext",
    "FinancialFactV2",
    "Scenario",
    "WorkbookLocator",
    "assert_comparable_v2",
]
