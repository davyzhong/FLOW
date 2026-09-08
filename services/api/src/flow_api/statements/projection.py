"""主题快照投影（U3/原 P04 第一切片）。

把客观分析引擎的条目结果包装为携带快照身份与来源定位的不可变投影：
- 前端只格式化投影值，不重算（D02）；
- 补充行（比较基线等）必须与快照同身份，跨身份拼接抛 typed 错误；
- 投影构建后源行修改不影响已构建投影（frozen + 构建期取值）。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.analysis.objective import ObjectiveAnalysisService
from flow_api.infrastructure.models.statement import (
    StatementNormalizedItem,
    StatementReport,
)


class ProjectionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True, slots=True)
class SnapshotIdentity:
    report_id: str
    mapping_version: str


@dataclass(frozen=True, slots=True)
class ProvenancePoint:
    item_id: str
    statement_type: str
    item_name: str
    role: str
    source_sha256: str | None
    trace: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ProjectionEntry:
    entry_id: str
    name: str
    status: str
    value: str | None
    caliber: str | None
    provenance: tuple[ProvenancePoint, ...]


@dataclass(frozen=True, slots=True)
class TopicProjection:
    identity: SnapshotIdentity
    catalog_id: str
    unit_note: str
    entries: tuple[ProjectionEntry, ...]


def assert_same_identity(
    rows: list[StatementNormalizedItem], identity: SnapshotIdentity
) -> None:
    """跨身份拼接守卫：任何行不属于快照身份即拒绝（P04 验收第一条）。"""

    for row in rows:
        if str(row.report_id) != identity.report_id or (
            row.mapping_version != identity.mapping_version
        ):
            raise ProjectionError(
                "snapshot_identity_mismatch",
                f"行 {row.item_name}（report={row.report_id}, "
                f"mapping={row.mapping_version}）不属于快照身份 "
                f"({identity.report_id}, {identity.mapping_version})；跨身份拼接被拒绝",
            )


def build_topic_projection(
    session: Session,
    identity: SnapshotIdentity,
    *,
    baseline_rows: list[StatementNormalizedItem] | None = None,
) -> TopicProjection:
    """构建主题投影：同身份归一化行 → 引擎条目 + 来源定位（不可变）。"""

    report = session.get(StatementReport, UUID(identity.report_id))
    if report is None:
        raise ProjectionError("statement_report_not_found", "快照对应的财报不存在")

    rows = list(
        session.scalars(
            select(StatementNormalizedItem).where(
                StatementNormalizedItem.report_id == report.id,
                StatementNormalizedItem.mapping_version == identity.mapping_version,
            )
        )
    )
    if not rows:
        raise ProjectionError(
            "snapshot_not_normalized",
            f"报告 {report.id} 在映射版本 {identity.mapping_version} 下没有归一化行",
        )
    # 补充行（比较基线等）也必须同身份
    assert_same_identity(rows, identity)
    if baseline_rows:
        assert_same_identity(baseline_rows, identity)

    result = ObjectiveAnalysisService(session).analyze(
        report.id, mapping_version=identity.mapping_version
    )

    by_item: dict[str, list[StatementNormalizedItem]] = {}
    for row in rows:
        if row.item_id:
            by_item.setdefault(row.item_id, []).append(row)

    entries: list[ProjectionEntry] = []
    for entry in result.entries:
        provenance: list[ProvenancePoint] = []
        for ref in entry.refs:
            for row in by_item.get(ref, []):
                for column, role in (
                    ("value_end", "end"),
                    ("value_begin", "open"),
                    ("value_current", "cur"),
                    ("value_prior", "prev_yoy"),
                ):
                    if getattr(row, column) is not None:
                        provenance.append(
                            ProvenancePoint(
                                item_id=row.item_id or ref,
                                statement_type=row.statement_type,
                                item_name=row.item_name,
                                role=role,
                                source_sha256=report.source_sha256,
                                trace=row.trace,
                            )
                        )
                        break  # 每行只取其主角色定位
        entries.append(
            ProjectionEntry(
                entry_id=entry.entry_id,
                name=entry.name,
                status=str(entry.status),
                value=entry.value,
                caliber=entry.basis,
                provenance=tuple(provenance),
            )
        )
    return TopicProjection(
        identity=identity,
        catalog_id=result.catalog_id,
        unit_note=report.unit_note,
        entries=tuple(entries),
    )




# ---- 维度下钻粒度校验（P04：合计与明细相加约束，未披露维度拒绝） ----

# item_id → 其归一化明细子集的 item_id 契约（公开财报披露结构）。
# 合计行本身也作为明细存在时，从明细集中剔除自身。
DRILLDOWN_TAXONOMY: dict[str, dict[str, list[str]]] = {
    "合并资产负债表": {
        # 流动资产合计的全部归一化子项（调研 07/10 + 财会〔2018〕15 号格式）
        "bs.current_assets": [
            "bs.cash", "bs.notes_receivable", "bs.ar", "bs.inventory",
        ],
        # 资产总计 = 流动 + 非流动（两级合计均守恒）
        "bs.total_assets": ["bs.current_assets", "bs.noncurrent_assets"],
        "bs.current_liab": ["bs.ap", "bs.short_debt"],
        "bs.total_liab": ["bs.current_liab", "bs.noncurrent_liab"],
        # 权益总额 = 归母 + 非控制性权益（归母存在映射；非控制性权益行按披露原文匹配）
        "bs.equity": ["bs.attr_equity"],
    },
}

_UNDISCLOSED_PREFIXES = ("customer", "order", "supplier", "internal_budget", "channel")


def drilldown_children(
    session: Session,
    report_id: UUID,
    mapping_version: str,
    item_id: str,
    *,
    tolerance: Decimal | None = None,
) -> list[StatementNormalizedItem]:
    """合计行项目的维度下钻：返回归一化明细并做相加守恒校验。

    - item_id 在下钻分类中没有契约 → drilldown_not_disclosed（缺失不补造）；
    - 明细分项之和与合计的偏差超出容差 → drilldown_not_consistent；
    容差默认 0.01（与 Driver 对账一致）。
    """

    flat_taxonomy: dict[str, list[str]] = {}
    for sub in DRILLDOWN_TAXONOMY.values():
        flat_taxonomy.update(sub)
    taxonomy = flat_taxonomy.get(item_id)
    if taxonomy is None and any(item_id.startswith(pre) for pre in _UNDISCLOSED_PREFIXES):
        raise ProjectionError(
            "drilldown_not_disclosed",
            f"维度 {item_id} 在公开财报中未披露，不得由模型构造下钻",
        )
    if taxonomy is None:
        # 叶子科目（已映射、无下钻子项契约）：返回空明细，非错误
        return []
    child_ids = taxonomy
    tolerance = tolerance or Decimal("0.01")

    report = session.get(StatementReport, report_id)
    if report is None:
        raise ProjectionError("statement_report_not_found", "快照对应的财报不存在")
    rows = list(
        session.scalars(
            select(StatementNormalizedItem).where(
                StatementNormalizedItem.report_id == report_id,
                StatementNormalizedItem.mapping_version == mapping_version,
            )
        )
    )
    by_id: dict[str, StatementNormalizedItem] = {}
    for row in rows:
        if row.item_id and row.item_id not in by_id:
            by_id[row.item_id] = row

    def _row_value(row: StatementNormalizedItem | None) -> Decimal | None:
        if row is None:
            return None
        return row.value_current or row.value_end or row.value_prior or row.value_begin

    present: list[StatementNormalizedItem] = []
    total_row = by_id.get(item_id)
    total = _row_value(total_row)
    if total is None:
        raise ProjectionError(
            "drilldown_not_disclosed", f"合计行 {item_id} 缺少数值，无法下钻"
        )
    children_sum = Decimal("0")
    for child_id in child_ids:
        row: StatementNormalizedItem | None = by_id.get(child_id)
        value = _row_value(row)
        if value is not None and row is not None:
            present.append(row)
            children_sum += value
    gap = abs(total - children_sum)
    if gap > tolerance:
        raise ProjectionError(
            "drilldown_not_consistent",
            f"下钻明细之和 {children_sum} 与合计 {total} 偏差 {gap} 超出容差；"
            "不得在不守恒的明细上继续分析",
        )
    return present


__all__ = [
    "ProjectionEntry",
    "ProjectionError",
    "ProvenancePoint",
    "SnapshotIdentity",
    "TopicProjection",
    "assert_same_identity",
    "build_topic_projection",
]
