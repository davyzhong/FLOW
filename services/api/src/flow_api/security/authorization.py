"""S01 §2 + §4 授权域：Action / ResourceRef / ReasonCode / Decision + 纯 `authorize`。

判定顺序（§4.2 八步短路）：
  1. Principal 合法且 role/service flag 一致：否则 INVALID_PRINCIPAL
  2. ResourceRef 及 scope/enterprise 组合合法：否则 INVALID_RESOURCE
  3. action 与 resource_type 是 policy 的精确组合：否则 ACTION_RESOURCE_MISMATCH
  4. enterprise scope 下 Principal enterprise 为空 → ENTERPRISE_REQUIRED；
     不相等 → CROSS_ENTERPRISE；public 不做 enterprise 比较
  5. role 不在 action 显式 allow set → ROLE_FORBIDDEN；未知 action 默认拒绝
  6. 要求本人资源时 owner 缺失 → OWNER_REQUIRED；不相等 → NOT_RESOURCE_OWNER
  7. 正式规则审批/激活/退役缺 proposed_by → PROPOSER_REQUIRED；
     与 Principal actor 相同 → SELF_APPROVAL_FORBIDDEN
  8. 全部通过 → ALLOW

allow set（§4.3 6 角色 × 56 Action）：
  - finance_bp / rule_owner / ai_analyst / ai_cfo / service_account 显式 allow 列表；
  - analyst 允许除 `metric.change.activate` / `metric.change.retire` 之外的全部 Action；
  - `*_PUBLISH` / `*_FREEZE` / `*_RENDER_AND_FREEZE` 只允许 analyst。
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Final
from uuid import UUID

from flow_api.security.principal import Principal, ResourceScope, Role

# ---------------------------------------------------------------------------
# §2.1 Action 冻结枚举（56 项；与规格完全一致）
# ---------------------------------------------------------------------------


class Action(StrEnum):
    SYSTEM_HEALTH_READ = "system.health.read"
    WORKSPACE_METADATA_READ = "workspace.metadata.read"
    INTAKE_TEMPLATE_READ = "intake.template.read"
    INTAKE_BATCH_CREATE = "intake.batch.create"
    INTAKE_SOURCE_UPLOAD = "intake.source.upload"
    INTAKE_SOURCE_PROFILE_READ = "intake.source.profile.read"
    INTAKE_MAPPING_PROPOSE = "intake.mapping.propose"
    INTAKE_MAPPING_CONFIRM = "intake.mapping.confirm"
    INTAKE_MAPPING_OVERRIDE = "intake.mapping.override"
    INTAKE_SOURCE_VALIDATE = "intake.source.validate"
    INTAKE_ISSUE_ACKNOWLEDGE = "intake.issue.acknowledge"
    INTAKE_IMPORT_PUBLISH = "intake.import.publish"
    INTAKE_VERSION_READ = "intake.version.read"
    INTAKE_CLEANING_SUMMARY_READ = "intake.cleaning_summary.read"
    INTAKE_STANDARDIZED_WORKBOOK_READ = "intake.standardized_workbook.read"
    DASHBOARD_OVERVIEW_READ = "dashboard.overview.read"
    INVESTIGATION_LIST = "investigation.list"
    INVESTIGATION_READ = "investigation.read"
    INVESTIGATION_EVIDENCE_DECIDE = "investigation.evidence.decide"
    INVESTIGATION_CONCLUSION_WRITE = "investigation.conclusion.write"
    INVESTIGATION_TRANSITION = "investigation.transition"
    COPILOT_INVESTIGATION_ASK = "copilot.investigation.ask"
    COPILOT_MAPPING_EXPLAIN = "copilot.mapping.explain"
    COPILOT_REPORT_OUTLINE_GENERATE = "copilot.report_outline.generate"
    PUBLISHING_REPORT_PUBLISH = "publishing.report.publish"
    PUBLISHING_ATTEMPT_READ = "publishing.attempt.read"
    PUBLISHING_SNAPSHOT_FREEZE = "publishing.snapshot.freeze"
    PUBLISHING_CANDIDATE_READ = "publishing.candidate.read"
    PUBLISHING_SNAPSHOT_READ = "publishing.snapshot.read"
    PUBLISHING_ARTIFACT_DOWNLOAD = "publishing.artifact.download"
    STATEMENT_SOURCE_UPLOAD = "statement.source.upload"
    STATEMENT_SOURCE_READ = "statement.source.read"
    STATEMENT_REPORT_READ = "statement.report.read"
    STATEMENT_PROJECTION_READ = "statement.projection.read"
    STATEMENT_CORRECTION_CREATE = "statement.correction.create"
    STATEMENT_CORRECTION_READ = "statement.correction.read"
    STATEMENT_REPORT_PUBLISH = "statement.report.publish"
    METRIC_LIBRARY_READ = "metric_library.read"
    METRIC_LIBRARY_IMPORT = "metric_library.import"
    METRIC_LIBRARY_RETIRE = "metric_library.retire"
    METRIC_CHANGE_PROPOSE = "metric.change.propose"
    METRIC_CHANGE_ACTIVATE = "metric.change.activate"
    METRIC_CHANGE_RETIRE = "metric.change.retire"
    METRIC_EVENT_READ = "metric.event.read"
    METRIC_IMPACT_ANALYZE = "metric.impact.analyze"
    ORCHESTRATION_BUILD_START = "orchestration.build.start"
    ORCHESTRATION_BUILD_READ = "orchestration.build.read"
    OBJECTIVE_SNAPSHOT_READ_AND_FREEZE = "objective_snapshot.read_and_freeze"
    OBJECTIVE_SNAPSHOT_FREEZE = "objective_snapshot.freeze"
    OBJECTIVE_SNAPSHOT_RENDER_AND_FREEZE = "objective_snapshot.render_and_freeze"
    WORKBENCH_REPORT_READ = "workbench.report.read"
    OPERATIONS_PUBLIC_READ = "operations.public.read"
    OPERATIONS_OVERVIEW_READ = "operations.overview.read"
    OPERATIONS_SNAPSHOT_READ = "operations.snapshot.read"
    OPERATIONS_REPORT_PUBLISH = "operations.report.publish"
    OPERATIONS_ATTEMPT_READ = "operations.attempt.read"
    OPERATIONS_SNAPSHOT_FREEZE = "operations.snapshot.freeze"
    OPERATIONS_RENDER_AND_FREEZE = "operations.render_and_freeze"
    METRIC_SNAPSHOT_READ = "metric_snapshot.read"
    ANALYSIS_RUN_READ = "analysis_run.read"


# ---------------------------------------------------------------------------
# §2.1 ReasonCode 冻结枚举（15 项；规格 §2.1 + §4.2 全集）
# ---------------------------------------------------------------------------


class ReasonCode(StrEnum):
    ALLOW = "allow"
    AUTHENTICATION_REQUIRED = "authentication_required"
    CREDENTIAL_INVALID = "credential_invalid"
    LEGACY_TOKEN_EXPIRED = "legacy_token_expired"
    INVALID_PRINCIPAL = "invalid_principal"
    INVALID_RESOURCE = "invalid_resource"
    ACTION_RESOURCE_MISMATCH = "action_resource_mismatch"
    RESOURCE_SCOPE_UNRESOLVED = "resource_scope_unresolved"
    ENTERPRISE_REQUIRED = "enterprise_required"
    CROSS_ENTERPRISE = "cross_enterprise"
    ROLE_FORBIDDEN = "role_forbidden"
    OWNER_REQUIRED = "owner_required"
    NOT_RESOURCE_OWNER = "not_resource_owner"
    PROPOSER_REQUIRED = "proposer_required"
    SELF_APPROVAL_FORBIDDEN = "self_approval_forbidden"
    ROUTE_BLOCKED = "route_blocked"
    AUDIT_UNAVAILABLE = "audit_unavailable"


# ---------------------------------------------------------------------------
# §2.1 ResourceRef + Decision 冻结
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ResourceRef:
    scope: ResourceScope
    resource_type: str
    resource_id: str
    enterprise_id: UUID | None
    owner_actor_id: str | None
    proposed_by_actor_id: str | None

    def __post_init__(self) -> None:
        if self.scope not in ("public", "enterprise"):
            raise ValueError("ResourceRef.scope 必须是 'public' 或 'enterprise'")
        if not self.resource_type or not isinstance(self.resource_type, str):
            raise ValueError("ResourceRef.resource_type 必须是非空 str")
        if not self.resource_id or not isinstance(self.resource_id, str):
            raise ValueError("ResourceRef.resource_id 必须是非空 str")
        if self.scope == "public":
            if self.enterprise_id is not None:
                raise ValueError("public 资源必须 enterprise_id=None（§4.1）")
        else:
            if self.enterprise_id is None:
                raise ValueError("enterprise 资源必须 enterprise_id 非空（§4.1）")
        for name in ("owner_actor_id", "proposed_by_actor_id"):
            v = getattr(self, name)
            if v is not None and (not isinstance(v, str) or not v):
                raise ValueError(f"ResourceRef.{name} 必须是 None 或非空 str")


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason_code: ReasonCode


# ---------------------------------------------------------------------------
# §4.3 完整 allow set（6 角色 × Action 矩阵）
# ---------------------------------------------------------------------------


# finance_bp 显式 allow actions
_FINANCE_BP_ALLOW: Final[frozenset[Action]] = frozenset(
    {
        Action.SYSTEM_HEALTH_READ,
        Action.WORKSPACE_METADATA_READ,
        Action.INTAKE_TEMPLATE_READ,
        Action.INTAKE_BATCH_CREATE,
        Action.INTAKE_SOURCE_UPLOAD,
        Action.INTAKE_SOURCE_PROFILE_READ,
        Action.INTAKE_MAPPING_CONFIRM,
        Action.INTAKE_MAPPING_OVERRIDE,
        Action.INTAKE_ISSUE_ACKNOWLEDGE,
        Action.INTAKE_VERSION_READ,
        Action.INTAKE_CLEANING_SUMMARY_READ,
        Action.INTAKE_STANDARDIZED_WORKBOOK_READ,
        Action.INVESTIGATION_READ,
        Action.METRIC_SNAPSHOT_READ,
        Action.ANALYSIS_RUN_READ,
        Action.STATEMENT_SOURCE_READ,
        Action.STATEMENT_REPORT_READ,
        Action.STATEMENT_PROJECTION_READ,
        Action.STATEMENT_CORRECTION_READ,
        Action.WORKBENCH_REPORT_READ,
        Action.OPERATIONS_PUBLIC_READ,
        Action.OPERATIONS_OVERVIEW_READ,
        Action.OPERATIONS_SNAPSHOT_READ,
        Action.OPERATIONS_ATTEMPT_READ,
    }
)

# rule_owner 显式 allow actions
_RULE_OWNER_ALLOW: Final[frozenset[Action]] = frozenset(
    {
        Action.SYSTEM_HEALTH_READ,
        Action.WORKSPACE_METADATA_READ,
        Action.INTAKE_TEMPLATE_READ,
        Action.INVESTIGATION_READ,
        Action.METRIC_SNAPSHOT_READ,
        Action.ANALYSIS_RUN_READ,
        Action.METRIC_LIBRARY_READ,
        Action.METRIC_CHANGE_PROPOSE,
        Action.METRIC_CHANGE_ACTIVATE,
        Action.METRIC_CHANGE_RETIRE,
        Action.METRIC_EVENT_READ,
        Action.METRIC_IMPACT_ANALYZE,
        Action.STATEMENT_SOURCE_READ,
        Action.STATEMENT_REPORT_READ,
        Action.STATEMENT_PROJECTION_READ,
        Action.STATEMENT_CORRECTION_READ,
        Action.WORKBENCH_REPORT_READ,
        Action.OPERATIONS_PUBLIC_READ,
        Action.OPERATIONS_OVERVIEW_READ,
        Action.OPERATIONS_SNAPSHOT_READ,
        Action.OPERATIONS_ATTEMPT_READ,
    }
)

# ai_analyst 显式 allow actions
_AI_ANALYST_ALLOW: Final[frozenset[Action]] = frozenset(
    {
        Action.SYSTEM_HEALTH_READ,
        Action.WORKSPACE_METADATA_READ,
        Action.INTAKE_SOURCE_PROFILE_READ,
        Action.INVESTIGATION_READ,
        Action.METRIC_SNAPSHOT_READ,
        Action.ANALYSIS_RUN_READ,
        Action.COPILOT_INVESTIGATION_ASK,
        Action.COPILOT_MAPPING_EXPLAIN,
        Action.METRIC_LIBRARY_READ,
        Action.METRIC_IMPACT_ANALYZE,
        Action.STATEMENT_SOURCE_READ,
        Action.STATEMENT_REPORT_READ,
        Action.STATEMENT_PROJECTION_READ,
        Action.WORKBENCH_REPORT_READ,
        Action.OPERATIONS_PUBLIC_READ,
        Action.OPERATIONS_OVERVIEW_READ,
    }
)

# ai_cfo 显式 allow actions
_AI_CFO_ALLOW: Final[frozenset[Action]] = frozenset(
    {
        Action.SYSTEM_HEALTH_READ,
        Action.WORKSPACE_METADATA_READ,
        Action.INVESTIGATION_READ,
        Action.METRIC_SNAPSHOT_READ,
        Action.ANALYSIS_RUN_READ,
        Action.COPILOT_INVESTIGATION_ASK,
        Action.COPILOT_REPORT_OUTLINE_GENERATE,
        Action.STATEMENT_REPORT_READ,
        Action.STATEMENT_PROJECTION_READ,
        Action.WORKBENCH_REPORT_READ,
        Action.OPERATIONS_PUBLIC_READ,
        Action.OPERATIONS_OVERVIEW_READ,
    }
)

# service_account 显式 allow actions
_SERVICE_ACCOUNT_ALLOW: Final[frozenset[Action]] = frozenset(
    {
        Action.SYSTEM_HEALTH_READ,
        Action.WORKSPACE_METADATA_READ,
        Action.INTAKE_TEMPLATE_READ,
        Action.INTAKE_SOURCE_PROFILE_READ,
        Action.INTAKE_SOURCE_VALIDATE,
        Action.ORCHESTRATION_BUILD_START,
        Action.ORCHESTRATION_BUILD_READ,
        Action.STATEMENT_SOURCE_READ,
        Action.STATEMENT_REPORT_READ,
        Action.STATEMENT_PROJECTION_READ,
        Action.OPERATIONS_PUBLIC_READ,
    }
)

# analyst 不允许 metric.change.activate / metric.change.retire
_ANALYST_FORBIDDEN_OVERRIDE: Final[frozenset[Action]] = frozenset(
    {Action.METRIC_CHANGE_ACTIVATE, Action.METRIC_CHANGE_RETIRE}
)

# §4.2 step5 需 owner 校验的 action（owner 缺/不等 → OWNER_REQUIRED / NOT_RESOURCE_OWNER）
_OWNER_REQUIRED_ACTIONS: Final[frozenset[Action]] = frozenset(
    {
        Action.INTAKE_BATCH_CREATE,
        Action.INTAKE_SOURCE_UPLOAD,
        Action.INTAKE_SOURCE_PROFILE_READ,
        Action.INTAKE_MAPPING_PROPOSE,
        Action.INTAKE_MAPPING_CONFIRM,
        Action.INTAKE_MAPPING_OVERRIDE,
        Action.INTAKE_SOURCE_VALIDATE,
        Action.INTAKE_ISSUE_ACKNOWLEDGE,
        Action.INTAKE_CLEANING_SUMMARY_READ,
        Action.INTAKE_STANDARDIZED_WORKBOOK_READ,
        Action.INVESTIGATION_READ,
        Action.METRIC_SNAPSHOT_READ,
        Action.ANALYSIS_RUN_READ,
        Action.INVESTIGATION_EVIDENCE_DECIDE,
        Action.INVESTIGATION_CONCLUSION_WRITE,
        Action.INVESTIGATION_TRANSITION,
        Action.COPILOT_INVESTIGATION_ASK,
        Action.COPILOT_MAPPING_EXPLAIN,
        Action.COPILOT_REPORT_OUTLINE_GENERATE,
        Action.PUBLISHING_REPORT_PUBLISH,
        Action.PUBLISHING_ATTEMPT_READ,
        Action.PUBLISHING_SNAPSHOT_FREEZE,
        Action.PUBLISHING_CANDIDATE_READ,
        Action.PUBLISHING_SNAPSHOT_READ,
        Action.PUBLISHING_ARTIFACT_DOWNLOAD,
        Action.STATEMENT_CORRECTION_CREATE,
        Action.STATEMENT_CORRECTION_READ,
        Action.METRIC_LIBRARY_IMPORT,
        Action.METRIC_LIBRARY_RETIRE,
        Action.METRIC_CHANGE_PROPOSE,
        Action.OBJECTIVE_SNAPSHOT_READ_AND_FREEZE,
        Action.OBJECTIVE_SNAPSHOT_FREEZE,
        Action.OBJECTIVE_SNAPSHOT_RENDER_AND_FREEZE,
        Action.OPERATIONS_REPORT_PUBLISH,
        Action.OPERATIONS_ATTEMPT_READ,
        Action.OPERATIONS_SNAPSHOT_FREEZE,
        Action.OPERATIONS_RENDER_AND_FREEZE,
    }
)

# §4.2 step7 需 proposed_by 校验的 action（审批/激活/退役）
_PROPOSER_REQUIRED_ACTIONS: Final[frozenset[Action]] = frozenset(
    {
        Action.METRIC_CHANGE_ACTIVATE,
        Action.METRIC_CHANGE_RETIRE,
    }
)


# ---------------------------------------------------------------------------
# §4.2 authorize 纯函数
# ---------------------------------------------------------------------------


def _step1_check_principal(principal: Principal) -> Decision | None:
    """Step 1: Principal 合法且 role/service flag 一致。"""
    # Principal 构造已硬约束，运行时只需检查关键一致
    if not isinstance(principal, Principal):
        return Decision(False, ReasonCode.INVALID_PRINCIPAL)
    if principal.role is Role.SERVICE_ACCOUNT and not principal.is_service_account:
        return Decision(False, ReasonCode.INVALID_PRINCIPAL)
    if principal.is_service_account and principal.role is not Role.SERVICE_ACCOUNT:
        return Decision(False, ReasonCode.INVALID_PRINCIPAL)
    if principal.enterprise_id is None:
        # §3.1.4 所有角色必须 enterprise_id 非空
        return Decision(False, ReasonCode.INVALID_PRINCIPAL)
    return None


def _step2_check_resource(resource: ResourceRef) -> Decision | None:
    """Step 2: ResourceRef 及 scope/enterprise 组合合法。"""
    if not isinstance(resource, ResourceRef):
        return Decision(False, ReasonCode.INVALID_RESOURCE)
    # ResourceRef 构造已硬约束 scope/enterprise；loader 显式标 `blocked:` 时应在
    # 进入 authorize 前由 route policy 形成 RESOURCE_SCOPE_UNRESOLVED（§4.2 step 2 注释）
    if resource.scope not in ("public", "enterprise"):
        return Decision(False, ReasonCode.INVALID_RESOURCE)
    return None


def _step4_enterprise_scope(
    principal: Principal,
    resource: ResourceRef,
) -> Decision | None:
    """Step 4: enterprise scope 下的企业比较。"""
    if resource.scope == "enterprise":
        if principal.enterprise_id is None:
            return Decision(False, ReasonCode.ENTERPRISE_REQUIRED)
        if principal.enterprise_id != resource.enterprise_id:
            return Decision(False, ReasonCode.CROSS_ENTERPRISE)
    # public scope 不做 enterprise 比较（§4.2）
    return None


def _step5_role_in_allow_set(
    principal: Principal,
    action: Action,
    resource: ResourceRef,
) -> Decision | None:
    """Step 5: role 在 action 显式 allow set。"""
    if principal.role is Role.ANALYST:
        # analyst 允许除 metric.change.activate / retire 之外的全部 Action
        if action in _ANALYST_FORBIDDEN_OVERRIDE:
            return Decision(False, ReasonCode.ROLE_FORBIDDEN)
        # 其他全部 allow（owner/proposer 检查在 step 6/7）
        return None
    if principal.role is Role.FINANCE_BP:
        if action in _FINANCE_BP_ALLOW:
            return None
        return Decision(False, ReasonCode.ROLE_FORBIDDEN)
    if principal.role is Role.RULE_OWNER:
        if action in _RULE_OWNER_ALLOW:
            return None
        return Decision(False, ReasonCode.ROLE_FORBIDDEN)
    if principal.role is Role.AI_ANALYST:
        if action in _AI_ANALYST_ALLOW:
            return None
        return Decision(False, ReasonCode.ROLE_FORBIDDEN)
    if principal.role is Role.AI_CFO:
        if action in _AI_CFO_ALLOW:
            return None
        return Decision(False, ReasonCode.ROLE_FORBIDDEN)
    if principal.role is Role.SERVICE_ACCOUNT:
        if action in _SERVICE_ACCOUNT_ALLOW:
            return None
        return Decision(False, ReasonCode.ROLE_FORBIDDEN)
    # 未知 role → ROLE_FORBIDDEN
    return Decision(False, ReasonCode.ROLE_FORBIDDEN)


def _step6_owner_check(
    principal: Principal,
    action: Action,
    resource: ResourceRef,
) -> Decision | None:
    """Step 6: 要求本人资源时 owner 缺/不等。

    Bootstrap 语义（R1 记录）：`owner_actor_id is None` 表示该资源的创建者列
    尚未由服务层落值（内部工作台 owner 精细化前的引导数据）；此时企业隔离已由
    step4 保证，owner 检查放行。owner 有值且不等仍一律 NOT_RESOURCE_OWNER。
    """
    if action not in _OWNER_REQUIRED_ACTIONS:
        return None
    if resource.owner_actor_id is None:
        return None
    if resource.owner_actor_id != principal.actor_id:
        return Decision(False, ReasonCode.NOT_RESOURCE_OWNER)
    return None


def _step7_proposer_check(
    principal: Principal,
    action: Action,
    resource: ResourceRef,
) -> Decision | None:
    """Step 7: 正式规则审批/激活/退役的 proposed_by 与 self-approval 检查。"""
    if action not in _PROPOSER_REQUIRED_ACTIONS:
        return None
    if resource.proposed_by_actor_id is None:
        return Decision(False, ReasonCode.PROPOSER_REQUIRED)
    if resource.proposed_by_actor_id == principal.actor_id:
        return Decision(False, ReasonCode.SELF_APPROVAL_FORBIDDEN)
    return None


def authorize(principal: Principal, action: Action, resource: ResourceRef) -> Decision:
    """§4.2 八步短路判定。

    测试断言首个 reason code（每步命中即返回，不进入下一步）。
    """
    checks: tuple[Callable[[], Decision | None], ...] = (
        lambda: _step1_check_principal(principal),
        lambda: _step2_check_resource(resource),
        # step3 (action×resource_type 精确组合) 在 route policy 接线处执行（Task 2B）。
        # 纯函数层允许任意 action×resource_type 组合进入 step4+，由 step5 allow set 决定最终结果。
        lambda: _step4_enterprise_scope(principal, resource),
        lambda: _step5_role_in_allow_set(principal, action, resource),
        lambda: _step6_owner_check(principal, action, resource),
        lambda: _step7_proposer_check(principal, action, resource),
    )
    for check in checks:
        decision = check()
        if decision is not None:
            return decision
    return Decision(allowed=True, reason_code=ReasonCode.ALLOW)
