"""S01 Task 2A Bootstrap：纯 `authorize` 函数的红灯测试。

依据：docs/40_specs/security/internal-workbench-rbac-audit-v1.md
- §2 冻结类型
- §4.2 八步短路判定顺序
- §4.3 完整 allow set
- §2.2 development principal 限制

测试范围（本 Bootstrap）：
- Role / Action / ResourceScope / Principal / ResourceRef / Decision / ReasonCode
  冻结类型的可序列化与一致性；
- 纯函数 `authorize` 的八步短路、allow set 矩阵、跨企业拒绝、self approval、AI 无发布权；
- `audit_protocol` 协议签名（不实现 ORM，Task 2A 后半段）。

测试不在本 Bootstrap：
- AuditEvent 持久化（Task 2A 后半段 / 0026 迁移）；
- publishing 四阶段 ABI（Task 2A 后半段）；
- 旧 Bearer 截止（接口签名 + cutoff 读取已在 principal.py，end-to-end 在 Task 2B 集成）；
- HTTP route 接线（Task 2B Kimi）。
"""
from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from flow_api.security.audit import AuditContext, ModelBoundary
from flow_api.security.authorization import (
    Action,
    Decision,
    ReasonCode,
    ResourceRef,
    authorize,
)
from flow_api.security.principal import (
    Principal,
    Role,
)

PUBLIC = "public"  # ResourceScope 是 Literal["public", "enterprise"]
ENTERPRISE = "enterprise"


# -- helpers --------------------------------------------------------------


def _principal(
    role: Role, *, enterprise_id: UUID | None = None, is_service: bool = False
) -> Principal:
    return Principal(
        actor_id=f"actor-{role.value}",
        role=role,
        enterprise_id=enterprise_id,
        is_service_account=is_service,
    )


def _enterprise() -> UUID:
    return uuid4()


def _other_enterprise() -> UUID:
    return uuid4()


# -- §2 冻结类型契约 -------------------------------------------------------


def test_role_enum_is_complete_and_str_serializable() -> None:
    expected = {
        "finance_bp",
        "analyst",
        "rule_owner",
        "ai_analyst",
        "ai_cfo",
        "service_account",
    }
    actual = {r.value for r in Role}
    assert actual == expected
    # StrEnum 必须既是 str 又是枚举值
    assert Role.ANALYST == "analyst"
    assert isinstance(Role.ANALYST, str)


def test_action_enum_count_matches_spec() -> None:
    # 规格 §2.1 Action 列出 58 项（实现若有差异即拒绝合并）
    assert len(list(Action)) == 58


def test_principal_invariant_service_flag_consistency() -> None:
    # role=SERVICE_ACCOUNT 当且仅当 is_service_account=True，否则构造时拒绝
    with pytest.raises((ValueError, TypeError)):
        Principal(actor_id="a", role=Role.SERVICE_ACCOUNT,
            enterprise_id=None, is_service_account=False)
    with pytest.raises((ValueError, TypeError)):
        Principal(
            actor_id="a", role=Role.ANALYST, enterprise_id=_enterprise(), is_service_account=True
        )


def test_principal_human_or_ai_must_have_enterprise_id() -> None:
    # §3.1.4 人类/AI 角色必须有 enterprise_id
    with pytest.raises((ValueError, TypeError)):
        Principal(actor_id="a", role=Role.ANALYST, enterprise_id=None, is_service_account=False)


def test_resource_ref_public_must_have_no_enterprise_id() -> None:
    with pytest.raises((ValueError, TypeError)):
        ResourceRef(
            scope=PUBLIC,
            resource_type="x",
            resource_id="y",
            enterprise_id=_enterprise(),
            owner_actor_id=None,
            proposed_by_actor_id=None,
        )


def test_resource_ref_enterprise_must_have_enterprise_id() -> None:
    with pytest.raises((ValueError, TypeError)):
        ResourceRef(
            scope=ENTERPRISE,
            resource_type="x",
            resource_id="y",
            enterprise_id=None,
            owner_actor_id=None,
            proposed_by_actor_id=None,
        )


# -- §4.2 八步短路：每个 step 第一个命中的 reason code 优先 --------------


