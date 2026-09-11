"""经营轨六主题概览冻结（O3 slice-2）。

复用 U5 客观资格合同（published 批准 + 来源指纹 + 归一化行）——资格不达标
不得冻结；复用 ObjectiveReportSnapshot 表（report_type=operations_overview，
版本序列按类型独立）；同内容幂等复用，不新建版本。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.statement import StatementReport
from flow_api.operations.engine import OperationsOverview, build_operations_overview
from flow_api.publishing.objective_freeze import (
    ObjectiveFreezeError,
    ObjectiveReportSnapshot,
    evaluate_objective_eligibility,
    payload_hash,
)

SCHEMA_VERSION = "operations.v1"
REPORT_TYPE = "operations_overview"


def _latest_overview_snapshot(
    session: Session, report_id: UUID
) -> ObjectiveReportSnapshot | None:
    return session.scalar(
        select(ObjectiveReportSnapshot)
        .where(
            ObjectiveReportSnapshot.statement_report_id == report_id,
            ObjectiveReportSnapshot.report_type == REPORT_TYPE,
        )
        .order_by(ObjectiveReportSnapshot.version.desc())
        .limit(1)
    )


def freeze_operations_overview(
    session: Any, *, report_id: UUID
) -> ObjectiveReportSnapshot:
    """六主题概览冻结：先过 U5 客观资格合同，再幂等落 typed 快照。"""

    report = session.get(StatementReport, report_id)
    if report is None:
        raise ObjectiveFreezeError("statement_report_not_found", "财报不存在")

    eligibility = evaluate_objective_eligibility(session, report)
    for code, message in eligibility.blockers:
        raise ObjectiveFreezeError(code, message)

    overview: OperationsOverview = build_operations_overview(
        session, report_id=report_id
    )
    content: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "overview": overview.model_dump(),
    }

    latest = _latest_overview_snapshot(session, report_id)
    if latest is not None:
        latest_content = {
            key: value for key, value in latest.payload.items() if key != "frozen_at"
        }
        if latest_content == content:
            return latest  # 冻结时间不是业务内容；内容相同即幂等复用

    payload = {
        **content,
        "frozen_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    digest = payload_hash(payload)

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


def load_operations_overview_payload(snapshot: ObjectiveReportSnapshot) -> dict[str, Any]:
    return snapshot.payload


__all__ = [
    "REPORT_TYPE",
    "freeze_operations_overview",
    "load_operations_overview_payload",
]
