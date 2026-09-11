"""客观财报冻结快照的 ORM 模型与冻结/取回服务（U6/P08 切片一）。"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from flow_api.infrastructure.models.base import Base
from flow_api.infrastructure.models.canonical import CanonicalIdentityMixin
from flow_api.infrastructure.models.statement import (
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)

SCHEMA_VERSION = "objective.v1"
REPORT_TYPE = "objective_statement"


class ObjectiveReportSnapshot(CanonicalIdentityMixin, Base):
    """客观财报冻结快照：typed payload + 不可变（CHECK 阻止 UPDATE）。"""

    __tablename__ = "objective_report_snapshot"
    __table_args__ = (
        UniqueConstraint(
            "statement_report_id",
            "report_type",
            "version",
            name="uq_objective_report_snapshot_type_version",
        ),
        CheckConstraint("version > 0", name="ck_objective_report_version_positive"),
        CheckConstraint("length(payload_hash) = 64", name="ck_objective_payload_hash"),
        CheckConstraint(
            "report_type in ('objective_statement', 'operations_overview')",
            name="ck_objective_report_type",
        ),
    )

    statement_report_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("statement_report.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    report_type: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


def payload_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ObjectiveFreezeError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ObjectiveEligibility:
    """客观报告资格合同（U5/P06）：与主观 Finding 证据审批分离。

    - published：财报发布是用户批准的事实动作（B 链发布门禁：阻断项/警告确认）；
    - 来源指纹完整：source_ref 与 source_sha256 齐备，报告可溯源到原文；
    - 归一化行存在；未解析行不阻断，但作为不可用项说明如实入载荷。
    """

    __slots__ = (
        "published",
        "source_complete",
        "has_normalized_rows",
        "unresolved_names",
        "statement_types",
    )

    def __init__(
        self,
        *,
        published: bool,
        source_complete: bool,
        has_normalized_rows: bool,
        unresolved_names: list[str],
        statement_types: list[str],
    ) -> None:
        self.published = published
        self.source_complete = source_complete
        self.has_normalized_rows = has_normalized_rows
        self.unresolved_names = unresolved_names
        self.statement_types = statement_types

    @property
    def blockers(self) -> list[tuple[str, str]]:
        result: list[tuple[str, str]] = []
        if not self.published:
            result.append(
                ("report_not_published", "财报未发布：事实发布是冻结前必须的用户批准动作")
            )
        if not self.source_complete:
            result.append(
                ("source_incomplete", "来源身份不完整：缺少 source_ref 或 source_sha256")
            )
        if not self.has_normalized_rows:
            result.append(("objective_report_empty", "财报没有任何归一化行项目"))
        return result

    @property
    def eligible(self) -> bool:
        return not self.blockers


def evaluate_objective_eligibility(
    session: Session, report: StatementReport
) -> ObjectiveEligibility:
    """评估客观报告冻结资格；阻断项与不可用项均 typed 返回，不静默。"""

    normalized = session.scalars(
        select(StatementNormalizedItem).where(
            StatementNormalizedItem.report_id == report.id
        )
    ).all()
    unresolved = sorted({row.item_name for row in normalized if row.item_id is None})
    statement_types = sorted({row.statement_type for row in normalized})
    return ObjectiveEligibility(
        published=report.status == "published",
        source_complete=bool(report.source_ref) and bool(report.source_sha256),
        has_normalized_rows=bool(normalized),
        unresolved_names=unresolved,
        statement_types=statement_types,
    )


def freeze_objective_statement_report(
    session: Session, *, report_id: UUID
) -> ObjectiveReportSnapshot:
    """把已导入并归一化的客观财报冻结为 typed 载荷（幂等，同内容同版本）。

    冻结前执行客观资格合同（U5/P06）：财报未发布、来源指纹不完整或无归一化
    行即拒绝；主观 Finding 证据审批不在本链，也不被本链替代或放松。
    """

    report = session.get(StatementReport, report_id)
    if report is None:
        raise ObjectiveFreezeError("statement_report_not_found", "财报不存在")

    eligibility = evaluate_objective_eligibility(session, report)
    for code, message in eligibility.blockers:
        raise ObjectiveFreezeError(code, message)

    rows = (
        session.scalars(
            select(StatementNormalizedItem).where(
                StatementNormalizedItem.report_id == report_id
            )
        ).all()
    )
    raw_rows = (
        session.scalars(
            select(StatementLineItem).where(StatementLineItem.report_id == report_id)
        ).all()
    )

    if not rows and not raw_rows:
        raise ObjectiveFreezeError("objective_report_empty", "财报没有任何行项目，拒绝冻结空载荷")

    def row_payload(row: Any, *, normalized: bool) -> dict[str, Any]:
        base = {
            "item_name": row.item_name,
            "statement_type": row.statement_type,
        }
        if normalized:
            base.update(
                {
                    "item_id": row.item_id,
                    "value_end": str(row.value_end) if row.value_end is not None else None,
                    "value_begin": str(row.value_begin) if row.value_begin is not None else None,
                    "value_current": str(row.value_current)
                    if row.value_current is not None
                    else None,
                    "value_prior": str(row.value_prior) if row.value_prior is not None else None,
                    "trace": row.trace,
                }
            )
        else:
            base.update(
                {
                    "value_end": str(row.value_end) if row.value_end is not None else None,
                    "value_begin": str(row.value_begin) if row.value_begin is not None else None,
                    "value_current": str(row.value_current)
                    if row.value_current is not None
                    else None,
                    "value_prior": str(row.value_prior) if row.value_prior is not None else None,
                }
            )
        return base

    normalized_rows = sorted(rows, key=lambda r: (r.statement_type, r.created_at))
    raw_rows_sorted = sorted(raw_rows, key=lambda r: (r.statement_type, r.sort_order))
    payload = {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "source": {
            "report_id": str(report.id),
            "company_name": report.company_name,
            "stock_code": report.stock_code,
            "report_kind": report.report_kind,
            "period_label": report.period_label,
            "unit_note": report.unit_note,
            "source_ref": report.source_ref,
            "source_sha256": report.source_sha256,
        },
        "statements": _statements_payload(normalized_rows),
        "statements_raw": _statements_payload(raw_rows_sorted),
        "eligibility": {
            "published": eligibility.published,
            "unresolved_count": len(eligibility.unresolved_names),
            "unavailable_notes": [
                f"{len(eligibility.unresolved_names)} 行未映射到标准报表项目，"
                "如实保留原文，不参与指标计算"
            ]
            if eligibility.unresolved_names
            else [],
            "statement_types": eligibility.statement_types,
        },
        "frozen_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }

    digest = payload_hash(payload)
    latest = _latest_snapshot(session, report_id)
    if latest is not None and latest.payload_hash == digest:
        return latest  # 内容相同：幂等复用，不新建版本

    snapshot = ObjectiveReportSnapshot(
        statement_report_id=report.id,
        version=(latest.version + 1) if latest else 1,
        schema_version=SCHEMA_VERSION,
        report_type=REPORT_TYPE,
        payload=payload,
        payload_hash=digest,
    )
    session.add(snapshot)
    session.flush()
    return snapshot


def _statements_payload(rows: list[Any]) -> dict[str, list[dict[str, Any]]]:
    statements: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        entry = {"item": row.item_name}
        for column in ("value_end", "value_begin", "value_current", "value_prior"):
            value = getattr(row, column, None)
            entry[column] = None if value is None else str(value)
        statements.setdefault(row.statement_type, []).append(entry)
    return statements


def _latest_snapshot(session: Session, report_id: UUID) -> ObjectiveReportSnapshot | None:
    return session.scalar(
        select(ObjectiveReportSnapshot)
        .where(ObjectiveReportSnapshot.statement_report_id == report_id)
        .order_by(ObjectiveReportSnapshot.version.desc())
        .limit(1)
    )


__all__ = [
    "ObjectiveFreezeError",
    "ObjectiveReportSnapshot",
    "freeze_objective_statement_report",
    "payload_hash",
]