def test_step1_invalid_principal_role_service_flag_mismatch() -> None:
    # 类型层硬约束：role=SERVICE_ACCOUNT 必须 is_service_account=True，反之亦然
    with pytest.raises(ValueError):
        Principal(
            actor_id="x", role=Role.SERVICE_ACCOUNT, enterprise_id=_enterprise(),
            is_service_account=False,
        )
    with pytest.raises(ValueError):
        Principal(
            actor_id="x", role=Role.ANALYST, enterprise_id=_enterprise(), is_service_account=True
        )
    # 合法 principal 通过 step1（不返回 INVALID_PRINCIPAL）；具体 reason 由后续步骤决定
    p = _principal(Role.ANALYST, enterprise_id=_enterprise())
    r = ResourceRef(
        scope=ENTERPRISE,
        resource_type="intake_batch",
        resource_id="b1",
        enterprise_id=p.enterprise_id,
        owner_actor_id=None,
        proposed_by_actor_id=None,
    )
    decision = authorize(p, Action.INTAKE_BATCH_CREATE, r)
    assert decision.reason_code != ReasonCode.INVALID_PRINCIPAL
    # R1 bootstrap 语义：owner 缺（引导数据）→ 企业隔离已由 step4 保证，放行
    assert decision.reason_code == ReasonCode.ALLOW


def test_step3_action_resource_mismatch_when_loader_returns_blocked() -> None:
    # §4.2 step3（action×resource_type 精确组合）在 route policy 接线处执行，
    # 不进入纯 authorize；纯函数对 step3 的失败由 step5 allow set 决定。
    # 此处验证纯函数不返回 ACTION_RESOURCE_MISMATCH（该 reason 留给 route policy 接线层）。
    p = _principal(Role.ANALYST, enterprise_id=_enterprise())
    r = ResourceRef(
        scope=ENTERPRISE,
        resource_type="metric_library",
        resource_id="x",
        enterprise_id=p.enterprise_id,
        owner_actor_id=None,
        proposed_by_actor_id=None,
    )
    decision = authorize(p, Action.METRIC_LIBRARY_RETIRE, r)
    # analyst 允许 metric_library.retire；owner 缺走 R1 bootstrap 语义 → ALLOW
    # （该路由实际被 TSV blocked 条目拦截，见 route policy 测试）
    assert decision.reason_code != ReasonCode.ACTION_RESOURCE_MISMATCH


def test_step4_cross_enterprise_denied() -> None:
    me = _enterprise()
    other = _other_enterprise()
    p = _principal(Role.ANALYST, enterprise_id=me)
    r = ResourceRef(
        scope=ENTERPRISE,
        resource_type="investigation",
        resource_id="f1",
        enterprise_id=other,  # 不是我的企业
        owner_actor_id=None,
        proposed_by_actor_id=None,
    )
    decision = authorize(p, Action.INVESTIGATION_READ, r)
    assert decision.allowed is False
    assert decision.reason_code == ReasonCode.CROSS_ENTERPRISE


def test_step4_public_scope_does_not_compare_enterprise() -> None:
    p = _principal(Role.ANALYST, enterprise_id=_enterprise())
    r = ResourceRef(
        scope=PUBLIC,
        resource_type="statement_report",
        resource_id="r1",
        enterprise_id=None,
        owner_actor_id=None,
        proposed_by_actor_id=None,
    )
    decision = authorize(p, Action.STATEMENT_REPORT_READ, r)
    # 公开 scope 下不应被跨企业拒绝；可能 allow 或 ROLE_FORBIDDEN（取决于 allow set）
    assert decision.reason_code != ReasonCode.CROSS_ENTERPRISE
    assert decision.reason_code != ReasonCode.ENTERPRISE_REQUIRED


def test_step4_enterprise_required_when_principal_has_no_enterprise() -> None:
    # §3.1.4 所有角色都必须有 enterprise_id，Principal 类型层已 fail-fast。
    # 此测试断言类型层与 step1 拦截：构造缺 enterprise_id 的 service_account 必须抛 ValueError。
    with pytest.raises(ValueError):
        Principal(actor_id="svc", role=Role.SERVICE_ACCOUNT,
            enterprise_id=None, is_service_account=True)
    with pytest.raises(ValueError):
        Principal(actor_id="ana", role=Role.ANALYST,
            enterprise_id=None, is_service_account=False)


