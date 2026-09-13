"""deny-by-default 授权纯函数（S01 安全 ABI 最小实现）。

规格：docs/40_specs/security/internal-workbench-rbac-audit-v1.md §4 权限矩阵。

- 没有明确 allow 即拒绝；
- 跨企业默认拒绝（resource 携带 enterprise_id 且与 principal 不一致）；
- 规则不可自批（metric:rule.approve 时 proposed_by == actor_id 即拒绝）；
- AI 与服务账户无发布/冻结/审批权（矩阵中不授予，无例外通道）；
- DEVELOPMENT 角色仅存在于本机开发模式，全量放行。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from flow_api.security.principal import Principal, Role

_HUMAN_READ = frozenset(
    {Role.ANALYST, Role.FINANCE_BP, Role.RULE_OWNER, Role.AI_ANALYST, Role.AI_CFO}
)
_ALL_READ = _HUMAN_READ | {Role.SERVICE_ACCOUNT}
_INTAKE_WRITE = frozenset({Role.ANALYST, Role.SERVICE_ACCOUNT})

# action -> 允许的角色集合（不在表内 = deny-by-default）
GRANTS: dict[str, frozenset[Role]] = {
    # intake
    "intake:batch.create": frozenset({Role.ANALYST, Role.FINANCE_BP, Role.SERVICE_ACCOUNT}),
    "intake:batch.read": _ALL_READ,
    "intake:source.upload": frozenset({Role.ANALYST, Role.FINANCE_BP, Role.SERVICE_ACCOUNT}),
    "intake:source.read": _ALL_READ,
    "intake:source.validate": _INTAKE_WRITE,
    "intake:template.read": _ALL_READ,
    "intake:mapping.propose": _INTAKE_WRITE,
    "intake:mapping.confirm": _INTAKE_WRITE,  # 映射确认：审计点
    "intake:mapping.override": _INTAKE_WRITE,  # 人工 override：审计点
    "intake:issue.acknowledge": _INTAKE_WRITE,
    "intake:import.read": _ALL_READ,
    "intake:import.publish": frozenset({Role.ANALYST}),  # 导入发布：唯一人工发布权
    # investigations
    "investigation:read": _ALL_READ,
    "investigation:evidence.decide": frozenset({Role.ANALYST}),  # 证据确认/驳回
    "investigation:conclusion.save": frozenset({Role.ANALYST, Role.AI_ANALYST}),  # AI 生成候选
    "investigation:transition": frozenset({Role.ANALYST}),  # 状态迁移/例外
    # metric library（专业治理）
    "metric:read": _ALL_READ,
    "metric:import": frozenset({Role.RULE_OWNER}),
    "metric:retire": frozenset({Role.RULE_OWNER}),
    "metric:rule.propose": frozenset({Role.ANALYST, Role.RULE_OWNER, Role.AI_ANALYST}),
    "metric:rule.approve": frozenset({Role.RULE_OWNER}),  # 另加不可自批检查
    "metric:rule.retire": frozenset({Role.RULE_OWNER}),
    "metric:impact.analyze": frozenset(
        {Role.ANALYST, Role.RULE_OWNER, Role.AI_ANALYST, Role.SERVICE_ACCOUNT}
    ),
    # statements（公开财报）
    "statement:source.upload": _INTAKE_WRITE,
    "statement:read": _ALL_READ,
    "statement:correction.add": _INTAKE_WRITE,  # 事实修订：审计点
    "statement:publish": frozenset({Role.ANALYST}),  # 报告发布：唯一人工发布权
    "statement:snapshot.freeze": frozenset({Role.ANALYST}),  # 冻结属发布链
    # orchestration
    "orchestration:build": _INTAKE_WRITE,
    "orchestration:read": _ALL_READ,
    # copilot（模型边界审计点）
    "copilot:ask": frozenset({Role.ANALYST, Role.AI_ANALYST, Role.AI_CFO, Role.SERVICE_ACCOUNT}),
    "copilot:explain": frozenset(
        {Role.ANALYST, Role.AI_ANALYST, Role.AI_CFO, Role.SERVICE_ACCOUNT}
    ),
    "copilot:outline": frozenset(
        {Role.ANALYST, Role.AI_ANALYST, Role.AI_CFO, Role.SERVICE_ACCOUNT}
    ),
    # publishing / operations（owner=Sol 串行接线后使用同一动作名）
    "report:freeze": frozenset({Role.ANALYST}),
    "report:publish": frozenset({Role.ANALYST}),
}

_SELF_APPROVAL_GUARDED = frozenset({"metric:rule.approve", "metric:rule.retire"})


@dataclass(frozen=True)
class ResourceContext:
    """被访问资源的授权上下文；enterprise_id 为 None 表示公开/平台级资源。"""

    kind: str
    resource_id: str | None
    enterprise_id: UUID | None
    attributes: dict[str, str] = field(default_factory=dict)

    @classmethod
    def unscoped(cls) -> ResourceContext:
        return cls(kind="unscoped", resource_id=None, enterprise_id=None)


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str


def authorize(principal: Principal, action: str, resource: ResourceContext) -> Decision:
    """纯函数授权；路由不得散落角色字符串，一律经此判定。"""

    if principal.role == Role.DEVELOPMENT:
        return Decision(True, "development principal")

    grants = GRANTS.get(action)
    if grants is None:
        return Decision(False, f"deny-by-default：动作 {action!r} 未登记授权矩阵")
    if principal.role not in grants:
        return Decision(False, f"角色 {principal.role} 无权执行 {action}（deny-by-default）")

    if resource.enterprise_id is not None and principal.enterprise_id != resource.enterprise_id:
        return Decision(
            False,
            f"跨企业默认拒绝：principal 企业 {principal.enterprise_id} "
            f"!= 资源企业 {resource.enterprise_id}",
        )

    if (
        action in _SELF_APPROVAL_GUARDED
        and resource.attributes.get("proposed_by") is not None
        and resource.attributes.get("proposed_by") == principal.actor_id
    ):
        return Decision(False, "规则不可自批：提议者与审批者不得为同一人")

    return Decision(True, "allow")


__all__ = ["Decision", "GRANTS", "ResourceContext", "authorize"]
