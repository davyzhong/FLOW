from __future__ import annotations

from pathlib import Path
from typing import Any

from httpx import ASGITransport, AsyncClient
from integration.analysis_run_support import (
    ANALYSIS_POLICY,
    CATALOG,
)
from integration.analysis_run_support import (
    _intake_session_fixture as _intake_session_fixture,  # noqa: F401
)
from integration.analysis_run_support import (
    _metric_session_fixture as _metric_session_fixture,  # noqa: F401
)
from integration.analysis_run_support import (
    analysis_session_fixture as _analysis_session_fixture,  # noqa: F401
)
from integration.test_metric_source_repository import _publish_reference
from sqlalchemy.orm import Session

from flow_api.analysis.policy import load_analysis_policy
from flow_api.analysis.service import AnalysisRunService
from flow_api.api.routes.dashboard import get_dashboard_session
from flow_api.dashboard.fixture import publish_dashboard_snapshot_series
from flow_api.main import create_app


async def test_dashboard_api_not_ready_ready_and_typed_filter_error(
    analysis_session: Session,
) -> None:
    app = create_app()

    def session_override() -> Any:
        yield analysis_session

    app.dependency_overrides[get_dashboard_session] = session_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        not_ready = await client.get("/api/v1/dashboard/overview")
        assert not_ready.status_code == 404
        assert not_ready.json()["detail"]["code"] == "dashboard_not_ready"

        _, batch, _ = _publish_reference(analysis_session)
        snapshots = publish_dashboard_snapshot_series(
            analysis_session, batch_id=batch.id, catalog=CATALOG
        )
        AnalysisRunService().create_run(
            analysis_session,
            snapshot_id=snapshots[-1].id,
            loaded_policy=load_analysis_policy(Path(ANALYSIS_POLICY)),
        )

        ready = await client.get("/api/v1/dashboard/overview")
        assert ready.status_code == 200
        payload = ready.json()
        assert payload["state"] == "ready"
        assert len(payload["metric_cards"]) == 8
        assert payload["trends"]["coverage_count"] == 12
        assert len(payload["product_table"]["rows"]) == 8
        assert len(payload["margin_matrix"]["cells"]) == 16
        assert len(payload["findings"]) == 4

        organization_id = payload["filter_options"]["dimensions"][0]["options"][0]["id"]
        product_id = payload["filter_options"]["dimensions"][2]["options"][0]["id"]
        unsupported = await client.get(
            "/api/v1/dashboard/overview",
            params={
                "organization_id": organization_id,
                "logistics_product_id": product_id,
            },
        )
        assert unsupported.status_code == 422
        assert (
            unsupported.json()["detail"]["code"]
            == "unsupported_filter_combination"
        )
