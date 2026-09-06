"""统一财务事实契约（A02）的参考实现。

规则见 docs/superpowers/specs/financial-facts-contract.md；
契约测试见 tests/statements/test_fact_contract.py。
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import ConfigDict, Field, model_validator

from flow_api.statements.models import FrozenModel, StrictDecimal

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ContractViolation(ValueError):
    """财务事实契约违规。"""


class FactConflictError(ContractViolation):
    """范围/币种/准则/语义冲突，拒绝合并。"""


class PeriodMismatchError(ContractViolation):
    """期间不可比较（单季/累计误混等）。"""


class PeriodKind(StrEnum):
    SINGLE_MONTH = "single_month"
    SINGLE_QUARTER = "single_quarter"
    YTD = "ytd"
    ANNUAL = "annual"
    POINT = "point"


class TimeSemantics(StrEnum):
    FLOW = "flow"
    STOCK = "stock"


class ConsolidationScope(StrEnum):
    CONSOLIDATED = "consolidated"
    PARENT = "parent"
    SEGMENT = "segment"
    OTHER = "other"


class AccountingStandard(StrEnum):
    CAS = "CAS"
    IFRS = "IFRS"
    US_GAAP = "US_GAAP"


class MissingReason(StrEnum):
    NOT_DISCLOSED = "not_disclosed"
    NOT_APPLICABLE = "not_applicable"
    PARSE_UNRESOLVED = "parse_unresolved"
    REDACTED = "redacted"


_SCALE_FACTORS = {
    "1": Decimal(1),
    "1e3": Decimal(1000),
    "1e6": Decimal(1_000_000),
}

UnitScale = Annotated[str, Field(pattern=r"^(1|1e3|1e6)$")]


class Period(FrozenModel):
    start: date
    end: date
    kind: PeriodKind
    label: str = Field(min_length=1)

    @model_validator(mode="after")
    def _check_span(self) -> Period:
        if self.kind == PeriodKind.POINT:
            if self.start != self.end:
                raise ContractViolation("point 期间必须是单一日期")
        elif self.start >= self.end:
            raise ContractViolation(f"{self.kind} 期间必须有真实跨度（start < end）")
        if self.kind == PeriodKind.YTD and (self.start.month, self.start.day) != (1, 1):
            raise ContractViolation("ytd 期间起点必须是财年首日")
        return self


class Unit(FrozenModel):
    currency: str = Field(min_length=3, max_length=3)
    scale: UnitScale = "1"


class SourceLocator(FrozenModel):
    file_sha256: str
    page: int | None = Field(default=None, ge=1)
    table: str | None = None
    row: str | None = None

    @model_validator(mode="after")
    def _check_locator(self) -> SourceLocator:
        if not SHA256_PATTERN.fullmatch(self.file_sha256):
            raise ContractViolation("来源必须携带 64 位小写 SHA-256 文件哈希")
        if self.page is None and self.table is None and self.row is None:
            raise ContractViolation("来源必须在页/表/行中至少提供一项定位")
        return self


class FinancialFact(FrozenModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    subject: str = Field(min_length=1)
    original_label: str = Field(min_length=1)
    period: Period
    semantics: TimeSemantics
    unit: Unit
    scope: ConsolidationScope
    standard: AccountingStandard
    source: SourceLocator
    value: StrictDecimal | None = None
    missing_reason: MissingReason | None = None
    restated: bool = False
    caliber_note: str | None = None

    @model_validator(mode="after")
    def _check_fact(self) -> FinancialFact:
        if self.semantics == TimeSemantics.FLOW and self.period.kind == PeriodKind.POINT:
            raise ContractViolation("flow 事实不能使用 point 期间")
        if self.semantics == TimeSemantics.STOCK and self.period.start != self.period.end:
            raise ContractViolation("stock 事实必须是单一日期")
        if self.value is None and self.missing_reason is None:
            raise ContractViolation("value 缺失必须携带 missing_reason（空值不等于零）")
        if self.value is not None and self.missing_reason is not None:
            raise ContractViolation("value 非空时不得携带 missing_reason")
        return self


def to_base(value: Decimal, from_scale: UnitScale, to_scale: UnitScale) -> Decimal:
    """以 10 幂缩放，Decimal 下可逆：to_base(to_base(v, a, b), b, a) == v。"""

    factor = _SCALE_FACTORS[from_scale]
    inverse = _SCALE_FACTORS[to_scale]
    return value * factor / inverse


def _same_basis(a: FinancialFact, b: FinancialFact) -> None:
    if a.scope != b.scope:
        raise FactConflictError(f"合并范围冲突：{a.scope} vs {b.scope}")
    if a.standard != b.standard:
        raise FactConflictError(f"准则冲突：{a.standard} vs {b.standard}")
    if a.unit.currency != b.unit.currency:
        raise FactConflictError(f"币种冲突：{a.unit.currency} vs {b.unit.currency}")
    if a.semantics != b.semantics:
        raise FactConflictError(f"时间语义冲突：{a.semantics} vs {b.semantics}")
    if a.subject != b.subject or a.original_label != b.original_label:
        raise FactConflictError("主体或项目不一致，拒绝合并")


def assert_comparable(a: FinancialFact, b: FinancialFact) -> None:
    """允许比较（求差/求比）的前提：同基线 + 同期间种类。"""

    _same_basis(a, b)
    if a.period.kind != b.period.kind:
        raise PeriodMismatchError(
            f"期间种类不一致：{a.period.kind} vs {b.period.kind}（单季/累计不可误混）"
        )


def merge_flow(facts: tuple[FinancialFact, ...]) -> Decimal | None:
    """同 kind 的 flow 事实加总；缺失传染（任一 None 则结果 None）；stock 拒绝相加。"""

    if not facts:
        raise ContractViolation("空事实集不可合并")
    head = facts[0]
    if head.semantics == TimeSemantics.STOCK:
        raise FactConflictError("时点余额跨期相加没有财务含义")
    total: Decimal | None = Decimal(0)
    for fact in facts:
        _same_basis(head, fact)
        if fact.period.kind != head.period.kind:
            raise PeriodMismatchError("不同期间种类的 flow 不可相加")
        if fact.value is None:
            total = None
        elif total is not None:
            total += to_base(fact.value, fact.unit.scale, head.unit.scale)
    return total


__all__ = [
    "AccountingStandard",
    "ConsolidationScope",
    "ContractViolation",
    "FactConflictError",
    "FinancialFact",
    "MissingReason",
    "Period",
    "PeriodKind",
    "PeriodMismatchError",
    "SourceLocator",
    "TimeSemantics",
    "Unit",
    "UnitScale",
    "assert_comparable",
    "merge_flow",
    "to_base",
]
