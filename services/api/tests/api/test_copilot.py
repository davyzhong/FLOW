from __future__ import annotations

from typing import Any

import pytest
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

from flow_api.api.routes.copilot import get_investigation_session
from flow_api.infrastructure.models.analytics import Finding
from flow_api.main import create_app


def _override(session: Session) -> Any:
    def _factory() -> Any:
        yield session

    return _factory


async def test_copilot_ask_returns_validated_structured_answer(
    analysis_session: Session,
) -> None:
    run = publish_analysis_run(analysis_session)
    finding = analysis_session.scalars(select(Finding).order_by(Finding.total_score.desc())).first()
    assert finding is not None

    app = create_app()
    app.dependency_overrides[get_investigation_session] = _override(analysis_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/copilot/investigations/{finding.id}/ask",
            json={
                "question": "这个发现的主要原因是什么？",
                "actor": "陈晨",
                "batch_id": str(run.metric_snapshot.batch_id),
                "metric_snapshot_id": str(run.metric_snapshot_id),
                "analysis_run_id": str(run.id),
            },
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] == "accepted"
    assert payload["provider"] == "deterministic"
    assert payload["answer"]["facts"], "deterministic provider must cite facts"
    assert payload["interaction_id"]


async def test_copilot_report_outline_rejects_unapproved_findings(
    analysis_session: Session,
) -> None:
    run = publish_analysis_run(analysis_session)
    app = create_app()
    app.dependency_overrides[get_investigation_session] = _override(analysis_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/copilot/report-outline",
            json={"batch_id": str(run.metric_snapshot.batch_id), "actor": "陈晨"},
        )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "copilot_validation_failed"
    assert "unapproved_finding" in response.json()["detail"]["message"]


@pytest.mark.parametrize("use_case", ["ask", "mapping", "outline"])
async def test_successful_copilot_audit_survives_request_close(
    analysis_session: Session,
    use_case: str,
) -> None:
    from publishing.publishing_support import approve_top_findings

    from flow_api.infrastructure.models.copilot import CopilotInteraction

    run = publish_analysis_run(analysis_session)
    approve_top_findings(analysis_session, count=100, run_id=run.id)
    finding = analysis_session.scalar(select(Finding).where(Finding.analysis_run_id == run.id))
    endpoints = {
        "ask": (f"/api/v1/copilot/investigations/{finding.id}/ask", {"question": "解释驱动"}),
        "mapping": (
            "/api/v1/copilot/explain-mapping",
            {"import_version_id": str(run.import_version_id)},
        ),
        "outline": (
            "/api/v1/copilot/report-outline",
            {"batch_id": str(run.metric_snapshot.batch_id)},
        ),
    }
    path, body = endpoints[use_case]
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(path, json={**body, "actor": "audit-test"})
    assert response.status_code == 200, response.text
    with Session(analysis_session.bind) as independent:
        audit = independent.get(CopilotInteraction, response.json()["interaction_id"])
        assert audit is not None
        assert audit.actor == "audit-test"
        assert audit.outcome == "accepted"


async def test_report_outline_uses_requested_batch_when_another_is_newer(
    analysis_session: Session,
) -> None:
    from publishing.publishing_support import approve_top_findings

    first = publish_analysis_run(analysis_session)
    approve_top_findings(analysis_session, count=100, run_id=first.id)
    second = publish_analysis_run(analysis_session)
    analysis_session.commit()
    assert first.metric_snapshot.batch_id != second.metric_snapshot.batch_id
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/copilot/report-outline",
            json={"batch_id": str(first.metric_snapshot.batch_id), "actor": "audit-test"},
        )
    assert response.status_code == 200, response.text
    cited = {
        citation for fact in response.json()["answer"]["facts"] for citation in fact["citations"]
    }
    first_ids = analysis_session.scalars(
        select(Finding.id).where(Finding.analysis_run_id == first.id)
    )
    assert any(f"finding:{finding_id}" in cited for finding_id in first_ids)
