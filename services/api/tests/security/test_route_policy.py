"""route_policy 测试（S01 Task 2B 重做）。

规格：docs/40_specs/security/internal-workbench-rbac-audit-v1.md（approved）§4/§5/§6；
权威清单 route-inventory-v1.tsv（66 条，含已批准待挂载的 modules 行）。

覆盖：
- TSV 装载与 §5 全部合并阻断项（重复/未知 Action/写豁免/blocked 无 action）；
- openapi() 探针双向一致（GLM P3-② 收编：`app.routes` 迭代是懒挂载盲区）；
- loader 契约（resource_type 登记表与 LOADERS 一一对应）；
- require_action：allow/deny/blocked/unresolved/审计失败 503/精确组合不符；
- 决策审计先于 handler，deny 也 durable（fake writer 断言顺序）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from flow_api.security.authorization import Action, ReasonCode
from flow_api.security.principal import Principal, Role
from flow_api.security.route_policy import (
    LOADER_RESOURCE_TYPE,
    LOADERS,
    PENDING_MOUNT_ROUTES,
    PRINCIPAL_DEP,
    PolicyValidationError,
    ResourceScopeUnresolved,
    get_audit_writer,
    get_readonly_session,
    iter_openapi_routes,
    load_policy,
    require_action,
    scan_two_way,
)

ENT_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ENT_B = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


def _principal(role: Role, enterprise: UUID = ENT_A, actor: str = "actor-1") -> Principal:
    return Principal(
        actor_id=actor,
        role=role,
        enterprise_id=enterprise,
        is_service_account=role == Role.SERVICE_ACCOUNT,
    )


# --- TSV 装载与校验 ---


def test_policy_loads_69_entries_sorted() -> None:
    entries = load_policy()
    assert len(entries) == 69
    keys = [(e.method, e.path) for e in entries]
    assert len(set(keys)) == 69, "存在重复 method/path"
    blocked = [e for e in entries if e.is_blocked]
    assert len(blocked) == 0, (
        f"R2 后权威清单不应再有 blocked 条目（治理写已策略化）：{[e.path for e in blocked]}"
    )
    for e in entries:
        if e.is_write:
            assert e.action is not None, f"写入口缺 action：{e.method} {e.path}"
        elif e.action is None:
            assert e.exemption_reason, f"只读入口缺豁免理由：{e.method} {e.path}"


def test_loader_registry_matches_loaders() -> None:
    assert set(LOADER_RESOURCE_TYPE) == set(LOADERS), (
        f"契约/实现不一致：{set(LOADER_RESOURCE_TYPE) ^ set(LOADERS)}"
    )
    # 每个非 blocked TSV 条目都有实现
    for e in load_policy():
        if not e.is_blocked:
            assert e.resource_loader in LOADERS, e.resource_loader


def _write_tsv(tmp_path: Path, rows: list[list[str]]) -> Path:
    path = tmp_path / "inventory.tsv"
    header = "\t".join(
        [
            "method",
            "path",
            "actual_side_effect",
            "action",
            "resource_loader",
            "owner",
            "exemption_reason",
        ]
    )
    body = "\n".join("\t".join(r) for r in rows)
    path.write_text(header + "\n" + body + "\n", encoding="utf-8")
    return path


def test_policy_validation_rejects_duplicates(tmp_path: Path) -> None:
    row = [
        "GET",
        "/api/v1/x",
        "database_read:x",
        "statement.report.read",
        "load_public_statement_report",
        "route-policy",
        "-",
    ]
    with pytest.raises(PolicyValidationError, match="重复"):
        load_policy(_write_tsv(tmp_path, [row, row]))


def test_policy_validation_rejects_unknown_action(tmp_path: Path) -> None:
    row = [
        "GET",
        "/api/v1/x",
        "database_read:x",
        "no.such.action",
        "load_public_statement_report",
        "route-policy",
        "-",
    ]
    with pytest.raises(PolicyValidationError, match="未知 Action"):
        load_policy(_write_tsv(tmp_path, [row]))


def test_policy_validation_rejects_write_with_exemption(tmp_path: Path) -> None:
    row = [
        "POST",
        "/api/v1/x",
        "database_write:x",
        "statement.report.publish",
        "load_public_statement_report",
        "route-policy",
        "read_only_exempt",
    ]
    with pytest.raises(PolicyValidationError, match="只读豁免"):
        load_policy(_write_tsv(tmp_path, [row]))


def test_policy_validation_rejects_blocked_without_action(tmp_path: Path) -> None:
    row = ["POST", "/api/v1/x", "database_write:x", "-", "blocked:no_scope", "route-policy", "-"]
    with pytest.raises(PolicyValidationError, match="blocked 入口缺少 action"):
        load_policy(_write_tsv(tmp_path, [row]))


# --- openapi() 探针双向一致（GLM 探针收编） ---


def test_openapi_probe_matches_tsv_two_way() -> None:
    from flow_api.main import create_app

    app = create_app()
    mounted = {(m, p) for m, p in iter_openapi_routes(app) if p.startswith("/api/v1")}
    assert len(mounted) == 69, f"openapi 探针挂载数变化：{len(mounted)}"
    report = scan_two_way(app, load_policy())
    assert report.missing == (), f"未登记路由：{report.missing}"
    assert report.stale == (), f"失效登记：{report.stale}"


def test_pending_mount_whitelist_is_empty() -> None:
    """「登记先行」白名单必须为空：/api/v1/modules 已随 module-boundaries 挂载。

    白名单非空 = 存在未经裁决的登记先行路由；新路由必须先挂载后登记，
    白名单仅用于已裁决但尚未合入的过渡窗口。
    """
    assert frozenset() == PENDING_MOUNT_ROUTES, "存在登记先行路由，须裁决后移入 TSV 或移除"


def test_principal_dep_is_wired_to_bearer_auth() -> None:
    """PRINCIPAL_DEP 单符号已接线到 Task 2A 的 require_bearer_auth（防回退）。

    若该符号被退回本地占位实现，说明 principal 解析被静默拆除——fail closed
    语义依赖真实 resolve_principal（§3/§10）。
    """
    from flow_api.api.auth import require_bearer_auth

    assert PRINCIPAL_DEP is require_bearer_auth


# --- require_action（mini-app + dependency_overrides） ---


class _FakeAuditWriter:
    def __init__(self, fail: bool = False) -> None:
        self.events: list[Any] = []
        self.fail = fail

    def write_decision(self, *, audit_context: Any, decision: Any, request_id: str) -> None:
        if self.fail:
            raise RuntimeError("audit store down")
        self.events.append((audit_context, decision, request_id))


def _app_with_route(
    *,
    method: str,
    path: str,
    action: Action,
    loader_name: str,
    principal: Principal,
    audit: _FakeAuditWriter,
    handler_called: list[bool],
) -> FastAPI:
    app = FastAPI()
    dependency = require_action(action, LOADERS[loader_name])

    async def handler(_ctx: Any = Depends(dependency)) -> dict[str, bool]:  # noqa: B008
        handler_called.append(True)
        return {"ok": True}

    app.add_api_route(path, handler, methods=[method])
    app.dependency_overrides[PRINCIPAL_DEP] = lambda: principal
    app.dependency_overrides[get_readonly_session] = lambda: None
    app.dependency_overrides[get_audit_writer] = lambda: audit
    return app


def test_allow_writes_audit_before_handler() -> None:
    called: list[bool] = []
    audit = _FakeAuditWriter()
    app = _app_with_route(
        method="POST",
        path="/api/v1/statements/{report_id}/publish",
        action=Action.STATEMENT_REPORT_PUBLISH,
        loader_name="load_public_statement_report",
        principal=_principal(Role.ANALYST),
        audit=audit,
        handler_called=called,
    )
    response = TestClient(app).post(f"/api/v1/statements/{uuid4()}/publish")
    assert response.status_code == 200
    assert called == [True]
    assert len(audit.events) == 1
    _, decision, _ = audit.events[0]
    assert decision.allowed and decision.reason_code == ReasonCode.ALLOW


def test_service_account_publish_denied_403_role_forbidden() -> None:
    called: list[bool] = []
    audit = _FakeAuditWriter()
    app = _app_with_route(
        method="POST",
        path="/api/v1/statements/{report_id}/publish",
        action=Action.STATEMENT_REPORT_PUBLISH,
        loader_name="load_public_statement_report",
        principal=_principal(Role.SERVICE_ACCOUNT, actor="legacy-bearer"),
        audit=audit,
        handler_called=called,
    )
    response = TestClient(app).post(f"/api/v1/statements/{uuid4()}/publish")
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "role_forbidden"
    assert called == [], "deny 后 handler 不得执行"
    assert audit.events and not audit.events[0][1].allowed, "deny 也必须 durable"


def test_blocked_route_never_enters_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    """blocked:* 条目无条件 403 route_blocked（机制守护；权威清单现无 blocked 条目）。

    R2 已把 metric-library 治理写策略化（blocked 清零）；本用例以合成 policy
    保住 require_action 的 blocked 分支，防止未来再引入 blocked 条目时分支失守。
    """
    from flow_api.security import route_policy as rp

    synthetic = (
        rp.PolicyEntry(
            method="POST",
            path="/api/v1/metric-library/import",
            actual_side_effect="database_write:x",
            action=Action.METRIC_LIBRARY_IMPORT,
            resource_loader="blocked:metric_dictionary_has_no_enterprise_scope",
            owner="route-policy",
            exemption_reason=None,
        ),
    )
    monkeypatch.setattr(rp, "_POLICY", synthetic)
    called: list[bool] = []
    audit = _FakeAuditWriter()
    app = _app_with_route(
        method="POST",
        path="/api/v1/metric-library/import",
        action=Action.METRIC_LIBRARY_IMPORT,
        loader_name="load_blocked_entry",
        principal=_principal(Role.ANALYST),
        audit=audit,
        handler_called=called,
    )
    response = TestClient(app).post("/api/v1/metric-library/import", json={"actor": "flow-dev-bp"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "route_blocked"
    assert called == []


def test_unresolved_lineage_denied_resource_scope_unresolved() -> None:
    called: list[bool] = []
    audit = _FakeAuditWriter()

    def unresolved_loader(request: Any, session: Any) -> Any:
        raise ResourceScopeUnresolved("analysis_batch", "missing")

    app = FastAPI()
    dependency = require_action(Action.ORCHESTRATION_BUILD_START, unresolved_loader)

    async def handler(_ctx: Any = Depends(dependency)) -> dict[str, bool]:  # noqa: B008
        called.append(True)
        return {"ok": True}

    app.add_api_route("/api/v1/orchestration/batches/{batch_id}/build", handler, methods=["POST"])
    app.dependency_overrides[PRINCIPAL_DEP] = lambda: _principal(Role.SERVICE_ACCOUNT)
    app.dependency_overrides[get_readonly_session] = lambda: None
    app.dependency_overrides[get_audit_writer] = lambda: audit

    response = TestClient(app).post(f"/api/v1/orchestration/batches/{uuid4()}/build")
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "resource_scope_unresolved"
    assert called == []


def test_audit_failure_returns_503_fail_closed() -> None:
    called: list[bool] = []
    app = _app_with_route(
        method="POST",
        path="/api/v1/statements/{report_id}/publish",
        action=Action.STATEMENT_REPORT_PUBLISH,
        loader_name="load_public_statement_report",
        principal=_principal(Role.ANALYST),
        audit=_FakeAuditWriter(fail=True),
        handler_called=called,
    )
    response = TestClient(app).post(f"/api/v1/statements/{uuid4()}/publish")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "audit_unavailable"
    assert called == [], "审计未 durable 时 handler 不得执行"


def test_action_mismatch_with_policy_denied() -> None:
    """接线的 action 与 TSV 登记不符 → action_resource_mismatch。"""
    called: list[bool] = []
    audit = _FakeAuditWriter()
    app = _app_with_route(
        method="POST",
        path="/api/v1/statements/{report_id}/publish",
        action=Action.STATEMENT_CORRECTION_CREATE,  # TSV 登记的是 statement.report.publish
        loader_name="load_public_statement_report",
        principal=_principal(Role.ANALYST),
        audit=audit,
        handler_called=called,
    )
    response = TestClient(app).post(f"/api/v1/statements/{uuid4()}/publish")
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "action_resource_mismatch"
    assert called == []


def test_cross_enterprise_denied_via_public_loader_impossible() -> None:
    """public scope 不做企业比较（§4.2-4）；enterprise loader 由集成测试覆盖。

    这里验证 public 资源上不同企业 Principal 仍按 role 判定（analyst allow）。
    """
    called: list[bool] = []
    audit = _FakeAuditWriter()
    app = _app_with_route(
        method="POST",
        path="/api/v1/statements/{report_id}/publish",
        action=Action.STATEMENT_REPORT_PUBLISH,
        loader_name="load_public_statement_report",
        principal=_principal(Role.ANALYST, enterprise=ENT_B),
        audit=audit,
        handler_called=called,
    )
    assert TestClient(app).post(f"/api/v1/statements/{uuid4()}/publish").status_code == 200
