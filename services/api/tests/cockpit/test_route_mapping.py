"""Cockpit 路由响应投影映射测试。"""

from __future__ import annotations

from types import SimpleNamespace

from flow_api.api.routes import cockpit


def test_overview_route_returns_filter_options(monkeypatch) -> None:
    filter_options = {
        "dimensions": [{"dimension": "organization", "label": "组织", "options": []}],
        "supported_combinations": [],
    }
    projection = SimpleNamespace(
        state="ready",
        context={},
        data_status={},
        filter_options=filter_options,
        kpi_cards=[],
        trends=[],
        conclusion=SimpleNamespace(text="", findings=[], tone="neutral"),
        source_notice=None,
    )
    monkeypatch.setattr(
        cockpit,
        "CockpitProjectionService",
        lambda: SimpleNamespace(overview=lambda *_args, **_kwargs: projection),
    )
    captured: dict[str, object] = {}

    class Response:
        @classmethod
        def model_validate(cls, payload: dict[str, object]) -> dict[str, object]:
            captured.update(payload)
            return payload

    monkeypatch.setattr(cockpit, "CockpitOverviewResponse", Response)

    result = cockpit.cockpit_overview(SimpleNamespace())

    assert result["filter_options"] == filter_options
    assert captured["filter_options"] == filter_options
