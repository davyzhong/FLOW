from __future__ import annotations

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
    finding = analysis_session.scalars(
        select(Finding).order_by(Finding.total_score.desc())
    ).first()
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