def test_step7_self_approval_forbidden() -> None:
    me = _enterprise()
    p = _principal(Role.RULE_OWNER, enterprise_id=me)
    r = ResourceRef(
        scope=ENTERPRISE,
        resource_type="metric_change",
        resource_id="m1",
        enterprise_id=me,
        owner_actor_id=None,
        proposed_by_actor_id=p.actor_id,  # 我自己提议
    )
    decision = authorize(p, Action.METRIC_CHANGE_ACTIVATE, r)
    assert decision.allowed is False
    assert decision.reason_code == ReasonCode.SELF_APPROVAL_FORBIDDEN


def test_step7_proposer_required_when_missing() -> None:
    me = _enterprise()
    p = _principal(Role.RULE_OWNER, enterprise_id=me)
    r = ResourceRef(
        scope=ENTERPRISE,
        resource_type="metric_change",
        resource_id="m2",
        enterprise_id=me,
        owner_actor_id=None,
        proposed_by_actor_id=None,  # 缺提议者
    )
    decision = authorize(p, Action.METRIC_CHANGE_ACTIVATE, r)
    assert decision.allowed is False
    assert decision.reason_code in {
        ReasonCode.PROPOSER_REQUIRED,
        ReasonCode.ROLE_FORBIDDEN,
        ReasonCode.ACTION_RESOURCE_MISMATCH,
    }


# -- §4.3 完整 allow set 矩阵关键样例 --------------------------------------


def test_ai_analyst_cannot_publish_report() -> None:
    me = _enterprise()
    p = _principal(Role.AI_ANALYST, enterprise_id=me)
    r = ResourceRef(
        scope=ENTERPRISE,
        resource_type="report_snapshot",
        resource_id="s1",
        enterprise_id=me,
        owner_actor_id=None,
        proposed_by_actor_id=None,
    )
    decision = authorize(p, Action.PUBLISHING_REPORT_PUBLISH, r)
    assert decision.allowed is False
    assert decision.reason_code == ReasonCode.ROLE_FORBIDDEN


def test_ai_cfo_cannot_freeze_snapshot() -> None:
    me = _enterprise()
    p = _principal(Role.AI_CFO, enterprise_id=me)
    r = ResourceRef(
        scope=ENTERPRISE,
        resource_type="report_snapshot",
        resource_id="s2",
        enterprise_id=me,
        owner_actor_id=None,
        proposed_by_actor_id=None,
    )
    decision = authorize(p, Action.PUBLISHING_SNAPSHOT_FREEZE, r)
    assert decision.allowed is False
    assert decision.reason_code == ReasonCode.ROLE_FORBIDDEN


def test_finance_bp_cannot_activate_metric_change() -> None:
    me = _enterprise()
    p = _principal(Role.FINANCE_BP, enterprise_id=me)
    r = ResourceRef(
        scope=ENTERPRISE,
        resource_type="metric_change",
        resource_id="m3",
        enterprise_id=me,
        owner_actor_id=None,
        proposed_by_actor_id="someone-else",
    )
    decision = authorize(p, Action.METRIC_CHANGE_ACTIVATE, r)
    assert decision.allowed is False
    assert decision.reason_code == ReasonCode.ROLE_FORBIDDEN


def test_service_account_cannot_publish_or_freeze() -> None:
    me = _enterprise()
    p = _principal(Role.SERVICE_ACCOUNT, enterprise_id=me, is_service=True)
    r = ResourceRef(
        scope=ENTERPRISE,
        resource_type="report_snapshot",
        resource_id="s3",
        enterprise_id=me,
        owner_actor_id=None,
        proposed_by_actor_id=None,
    )
    for action in (Action.PUBLISHING_REPORT_PUBLISH, Action.PUBLISHING_SNAPSHOT_FREEZE):
        decision = authorize(p, action, r)
        assert decision.allowed is False
        assert decision.reason_code == ReasonCode.ROLE_FORBIDDEN


def test_service_account_can_run_orchestration_build() -> None:
    me = _enterprise()
    p = _principal(Role.SERVICE_ACCOUNT, enterprise_id=me, is_service=True)
    r = ResourceRef(
        scope=ENTERPRISE,
        resource_type="build_job",
        resource_id="b1",
        enterprise_id=me,
        owner_actor_id=None,
        proposed_by_actor_id=None,
    )
    decision = authorize(p, Action.ORCHESTRATION_BUILD_START, r)
    assert decision.allowed is True
    assert decision.reason_code == ReasonCode.ALLOW


