"""企业空间与月度分析周期（S01 Task 5）。

规格：docs/40_specs/financial-facts/financial-facts-contract-v2.md（approved）§4。

- ORM：Enterprise / AnalysisCycle；
- AnalysisBatch 合法组合矩阵的 Python 侧重复校验（数据库单一 CHECK 为最终防线，
  见 intake.py 的 ck_analysis_batch_module_combo 与迁移 0025）。
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from flow_api.financial_facts_v2.models import ContractV2Violation
from flow_api.infrastructure.models.base import Base
from flow_api.infrastructure.models.canonical import CanonicalIdentityMixin
from flow_api.infrastructure.models.intake import AnalysisBatch


class Enterprise(CanonicalIdentityMixin, Base):
    __tablename__ = "enterprise"

    code: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class AnalysisCycle(CanonicalIdentityMixin, Base):
    __tablename__ = "analysis_cycle"
    __table_args__ = (
        UniqueConstraint(
            "enterprise_id", "period_key", name="uq_analysis_cycle_enterprise_period"
        ),
        CheckConstraint(
            r"period_key ~ '^\d{4}-(0[1-9]|1[0-2])$'", name="ck_analysis_cycle_period_key"
        ),
        CheckConstraint(
            "status in ('open', 'frozen', 'closed')", name="ck_analysis_cycle_status"
        ),
    )

    enterprise_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("enterprise.id", ondelete="RESTRICT"),
        nullable=False,
    )
    period_key: Mapped[str] = mapped_column(String(7), nullable=False)  # 例如 2026-01
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")


# 合法组合：(module_kind, fact_context_version, 是否携带 cycle)
LEGAL_BATCH_COMBINATIONS = frozenset(
    {
        ("legacy", 1, False),
        ("public", 1, False),
        ("public", 2, False),
        ("internal", 2, True),
    }
)


def assert_legal_batch_combination(
    module_kind: str, fact_context_version: int, analysis_cycle_id: UUID | None
) -> None:
    """创建服务侧的重复校验；数据库 CHECK 为最终防线。"""

    key = (module_kind, fact_context_version, analysis_cycle_id is not None)
    if key not in LEGAL_BATCH_COMBINATIONS:
        raise ContractV2Violation(
            "非法批次组合："
            f"module_kind={module_kind!r}, fact_context_version={fact_context_version}, "
            f"cycle={'NOT NULL' if analysis_cycle_id is not None else 'NULL'}；"
            "仅允许 legacy/1/无 cycle、public/1|2/无 cycle、internal/2/有 cycle"
        )


def new_analysis_batch(
    *,
    name: str,
    module_kind: str,
    fact_context_version: int,
    analysis_cycle_id: UUID | None = None,
    description: str | None = None,
) -> AnalysisBatch:
    """内部创建入口：先经 Python 侧校验，再构造 ORM 对象（不落库，由调用方 add/commit）。"""

    assert_legal_batch_combination(module_kind, fact_context_version, analysis_cycle_id)
    return AnalysisBatch(
        name=name,
        description=description,
        module_kind=module_kind,
        fact_context_version=fact_context_version,
        analysis_cycle_id=analysis_cycle_id,
    )


__all__ = [
    "AnalysisCycle",
    "Enterprise",
    "LEGAL_BATCH_COMBINATIONS",
    "assert_legal_batch_combination",
    "new_analysis_batch",
]
