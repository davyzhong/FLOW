"""operations 家族与 §7 四阶段 ABI 的绑定：冻结资源校验器注册。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from flow_api.publication.four_stage import (
    PublicationFreezeConflict,
    PublicationNotFound,
    VerifiedResource,
    register_resource_verifier,
)


def _verify_operations_snapshot(session: Session, resource_id: UUID) -> VerifiedResource:
    from flow_api.publishing.objective_freeze import ObjectiveReportSnapshot

    snapshot = session.get(ObjectiveReportSnapshot, resource_id)
    if snapshot is None or snapshot.report_type != "operations_overview":
        raise PublicationNotFound(f"operations snapshot does not exist: {resource_id}")
    payload = snapshot.payload
    if not isinstance(payload, dict) or not payload:
        raise PublicationFreezeConflict("operations snapshot has no frozen payload")
    return VerifiedResource(
        canonical_payload=payload,
        scope="public",
        enterprise_id=None,
    )


register_resource_verifier("operations_snapshot", _verify_operations_snapshot)
