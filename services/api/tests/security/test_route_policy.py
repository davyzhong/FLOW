"""route_policy 注册表与扫描器测试（S01 三智能体计划 Task 2B）。

规格：docs/40_specs/security/internal-workbench-rbac-audit-v1.md（approved）。
- 最终挂载的每个 /api/v1 路由必须登记：写方法/隐藏写 GET 必须有 action；
  只读路由必须有豁免理由；不允许未登记或失效（stale）条目；
- authorize 纯函数：deny-by-default、跨企业拒绝、规则不可自批、AI 无发布权、
  旧 Bearer（service_account）无发布/冻结/审批权；
- require_action 依赖：allow/deny 都写审计事件（测试 fake，不实现第二套存储）。
"""

from __future__ import annotations

from uuid import UUID

import pytest
from fastapi import HTTPException

from flow_api.security.authorization import (
    ResourceContext,
    authorize,
)
from flow_api.security.principal import Principal, Role
from flow_api.security.route_policy import (
    ROUTE_POLICY,
    iter_mounted_routes,
    scan_route_coverage,
)

ENT_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ENT_B = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


def _principal(role: Role, enterprise: UUID | None = ENT_A, actor: str = "actor-1") -> Principal:
    return Principal(
        actor_id=actor,
        role=role,
        enterprise_id=enterprise,
        is_service_account=role == Role.SERVICE_ACCOUNT,
    )


# --- 扫描器：全路由覆盖 ---


def test_every_mounted_route_registered() -> None:
    from flow_api.main import create_app

    report = scan_route_coverage(create_app().router)
    assert report.missing == [], f"未登记路由：{report.missing}"
    assert report.stale == [], f"失效登记：{report.stale}"


def test_write_routes_have_action_and_read_routes_have_reason() -> None:
    from flow_api.main import create_app

    for method, path in iter_mounted_routes(create_app().router):
        if not path.startswith("/api/v1"):
            continue
        entry = ROUTE_POLICY[(method, path)]
        if entry.is_write:
            assert entry.action, f"{method} {path} 写入口缺少 action"
            assert entry.read_only_reason is None
        else:
            assert entry.read_only_reason, f"{method} {path} 只读入口缺少豁免理由"


def test_hidden_write_gets_are_write_entries() -> None:
    """会冻结快照的 GET 必须按写入口处理。"""
    for path in (
        "/api/v1/statements/{report_id}/objective-snapshot",
        "/api/v1/statements/{report_id}/objective-snapshot/html",
    ):
        entry = ROUTE_POLICY[("GET", path)]
        assert entry.is_write and entry.action == "statement:snapshot.freeze"


def test_scanner_flags_unregistered_sensitive_route() -> None:
    """构造未登记敏感路由 fixture，证明扫描不是空转。"""

    class _FakeRoute:
        methods = {"POST"}
        path = "/api/v1/secret-unregistered"

    class _FakeRouter:
        routes = [_FakeRoute()]

    report = scan_route_coverage(_FakeRouter())
    assert ("POST", "/api/v1/secret-unregistered") in report.missing


# --- authorize 纯函数 ---


def test_deny_by_default_for_unknown_action() -> None:
    decision = authorize(_principal(Role.ANALYST), "unknown:action", ResourceContext.unscoped())
    assert not decision.allowed


def test_cross_enterprise_denied() -> None:
    resource = ResourceContext(kind="batch", resource_id="x", enterprise_id=ENT_B)
    decision = authorize(_principal(Role.ANALYST, enterprise=ENT_A), "intake:batch.read", resource)
    assert not decision.allowed
    assert "跨企业" in decision.reason


def test_same_enterprise_allowed() -> None:
    resource = ResourceContext(kind="batch", resource_id="x", enterprise_id=ENT_A)
    assert authorize(
        _principal(Role.ANALYST, enterprise=ENT_A), "intake:batch.read", resource
    ).allowed


def test_rule_self_approval_denied() -> None:
    resource = ResourceContext(
        kind="metric_entry",
        resource_id="e1",
        enterprise_id=ENT_A,
        attributes={"proposed_by": "actor-1"},
    )
    decision = authorize(
        _principal(Role.RULE_OWNER, actor="actor-1"), "metric:rule.approve", resource
    )
    assert not decision.allowed
    assert "自批" in decision.reason


def test_rule_approval_by_other_allowed() -> None:
    resource = ResourceContext(
        kind="metric_entry",
        resource_id="e1",
        enterprise_id=ENT_A,
        attributes={"proposed_by": "someone-else"},
    )
    assert authorize(
        _principal(Role.RULE_OWNER, actor="actor-1"), "metric:rule.approve", resource
    ).allowed


@pytest.mark.parametrize("role", [Role.AI_ANALYST, Role.AI_CFO, Role.SERVICE_ACCOUNT])
@pytest.mark.parametrize(
    "action",
    [
        "statement:publish",
        "statement:snapshot.freeze",
        "intake:import.publish",
        "metric:rule.approve",
        "investigation:evidence.decide",
    ],
)
def test_ai_and_service_account_have_no_publish_or_approve(role: Role, action: str) -> None:
    decision = authorize(_principal(role), action, ResourceContext.unscoped())
    assert not decision.allowed


def test_analyst_is_unique_human_publisher() -> None:
    assert authorize(
        _principal(Role.ANALYST), "statement:publish", ResourceContext.unscoped()
    ).allowed
    for role in (
        Role.FINANCE_BP,
        Role.RULE_OWNER,
        Role.AI_ANALYST,
        Role.AI_CFO,
        Role.SERVICE_ACCOUNT,
    ):
        assert not authorize(
            _principal(role), "statement:publish", ResourceContext.unscoped()
        ).allowed


def test_development_principal_allowed() -> None:
    dev = Principal(
        actor_id="dev", role=Role.DEVELOPMENT, enterprise_id=None, is_service_account=False
    )
    assert authorize(dev, "statement:publish", ResourceContext.unscoped()).allowed


def test_finance_bp_submit_only() -> None:
    assert authorize(
        _principal(Role.FINANCE_BP), "intake:source.upload", ResourceContext.unscoped()
    ).allowed
    assert not authorize(
        _principal(Role.FINANCE_BP), "metric:rule.approve", ResourceContext.unscoped()
    ).allowed
    assert not authorize(
        _principal(Role.FINANCE_BP), "statement:publish", ResourceContext.unscoped()
    ).allowed


# --- require_action 依赖（fake 审计） ---


class _FakeAuditWriter:
    def __init__(self) -> None:
        self.events = []

    def record(self, event) -> None:  # noqa: ANN001
        self.events.append(event)


@pytest.mark.asyncio
async def test_require_action_allows_and_audits() -> None:
    from flow_api.security.route_policy import require_action

    writer = _FakeAuditWriter()
    dependency = require_action("statement:publish")
    await dependency(
        principal=_principal(Role.ANALYST),
        resource=ResourceContext.unscoped(),
        audit=writer,
    )
    assert writer.events and writer.events[0].decision == "allow"


@pytest.mark.asyncio
async def test_require_action_denies_with_403_and_audit() -> None:
    from flow_api.security.route_policy import require_action

    writer = _FakeAuditWriter()
    dependency = require_action("statement:publish")
    with pytest.raises(HTTPException) as exc_info:
        await dependency(
            principal=_principal(Role.AI_ANALYST),
            resource=ResourceContext.unscoped(),
            audit=writer,
        )
    assert exc_info.value.status_code == 403
    assert writer.events and writer.events[0].decision == "deny"