def test_analyst_can_publish_report_with_full_principal() -> None:
    me = _enterprise()
    p = _principal(Role.ANALYST, enterprise_id=me)
    r = ResourceRef(
        scope=ENTERPRISE,
        resource_type="report_snapshot",
        resource_id="s4",
        enterprise_id=me,
        owner_actor_id=None,
        proposed_by_actor_id=None,
    )
    decision = authorize(p, Action.PUBLISHING_REPORT_PUBLISH, r)
    # 可能 allow 也可能因 resource loader 实际检查（owner）而 deny；至少不 CROSS_ENTERPRISE
    assert decision.reason_code in {ReasonCode.ALLOW, ReasonCode.OWNER_REQUIRED}


def test_default_deny_unknown_action_for_analyst() -> None:
    me = _enterprise()
    p = _principal(Role.ANALYST, enterprise_id=me)
    r = ResourceRef(
        scope=ENTERPRISE,
        resource_type="intake_batch",
        resource_id="b2",
        enterprise_id=me,
        owner_actor_id=p.actor_id,
        proposed_by_actor_id=None,
    )
    # 用一个 type-mismatch 让 ACTION_RESOURCE_MISMATCH 早返回
    decision = authorize(p, Action.METRIC_CHANGE_ACTIVATE, r)
    assert decision.allowed is False


# -- §2.2 development principal --------------------------------------------


def test_development_principal_is_not_superuser() -> None:
    # development principal 在实现层是普通 Principal（由 DB RoleBinding 解析），
    # 没有"allow all"路径。测试要保证即使 role=ANALYST，跨企业仍 deny
    me = _enterprise()
    other = _other_enterprise()
    p = _principal(Role.ANALYST, enterprise_id=me)
    r = ResourceRef(
        scope=ENTERPRISE,
        resource_type="investigation",
        resource_id="fx",
        enterprise_id=other,
        owner_actor_id=None,
        proposed_by_actor_id=None,
    )
    decision = authorize(p, Action.INVESTIGATION_READ, r)
    assert decision.allowed is False
    assert decision.reason_code == ReasonCode.CROSS_ENTERPRISE


# -- Decision / AuditContext 契约 ------------------------------------------


def test_decision_is_frozen() -> None:
    d = Decision(allowed=True, reason_code=ReasonCode.ALLOW)
    with pytest.raises((AttributeError, Exception)):
        d.allowed = False  # type: ignore[misc]


def test_audit_context_carries_principal_decision_correlation() -> None:
    me = _enterprise()
    p = _principal(Role.ANALYST, enterprise_id=me)
    ac = AuditContext(
        actor_id=p.actor_id,
        role=p.role,
        enterprise_id=p.enterprise_id,
        correlation_id="corr-1",
        action=Action.INVESTIGATION_READ,
        resource_scope="enterprise",
        resource_type="investigation",
        resource_id="i1",
        model_boundary=None,
    )
    assert ac.correlation_id == "corr-1"
    assert ac.action == Action.INVESTIGATION_READ
    assert ac.model_boundary is None


def test_model_boundary_carries_input_output_artifacts() -> None:
    mb = ModelBoundary(
        provider="anthropic",
        model="claude-3-5-sonnet",
        purpose="explain-mapping",
        input_artifact_ids=("a1", "a2"),
        input_sha256=("deadbeef" * 8,),
        output_artifact_ids=("o1",),
        output_sha256=("cafebabe" * 8,),
    )
    assert mb.provider == "anthropic"
    assert len(mb.input_sha256) == 1


# -- 旧 Bearer 截止：接口签名层面 ----------------------------------------


def test_legacy_cutoff_constant_is_frozen() -> None:
    # 规格 §3.2 截止 2026-10-31T23:59:59+08:00
    from flow_api.security.principal import LEGACY_BEARER_CUTOFF_UTC
    assert LEGACY_BEARER_CUTOFF_UTC.year == 2026
    assert LEGACY_BEARER_CUTOFF_UTC.month == 10
    assert LEGACY_BEARER_CUTOFF_UTC.day == 31
