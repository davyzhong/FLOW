from __future__ import annotations

import uuid
from typing import Any

from httpx import ASGITransport, AsyncClient
from integration.analysis_run_support import (
    _intake_session_fixture as _intake_session_fixture,  # noqa: F401
)
from integration.analysis_run_support import (
    _metric_session_fixture as _metric_session_fixture,  # noqa: F401
)
from integration.analysis_run_support import (
    analysis_session_fixture as _analysis_session_fixture,  # noqa: F401
)
from integration.analysis_run_support import publish_analysis_run
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.api.routes.investigations import get_investigation_session
from flow_api.infrastructure.models.analytics import Finding
from flow_api.main import create_app


def _override(session: Session) -> Any:
    def _factory() -> Any:
        yield session

    return _factory


async def test_investigation_api_full_review_flow(analysis_session: Session) -> None:
    run = publish_analysis_run(analysis_session)
    finding = analysis_session.scalars(
        select(Finding).order_by(Finding.total_score.desc())
    ).first()
    assert finding is not None and finding.analysis_run_id is not None

    app = create_app()
    app.dependency_overrides[get_investigation_session] = _override(analysis_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing = await client.get(f"/api/v1/investigations/{uuid.uuid4()}")
        assert missing.status_code == 404
        assert missing.json()["detail"]["code"] == "investigation_not_found"

        mismatched = await client.get(
            f"/api/v1/investigations/{finding.id}",
            params={"analysis_run_id": str(uuid.uuid4())},
        )
        assert mismatched.status_code == 409
        assert mismatched.json()["detail"]["code"] == "investigation_identity_mismatch"

        context = await client.get(
            f"/api/v1/investigations/{finding.id}",
            params={
                "batch_id": str(run.metric_snapshot.batch_id),
                "metric_snapshot_id": str(run.metric_snapshot_id),
                "analysis_run_id": str(run.id),
            },
        )
        assert context.status_code == 200
        payload = context.json()
        assert payload["identity"]["analysis_run_id"] == str(run.id)
        assert payload["metric"]["engine_version"] == "flow-analysis/1"
        assert payload["metric"]["formula"]
        assert len(payload["evidence"]) == 5
        assert len(payload["drivers"]) >= 1
        assert "conclusion_incomplete" in payload["eligibility_blockers"]
        assert len(payload["source_records"]) >= 1
        assert payload["source_records"][0]["source_row"] >= 1
        finding_id = payload["identity"]["finding_id"]
        evidence_id = payload["evidence"][0]["evidence_id"]

        rejected = await client.post(
            f"/api/v1/investigations/{finding_id}/evidence/{evidence_id}/decision",
            json={"decision": "rejected", "reviewer": "陈晨", "comment": "口径存疑"},
        )
        assert rejected.status_code == 200
        assert rejected.json()["decision"] == "evidence_rejected"

        blocked = await client.post(
            f"/api/v1/investigations/{finding_id}/transition",
            json={"decision": "approved", "reviewer": "王总"},
        )
        assert blocked.status_code == 409
        assert blocked.json()["detail"]["code"] == "invalid_transition"

        submitted = await client.post(
            f"/api/v1/investigations/{finding_id}/transition",
            json={"decision": "submitted", "reviewer": "陈晨"},
        )
        assert submitted.status_code == 200
        assert submitted.json()["status"] == "in_review"

        still_blocked = await client.post(
            f"/api/v1/investigations/{finding_id}/transition",
            json={"decision": "approved", "reviewer": "王总"},
        )
        assert still_blocked.status_code == 409
        assert still_blocked.json()["detail"]["code"] == "evidence_rejected"

        reverified = await client.post(
            f"/api/v1/investigations/{finding_id}/evidence/{evidence_id}/decision",
            json={"decision": "verified", "reviewer": "陈晨", "comment": "审批单已归档"},
        )
        assert reverified.status_code == 200

        incomplete = await client.post(
            f"/api/v1/investigations/{finding_id}/transition",
            json={"decision": "approved", "reviewer": "王总"},
        )
        assert incomplete.status_code == 409
        assert incomplete.json()["detail"]["code"] == "conclusion_incomplete"

        conclusion = await client.put(
            f"/api/v1/investigations/{finding_id}/conclusion",
            json={
                "verified_facts": "低毛利业务占比上升，结构影响为负。",
                "analysis_judgment": "利润缺口的首要原因是增长结构。",
                "open_questions": "两家战略客户折扣审批单待归档。",
                "recommendation": "对快消与运输业务重新定价。",
                "editor": "陈晨",
            },
        )
        assert conclusion.status_code == 200

        approved = await client.post(
            f"/api/v1/investigations/{finding_id}/transition",
            json={"decision": "approved", "reviewer": "王总", "comment": "同意签发"},
        )
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"

        final = await client.get(f"/api/v1/investigations/{finding_id}")
        assert final.status_code == 200
        final_payload = final.json()
        assert final_payload["finding"]["status"] == "approved"
        assert final_payload["eligibility_blockers"] == []
        decisions = [review["decision"] for review in final_payload["reviews"]]
        assert decisions == [
            "evidence_rejected",
            "submitted",
            "evidence_verified",
            "approved",
        ]

