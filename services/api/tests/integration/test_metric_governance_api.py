"""指标库治理 API（C04 × S01 R2）：治理写策略化后的角色矩阵与自审批防线。

规格合同：
- §4.3：analyst=全部 Action 除 activate/retire；rule_owner=治理全集（无
  metric_library.import/retire）；ai_analyst 有 impact 无 propose/activate；
  finance_bp 无任何治理权；
- §4.2 step7：activate/retire 必须 proposed_by 且不得本人审批；
- §3.3：body operator 与 Principal 冲突 → 409 actor_conflict；
- §6：每个 allow/deny 决策先落 durable AuditEvent。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete, select, text
from sqlalchemy.orm import Session

from flow_api.api.routes.metric_library import get_metric_library_session
from flow_api.infrastructure.models.metric_library import (
    AccountingStandard,
    AccountingSubject,
    EntryTemplate,
    MetricCatalogDocument,
    MetricDictionaryEntry,
    MetricGovernanceEvent,
    StatementLineMapping,
)
from flow_api.main import create_app
from flow_api.metric_library_store.importer import import_metric_dictionary, resolve_dictionary_file
from flow_api.settings import get_settings

REPO_ROOT = Path(__file__).resolve().parents[4]
DICT_YAML = resolve_dictionary_file(REPO_ROOT / "config/metrics")

ANALYST = "flow-dev-bp"
RULE_OWNER = "govern-rule-owner-a"
FINANCE_BP = "govern-finance-bp-a"
AI_ANALYST = "govern-ai-analyst-a"

_ENTERPRISE = "00000000-0000-0000-0000-00000000d001"


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
async def client() -> Any:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    for table in (
        MetricGovernanceEvent,
        MetricDictionaryEntry,
        MetricCatalogDocument,
        AccountingSubject,
        AccountingStandard,
        EntryTemplate,
        StatementLineMapping,
    ):
        session.execute(delete(table))
    # 多角色 binding（conftest 只种 analyst + service_account）
    with engine.begin() as conn:
        for actor, role, svc in (
            (RULE_OWNER, "rule_owner", False),
            (FINANCE_BP, "finance_bp", False),
            (AI_ANALYST, "ai_analyst", False),
        ):
            conn.execute(
                text(
                    "INSERT INTO role_binding (actor_id, role, enterprise_id,"
                    " is_service_account, active)"
                    " SELECT CAST(:actor AS varchar), :role,"
                    " CAST(:enterprise AS uuid), :svc, true"
                    " WHERE NOT EXISTS (SELECT 1 FROM role_binding"
                    " WHERE actor_id = :actor AND active IS TRUE)"
                ),
                {"actor": actor, "role": role, "enterprise": _ENTERPRISE, "svc": svc},
            )
    session.commit()
    import_metric_dictionary(session, DICT_YAML)
    session.commit()

    app = create_app()
    app.dependency_overrides[get_metric_library_session] = lambda: session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    session.close()
    engine.dispose()


def _become(actor: str) -> None:
    os.environ["FLOW_DEV_ACTOR_ID"] = actor
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_actor() -> Any:
    yield
    _become(ANALYST)


async def _effective_entry_id(metric_code: str) -> str:
    from flow_api.infrastructure.db import get_engine

    with Session(get_engine()) as reader:
        entry = reader.scalar(
            select(MetricDictionaryEntry).where(
                MetricDictionaryEntry.metric_code == metric_code,
                MetricDictionaryEntry.status == "effective",
            )
        )
        assert entry is not None
        return str(entry.id)


async def test_analyst_can_propose_but_not_activate(client: AsyncClient) -> None:
    _become(ANALYST)
    entry_id = await _effective_entry_id("current_ratio")

    draft = await client.post(
        f"/api/v1/metric-library/entries/{entry_id}/drafts",
        json={
            "changes": {"benchmark": "经验参考约 2.2"},
            "operator": ANALYST,
            "reason": "基准校准",
        },
    )
    assert draft.status_code == 201, draft.text
    assert draft.json()["status"] == "draft"

    activated = await client.post(
        f"/api/v1/metric-library/entries/{entry_id}/activate",
        json={"reason": "评审通过"},
    )
    assert activated.status_code == 403
    assert activated.json()["detail"]["code"] == "role_forbidden"


async def test_rule_owner_activates_other_proposal(client: AsyncClient) -> None:
    entry_id = await _effective_entry_id("quick_ratio")
    _become(ANALYST)
    draft = await client.post(
        f"/api/v1/metric-library/entries/{entry_id}/drafts",
        json={"changes": {"definition": "保守口径说明"}, "reason": "口径澄清"},
    )
    assert draft.status_code == 201, draft.text

    _become(RULE_OWNER)
    activated = await client.post(
        f"/api/v1/metric-library/entries/{draft.json()['id']}/activate",
        json={"reason": "评审通过"},
    )
    assert activated.status_code == 200, activated.text
    assert activated.json()["status"] == "effective"

    events = await client.get(
        "/api/v1/metric-library/events", params={"metric_code": "quick_ratio"}
    )
    assert events.status_code == 200
    actions = [e["action"] for e in events.json()["events"]]
    assert "draft" in actions and "activate" in actions


async def test_self_approval_forbidden(client: AsyncClient) -> None:
    entry_id = await _effective_entry_id("gross_margin")
    _become(RULE_OWNER)
    draft = await client.post(
        f"/api/v1/metric-library/entries/{entry_id}/drafts",
        json={"changes": {"benchmark": "自审草稿"}, "reason": "r"},
    )
    assert draft.status_code == 201, draft.text
    activated = await client.post(
        f"/api/v1/metric-library/entries/{draft.json()['id']}/activate",
        json={"reason": "自己批自己"},
    )
    assert activated.status_code == 403
    assert activated.json()["detail"]["code"] == "self_approval_forbidden"


async def test_retire_without_proposer_is_fail_closed(client: AsyncClient) -> None:
    """导入直接生成的 effective 版本无 draft 事件 → proposed_by=None → deny。"""
    _become(RULE_OWNER)
    entry_id = await _effective_entry_id("net_profit_growth")
    retired = await client.post(
        f"/api/v1/metric-library/entries/{entry_id}/retire",
        json={"reason": "无提议人"},
    )
    assert retired.status_code == 403
    assert retired.json()["detail"]["code"] == "proposer_required"


async def test_rule_owner_cannot_import_or_dictionary_retire(client: AsyncClient) -> None:
    """§4.3 机器真相：metric_library.import/retire 只在 analyst allow set。"""
    _become(RULE_OWNER)
    imported = await client.post("/api/v1/metric-library/import", json={"actor": RULE_OWNER})
    assert imported.status_code == 403
    assert imported.json()["detail"]["code"] == "role_forbidden"
    retired = await client.post(
        "/api/v1/metric-library/retire",
        json={"dictionary_id": "flow.metric_dictionary.v1", "reason": "x"},
    )
    assert retired.status_code == 403


async def test_analyst_import_and_dictionary_retire(client: AsyncClient) -> None:
    _become(ANALYST)
    imported = await client.post("/api/v1/metric-library/import", json={"actor": ANALYST})
    assert imported.status_code == 200, imported.text
    retired = await client.post(
        "/api/v1/metric-library/retire",
        json={"dictionary_id": "flow.metric_dictionary.v1", "actor": ANALYST, "reason": "演练退役"},
    )
    assert retired.status_code == 200, retired.text
    assert retired.json()["retired"] > 0
    # 幂等恢复：再导入回来
    again = await client.post("/api/v1/metric-library/import", json={"actor": ANALYST})
    assert again.status_code == 200


async def test_finance_bp_has_no_governance_access(client: AsyncClient) -> None:
    _become(FINANCE_BP)
    entry_id = await _effective_entry_id("current_ratio")
    events = await client.get("/api/v1/metric-library/events")
    assert events.status_code == 403
    draft = await client.post(
        f"/api/v1/metric-library/entries/{entry_id}/drafts",
        json={"changes": {"benchmark": "bp 不可以"}, "reason": "r"},
    )
    assert draft.status_code == 403


async def test_ai_analyst_impact_only(client: AsyncClient) -> None:
    """ai_analyst：有 metric.impact.analyze，无 propose/activate/events。"""
    entry_id = await _effective_entry_id("current_ratio")
    _become(AI_ANALYST)
    events = await client.get("/api/v1/metric-library/events")
    assert events.status_code == 403
    draft = await client.post(
        f"/api/v1/metric-library/entries/{entry_id}/drafts",
        json={"changes": {"benchmark": "AI 不可以"}, "reason": "r"},
    )
    assert draft.status_code == 403
    # impact 走真实草稿链：AI 无 propose → 先由 analyst 起草，AI 只读影响
    _become(ANALYST)
    draft = await client.post(
        f"/api/v1/metric-library/entries/{entry_id}/drafts",
        json={"changes": {"benchmark": "AI 影响分析基线"}, "reason": "r"},
    )
    assert draft.status_code == 201
    draft_entry_id = draft.json()["id"]
    _become(AI_ANALYST)
    impact = await client.post(f"/api/v1/metric-library/entries/{draft_entry_id}/impact")
    assert impact.status_code == 200, impact.text
    assert impact.json()["metric_code"] == "current_ratio"


async def test_body_operator_conflict_is_409(client: AsyncClient) -> None:
    """§3.3：body operator 与 Principal 不同 → 409 actor_conflict（allow 审计后）。"""
    _become(ANALYST)
    entry_id = await _effective_entry_id("current_ratio")
    draft = await client.post(
        f"/api/v1/metric-library/entries/{entry_id}/drafts",
        json={"changes": {"benchmark": "x"}, "operator": "someone-else", "reason": "r"},
    )
    assert draft.status_code == 409
    assert draft.json()["detail"]["code"] == "actor_conflict"


async def test_activate_illegal_ast_rejected_over_http(client: AsyncClient) -> None:
    entry_id = await _effective_entry_id("cash_conversion")
    _become(ANALYST)
    draft = await client.post(
        f"/api/v1/metric-library/entries/{entry_id}/drafts",
        json={
            "changes": {"formula": {"op": "median", "args": ["bs.total_assets"]}},
            "reason": "非法算子",
        },
    )
    assert draft.status_code == 201, draft.text
    _become(RULE_OWNER)
    activated = await client.post(
        f"/api/v1/metric-library/entries/{draft.json()['id']}/activate",
        json={"reason": "r"},
    )
    assert activated.status_code == 409
    assert activated.json()["detail"]["code"] == "invalid_formula_ast"
