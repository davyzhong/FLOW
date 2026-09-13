---
doc_id: FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1
title: 内部工作台 RBAC 与追加式审计规格 V1
doc_type: specification
status: approved
version: 1.1
created_at: 2026-09-13
updated_at: 2026-09-13
owner: FLOW
decision_refs: [D052, D053, D054]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: services/api
---

# 内部工作台 RBAC 与追加式审计规格 V1

- 依据：战略重构设计 V1.1 §4、§4.1、§11；产品原则；S01 Task 6。
- 目标：deny-by-default 授权、企业隔离、不可伪造身份、追加式审计，以及发布对象副作用的可恢复事务边界。
- 状态纪律：本文已转为 `approved`（2026-09-13 主协调者终审清零 P1/P2 + F1/F2 裁决后由用户明确批准；见 `docs/80_reviews/2026-09-13-s01-security-spec-v1.1-coordinator-review.md`）。本轮合同收紧后的最终字节即本文件，任何 ABI/枚举/allow set/截止/retention 偏差必须先修订本文并重新批准。
- 路由权威清单：[`route-inventory-v1.tsv`](route-inventory-v1.tsv)。清单按最终 `api_router` 的实际挂载结果生成，路径名和 HTTP method 均不能替代实际副作用判断。

## 1. 范围与强制输出

S01 Task 6 必须同时交付：

1. 本文 §2 的不可变身份、动作、资源和判定类型；
2. 纯函数 `authorize` 与集中 dependency `require_action`；
3. credential → Principal 解析、数据库 RoleBinding 和 route policy；
4. 迁移 `0026_security_audit`：RoleBinding、AuditEvent、追加式约束与索引；
5. publishing 与 operations 共用的四阶段发布 ABI；
6. 全挂载路由的机器可读 inventory、守护扫描和逐入口测试；
7. 认证、允许、拒绝均在业务执行前完成独立、短事务、durable 的审计。

## 2. 冻结类型

### 2.1 Role、Principal、Action、ResourceRef、Decision

以下枚举值是 V1.1 的完整集合。实现可换用等价的 `StrEnum`/冻结 dataclass，但不得新增隐式角色、通配动作或 `superuser` 分支。

```python
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal
from uuid import UUID


class Role(StrEnum):
    FINANCE_BP = "finance_bp"
    ANALYST = "analyst"
    RULE_OWNER = "rule_owner"
    AI_ANALYST = "ai_analyst"
    AI_CFO = "ai_cfo"
    SERVICE_ACCOUNT = "service_account"


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


ResourceScope = Literal["public", "enterprise"]


@dataclass(frozen=True)
class Principal:
    actor_id: str
    role: Role
    enterprise_id: UUID | None
    is_service_account: bool


@dataclass(frozen=True)
class ResourceRef:
    scope: ResourceScope
    resource_type: str
    resource_id: str
    enterprise_id: UUID | None
    owner_actor_id: str | None
    proposed_by_actor_id: str | None


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


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason_code: ReasonCode
```

字段约束：

- `actor_id` 为认证系统的稳定、非空主体 ID，不是显示名；大小写敏感。
- `role == Role.SERVICE_ACCOUNT` 当且仅当 `is_service_account is True`；任何不一致 Principal 无效。
- 人类和 AI 角色的 `is_service_account` 必须为 `False`；服务账号不得假扮 AI 或人类角色。
- `scope == "enterprise"` 时 `enterprise_id` 必须非空，并由数据库资源链解析；不得从 request body、query 或 Principal 回填。
- `scope == "public"` 时 `enterprise_id` 必须为空，且 `resource_type` 必须在 route policy 的显式 public 类型集合中。
- `owner_actor_id` 只用于“本人任务/被指派任务”约束；需要 owner 却无法从数据库解析时拒绝。
- `proposed_by_actor_id` 用于不可自批；审批动作缺该值必须拒绝，不能把“未知提议者”当作可审批。

### 2.2 development principal 不是超级用户

development 不得绕过 `authorize`。本地无 Bearer 的兼容入口仅在 `FLOW_ENV=development` 且显式配置 `FLOW_DEV_ACTOR_ID` 时存在：实现用该 actor 查询数据库中唯一 active RoleBinding 生成普通 Principal。缺 binding、binding 不唯一、enterprise 不一致均 401；不自动创建 binding，也没有 `allow_all`、跨企业、发布或审批例外。未配置 `FLOW_DEV_ACTOR_ID` 时，除显式匿名 public 路由外仍为 401。

## 3. 身份配置与 RoleBinding 权威

### 3.1 `FLOW_IDENTITY_BINDINGS_JSON`

值必须是非空 JSON 数组；每项必须**恰好**包含 `token_sha256`、`actor_id`、`role`、`enterprise_id`、`is_service_account` 五字段，未知字段、缺字段、空数组和非数组均令服务启动失败。

digest 唯一合法格式为：

```python
token_sha256 = hashlib.sha256(token.encode("utf-8")).hexdigest()
```

它必须匹配 `^[0-9a-f]{64}$`，不接受 `sha256:` 前缀、大写、base64、空白、对原始 header 的 hash 或二次 hash。请求端去掉 `Bearer ` scheme 后，对 token 的原始 UTF-8 字节计算一次 SHA-256，再使用 `hmac.compare_digest` 与配置 digest 比较；不得日志记录 token。

启动校验按以下规则 fail-fast，所有环境相同：

1. `token_sha256` 重复，拒绝；`actor_id` 重复，即使五字段相同也拒绝；
2. 同一 actor 同时出现在新配置、legacy 映射或 development 配置且声明冲突，拒绝；
3. `role=service_account` 与 `is_service_account=true` 必须同时成立，其他组合拒绝；
4. 人类、AI、服务账号均必须有固定 `enterprise_id`，不存在跨企业 service account；
5. 数据库是 role 和 enterprise 的唯一运行时权威：每个配置 actor 必须恰好匹配一条 active RoleBinding，且数据库的 `role`、`enterprise_id`、`is_service_account` 与配置声明完全相同，否则启动失败；配置声明只用于启动对账，不可覆盖数据库；
6. 非 development 环境配置缺失或合法项为零时启动失败；数据库不可达、查询失败或重复 active binding 同样启动失败；
7. 每次解析 Principal 都读取或使用有明确失效机制的 RoleBinding 缓存；binding 被撤销后不得继续使用无期限缓存。

RoleBinding 的冻结数据库字段为 `id UUID`、`actor_id str`、`role Role`、`enterprise_id UUID`、`is_service_account bool`、`active bool`、`created_at timestamptz`、`revoked_at timestamptz|null`。数据库必须用 partial unique constraint 保证每个 `actor_id` 最多一条 `active=true`；`active=false` 必须有 `revoked_at`，active binding 的 `revoked_at` 必须为空。角色或企业变更采用“撤销旧行、追加新行”，不覆盖审计历史。

### 3.2 旧 Bearer 的无条件截止

- 兼容变量为 `FLOW_AUTH_TOKEN`，其 actor、企业固定为 `FLOW_LEGACY_ACTOR_ID`、`FLOW_LEGACY_ENTERPRISE_ID`，数据库必须存在完全匹配的 active `service_account` RoleBinding。
- 截止瞬间为 `2026-10-31T23:59:59+08:00`（`2026-10-31T15:59:59Z`），仅当可信 UTC 时钟 `now <= cutoff` 时可解析。
- 当 `now > cutoff` 时，所有环境无条件拒绝旧 token：配置了 `FLOW_AUTH_TOKEN` 则启动失败；请求携带该 token 仍返回 401 / `legacy_token_expired`。development、仅剩旧 token、binding active 均不是例外。
- 截止前 legacy Principal 仍走完整 matrix，只拥有 service_account 的显式最小动作，永远没有 freeze/publish/approve 权限。

### 3.3 请求体身份字段不可成为权威

授权和审计中的 actor、role、enterprise 只能来自 Principal。request body/query/path 内名为 `actor`、`actor_id`、`operator`、`reviewer`、`approved_by`、`enterprise_id` 的字段不得进入 Principal、ResourceRef enterprise、Decision 或 AuditEvent actor 字段。

新 schema 删除这些身份字段。兼容 schema 尚未删除时：相同值也仅忽略并向 service 传 `principal.actor_id`；与 Principal 冲突则在 allow 审计 durable 后返回 409 `actor_conflict`，另追加业务校验事件。任何情况下都不得把请求值写成审计 actor。资源 enterprise 只允许由数据库 lineage 或显式 public policy 得出。

## 4. public / enterprise 语义和授权顺序

### 4.1 scope 语义

- `public` 表示不含企业私有数据的公开财报、公开经营披露、静态健康/模板/产品元数据；它不是“可跨企业读取”。public ResourceRef 必须 `enterprise_id=None`。
- `enterprise` 表示企业内部数据、配置、知识上下文、对象、任务和审计；ResourceRef 必须带由数据库链解析出的 enterprise。
- endpoint 若可处理 public/internal 两类对象，loader 必须按数据库 `module_kind` 分流；`legacy` 或断裂 lineage 返回 `RESOURCE_SCOPE_UNRESOLVED`，不得借 Principal enterprise 猜测。
- service account 与其他角色执行相同 scope 比较，没有跨企业、平台级或“内部服务可信”例外。
- 仅 `system.health.read` 可显式 `allow_anonymous=True`。`public` 只描述数据 scope，不授予匿名访问；operations、statements、workbench 和其他 public 动作仍需 Principal 与角色检查。本规格不扩大任何现有匿名面。

### 4.2 精确判定顺序

```python
def authorize(principal: Principal, action: Action, resource: ResourceRef) -> Decision:
    raise NotImplementedError
```

实现必须按以下顺序短路，测试断言首个 reason code：

1. Principal 合法且 role/service flag 一致，否则 `INVALID_PRINCIPAL`；
2. ResourceRef 及 scope/enterprise 组合合法，否则 `INVALID_RESOURCE`；loader 无法解析时在进入纯函数前形成 deny `RESOURCE_SCOPE_UNRESOLVED`；
3. action 与 `resource_type` 是 policy 的精确组合，否则 `ACTION_RESOURCE_MISMATCH`；
4. enterprise scope 下 Principal enterprise 为空返回 `ENTERPRISE_REQUIRED`，不相等返回 `CROSS_ENTERPRISE`；public 不做 enterprise 相等比较；
5. role 不在 action 显式 allow set 返回 `ROLE_FORBIDDEN`；未知 action 默认拒绝；
6. 要求本人资源时，owner 缺失返回 `OWNER_REQUIRED`，不相等返回 `NOT_RESOURCE_OWNER`；
7. 正式规则审批/激活/退役缺 proposed_by 返回 `PROPOSER_REQUIRED`，与 Principal actor 相同返回 `SELF_APPROVAL_FORBIDDEN`；
8. 全部通过才返回 `Decision(True, ReasonCode.ALLOW)`。

认证缺失/无效发生在 `authorize` 前，分别为 401 `authentication_required` / `credential_invalid` / `legacy_token_expired`，但仍须按 §6 先写 durable 审计。

### 4.3 完整 allow set

下列集合是权限矩阵机器真相；每个 Role × 每个 Action 不在集合中即 deny。`*_PUBLISH`、`*_FREEZE`、`*_RENDER_AND_FREEZE` 只允许 analyst，AI、finance_bp、rule_owner、service_account 均没有报告或导入发布/冻结权。

| role | 显式 allow actions |
|---|---|
| `finance_bp` | `system.health.read`, `workspace.metadata.read`, `intake.template.read`, `intake.batch.create`, `intake.source.upload`, `intake.source.profile.read`, `intake.mapping.confirm`, `intake.mapping.override`, `intake.issue.acknowledge`, `intake.version.read`, `intake.cleaning_summary.read`, `intake.standardized_workbook.read`, `investigation.read`, `statement.source.read`, `statement.report.read`, `statement.projection.read`, `statement.correction.read`, `workbench.report.read`, `operations.public.read`, `operations.overview.read`, `operations.snapshot.read`, `operations.attempt.read` |
| `analyst` | 全部 Action，除 `metric.change.activate`, `metric.change.retire`；inventory 为 `blocked:*` 的入口仍无条件阻断 |
| `rule_owner` | `system.health.read`, `workspace.metadata.read`, `intake.template.read`, `investigation.read`, `metric_library.read`, `metric.change.propose`, `metric.change.activate`, `metric.change.retire`, `metric.event.read`, `metric.impact.analyze`, `statement.source.read`, `statement.report.read`, `statement.projection.read`, `statement.correction.read`, `workbench.report.read`, `operations.public.read`, `operations.overview.read`, `operations.snapshot.read`, `operations.attempt.read` |
| `ai_analyst` | `system.health.read`, `workspace.metadata.read`, `intake.source.profile.read`, `investigation.read`, `copilot.investigation.ask`, `copilot.mapping.explain`, `metric_library.read`, `metric.impact.analyze`, `statement.source.read`, `statement.report.read`, `statement.projection.read`, `workbench.report.read`, `operations.public.read`, `operations.overview.read` |
| `ai_cfo` | `system.health.read`, `workspace.metadata.read`, `investigation.read`, `copilot.investigation.ask`, `copilot.report_outline.generate`, `statement.report.read`, `statement.projection.read`, `workbench.report.read`, `operations.public.read`, `operations.overview.read` |
| `service_account` | `system.health.read`, `workspace.metadata.read`, `intake.template.read`, `intake.source.profile.read`, `intake.source.validate`, `orchestration.build.start`, `orchestration.build.read`, `statement.source.read`, `statement.report.read`, `statement.projection.read`, `operations.public.read` |

补充硬规则：

- finance_bp 的 intake 写/读与调查读取必须 owner 为本人或显式指派本人；现有模型不能提供 owner 时 route 保持 blocked，而不是降低为企业级访问。
- `metric.change.activate` / `metric.change.retire` 只允许 rule_owner 且不可审批本人提议；`metric.change.propose` 可由 analyst/rule_owner 发起。
- AI 只能生成候选、解释、挑战或读取最小证据投影；不能提升 evidence 等级，不能调用 publish/freeze/approve。
- 新增 Action 必须先修订本文、全矩阵测试与 inventory；不能以字符串前缀或 wildcard 自动授权。

## 5. `require_action` 与 route policy

```python
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Request
from sqlalchemy.orm import Session


ResourceLoader = Callable[[Request, Session], ResourceRef]


@dataclass(frozen=True)
class AuthorizationContext:
    principal: Principal
    action: Action
    resource: ResourceRef
    decision: Decision
    correlation_id: str


AuthorizationDependency = Callable[[Request, Principal, Session], AuthorizationContext]


def require_action(
    action: Action,
    resource_loader: ResourceLoader,
) -> AuthorizationDependency:
    raise NotImplementedError
```

生成 dependency 的实际参数必须是 `request: Request`、认证 dependency 返回的 `principal: Principal` 和 route 同一个只读预加载 `session: Session`。loader 只允许 SELECT，须禁用 autoflush，不得 commit、写审计、调用模型、渲染或访问对象存储。`require_action` 执行 §6 的独立决策审计；handler 只能在它返回 AuthorizationContext 后运行。

policy 每项精确包含 `method`、normalized `path`、`actual_side_effect`、`action`、`resource_loader`、`owner`、`exemption_reason`。以下均合并阻断：最终 router 与 inventory 非双向一致；重复 method/path；未知 Action/loader；副作用被标只读豁免；`blocked:*` 被接线为 allow；GET 内有 flush/commit、write service、freeze、render-to-file、object write 或模型调用却登记为纯 read。

## 6. 认证/授权审计的独立 durable 屏障

对 401、deny、allow 使用同一顺序：

1. 建立 §9 correlation id，尚未执行 handler；
2. 解析 credential；缺失/无效时构造 actor 为空的认证拒绝事件；
3. 有效 Principal 经只读 loader 得到 ResourceRef，再调用 `authorize`；
4. 使用**新建 Audit Session** 开启独立短事务，插入认证拒绝或 authorization allow/deny AuditEvent 并 commit，不复用业务 Session；
5. audit commit 失败或结果不确定，rollback 并返回 503 `audit_unavailable`；不得继续 handler，也不得返回原本的 401/403/2xx；
6. durable 后，认证拒绝返回 401，authorization deny 返回 403，allow 才进入 handler；
7. 业务事务成功/失败另追加 outcome。业务 rollback 不得回滚第 4 步 decision。

durable allow 前禁止数据库 mutation/autoflush、对象写、render、模型/工具调用或外部网络副作用。资源不存在可在只读 loader 得到 404 候选，但仍先记含 action、path 和 locator hash 的 deny/error 审计再返回，且不得泄漏跨企业对象存在性。

有效认证事件的 `actor_id`、`actor_role`、`enterprise_id` 只复制 Principal。401 三字段必须全为 `NULL`；可记录 credential digest 的不可逆短指纹，不能用 body actor 替代。body 身份字段即使相等也只能在 redacted metadata 记 `identity_field_present=true`。

## 7. 发布与对象存储四阶段 ABI

publishing 与 operations 必须共用以下类型、签名、异常和时序。

### 7.1 完整类型

```python
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, Protocol
from uuid import UUID

from sqlalchemy.orm import Session


class PublicationFormat(StrEnum):
    HTML = "html"
    XLSX = "xlsx"
    PPTX = "pptx"
    PDF = "pdf"


class PublicationAttemptStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    RENDER_FAILED = "render_failed"
    STORE_FAILED = "store_failed"


class PublicationErrorCode(StrEnum):
    NOT_FOUND = "publication_not_found"
    SCOPE_CONFLICT = "publication_scope_conflict"
    FREEZE_CONFLICT = "publication_freeze_conflict"
    IDEMPOTENCY_CONFLICT = "publication_idempotency_conflict"
    RENDER_FAILURE = "publication_render_failure"
    OBJECT_STORE_FAILURE = "publication_object_store_failure"
    INTEGRITY_FAILURE = "publication_integrity_failure"
    INTENT_NOT_DURABLE = "publication_intent_not_durable"
    OUTCOME_NOT_DURABLE = "publication_outcome_not_durable"
    AUDIT_UNAVAILABLE = "audit_unavailable"


@dataclass(frozen=True)
class ModelBoundary:
    provider: str
    model: str
    purpose: str
    input_artifact_ids: tuple[str, ...]
    input_sha256: tuple[str, ...]
    output_artifact_ids: tuple[str, ...]
    output_sha256: tuple[str, ...]


@dataclass(frozen=True)
class AuditContext:
    actor_id: str
    role: Role
    enterprise_id: UUID | None
    correlation_id: str
    action: Action
    resource_type: str
    resource_id: str
    model_boundary: ModelBoundary | None


@dataclass(frozen=True)
class PublicationRequest:
    publication_id: UUID | None
    idempotency_key: str
    resource_type: str
    resource_id: str
    enterprise_id: UUID | None
    source_payload_sha256: str
    formats: tuple[PublicationFormat, ...]


@dataclass(frozen=True)
class ObjectPlan:
    attempt_id: UUID
    format: PublicationFormat
    object_key: str


@dataclass(frozen=True)
class PreparedPublication:
    publication_id: UUID
    idempotency_key: str
    resource_type: str
    resource_id: str
    enterprise_id: UUID | None
    source_payload_sha256: str
    formats: tuple[PublicationFormat, ...]
    object_plans: tuple[ObjectPlan, ...]
    intent_event_id: UUID


@dataclass(frozen=True)
class ObjectOutcome:
    attempt_id: UUID
    format: PublicationFormat
    status: PublicationAttemptStatus
    object_key: str
    content_type: str | None
    content_sha256: str | None
    size_bytes: int | None
    stored_object_id: UUID | None
    error_type: PublicationErrorCode | None
    error_message: str | None


@dataclass(frozen=True)
class ObjectBatchOutcome:
    publication_id: UUID
    outcomes: tuple[ObjectOutcome, ...]


@dataclass(frozen=True)
class PublicationFailure:
    error_code: PublicationErrorCode
    failed_attempt_ids: tuple[UUID, ...]
    retryable: bool
    http_status: int
    message: str


@dataclass(frozen=True)
class StoredObjectRef:
    stored_object_id: UUID
    object_key: str
    content_type: str
    content_sha256: str
    size_bytes: int


@dataclass(frozen=True)
class FinalizedPublication:
    publication_id: UUID
    status: Literal["published", "failed"]
    outcomes: tuple[ObjectOutcome, ...]
```

所有 tuple 不可为 `None`；formats 非空、无重复，并按枚举值排序。`Idempotency-Key` 必须是 1–128 字节可打印 ASCII 且每次发布必填；初次请求 `publication_id=None`，prepare 生成 UUID7，重试必须传回原 id。`ObjectOutcome.content_sha256` 是 render 后产物 hash；prepare 的 `source_payload_sha256` 是冻结输入 hash，不得混用。error_message 经 §8 脱敏并限 256 字符。

### 7.2 精确签名和 Session 归属

```python
RendererRegistry = Mapping[PublicationFormat, Callable[[PreparedPublication, ObjectPlan], bytes]]


class PublicationObjectStore(Protocol):
    def write_if_absent(
        self,
        *,
        object_key: str,
        content: bytes,
        content_type: str,
        content_sha256: str,
    ) -> StoredObjectRef:
        raise NotImplementedError


def prepare_intent(
    session: Session,
    request: PublicationRequest,
    audit_context: AuditContext,
) -> PreparedPublication:
    raise NotImplementedError


def execute_object(
    prepared: PreparedPublication,
    renderers: RendererRegistry,
    object_store: PublicationObjectStore,
) -> ObjectBatchOutcome:
    raise NotImplementedError


def finalize_success(
    session: Session,
    prepared: PreparedPublication,
    outcome: ObjectBatchOutcome,
    audit_context: AuditContext,
) -> FinalizedPublication:
    raise NotImplementedError


def finalize_failure(
    session: Session,
    prepared: PreparedPublication,
    outcome: ObjectBatchOutcome,
    failure: PublicationFailure,
    audit_context: AuditContext,
) -> FinalizedPublication:
    raise NotImplementedError
```

prepare 和 finalize 只使用 route 传入的同一个业务 Session，只 flush、不 commit/rollback。`execute_object` 无 Session，禁止开数据库连接。audit writer、renderer、publication/operations service、object store 都不得自行 commit。

### 7.3 固定四阶段

1. **prepare intent**：验证冻结资源、batch formats、idempotency；每 format 写 PENDING attempt，追加 intent AuditEvent，flush。不得 render/写对象。
2. **caller commit**：route 显式 commit 使 PENDING 与 intent durable；失败返回 503，且不得 render/object write。
3. **execute object**：按 canonical formats 逐项 render → SHA-256/size/content type → immutable object write，形成 ObjectOutcome。render 也只能在 durable intent 后发生。预期的 render/store/integrity 错误不得丢失 partial outcome：函数捕获后写入该 format 的失败 ObjectOutcome 并继续处理其余 format，最后正常返回完整 ObjectBatchOutcome。
4. **finalize + caller commit**：全部 succeeded 调 `finalize_success`，任一失败调 `finalize_failure`；追加逐项 outcome 并 flush。仅全成功可置 published，route 再显式 commit；failure outcome durable 后才返回原失败。

format 批次是 all-or-failed：部分对象成功可保留，但 publication 仍 `failed`。failure finalize commit 失败返回 503 `publication_outcome_not_durable` 并按 publication_id 对账，不得谎报已持久化。

### 7.4 幂等与重试

- identity 为 `(resource_type, resource_id, sorted_formats, idempotency_key)`；同 key 同 source hash 返回既有状态，不新增 intent/attempt/object。
- 同 key 但 resource、formats 或 source hash 不同抛 `PublicationIdempotencyConflict`，409。
- 重试携带原 publication_id/key；已 succeeded format 校验 object hash 后复用，只为失败 format 新增 sequence attempt；全批成功后才 published。
- object key 至少含 `resource_type/resource_id/publication_id/format/source_payload_sha256`，if-absent 写并校验 hash；同 key 异内容拒绝覆盖。
- client 断连/崩溃/超时不改变重放规则；PENDING 恢复器只依据 durable intent，不依赖内存。

### 7.5 错误类型

| error type | 条件 | HTTP / 持久化 |
|---|---|---|
| `PublicationNotFound` | 资源不存在 | 404；decision/error 审计 durable |
| `PublicationScopeConflict` | scope/enterprise 不匹配 | 403；deny 审计 durable |
| `PublicationFreezeConflict` | 未冻结或状态不允许 | 409；无对象副作用 |
| `PublicationIdempotencyConflict` | 同 key 参数不同 | 409；无对象副作用 |
| `PublicationRenderFailure` | renderer 失败 | failure outcome，503 |
| `PublicationObjectStoreFailure` | 对象写/校验失败 | failure outcome，503 |
| `PublicationIntentNotDurable` | 第 2 阶段 commit 失败/不确定 | 503；render/store 调用 0 次 |
| `PublicationOutcomeNotDurable` | 第 4 阶段 commit 失败/不确定 | 503；进入对账，不能成功 |
| `AuditUnavailable` | 授权或 intent audit 失败 | 503；fail closed |

## 8. AuditEvent、保留与确定性脱敏

### 8.1 机器字段

AuditEvent 至少含：`id UUID`、`event_type str`、`actor_id str|null`、`actor_role Role|null`、`enterprise_id UUID|null`、`resource_scope`、`resource_type`、`resource_id`、`action Action|null`、`decision allow|deny|error`、`reason_code ReasonCode|str`、`correlation_id str`、`request_id str`、`model_boundary json|null`、`artifact_refs json`、`redacted_metadata json`、`created_at timestamptz`、`retention_class str`、`retain_until timestamptz`。

机器读取不能从自由文本推断 scope、decision、actor、hash、保留或 archive eligibility。artifact_refs 每项固定 `artifact_id`、`sha256`、`size_bytes`、`content_type`；model_boundary 只含 §7.1 字段，不含 prompt/output 原文。

数据库 trigger 拒绝 AuditEvent UPDATE/DELETE；ORM 重复防线。直接 SQL、ORM bulk、cascade、maintenance role 测试均证明应用角色不可修改/删除。

### 8.2 保留和 archive eligibility

- 唯一配置 `FLOW_AUDIT_RETENTION_DAYS`；缺失默认 365，须十进制整数且 `365 <= value <= 36500`。空串、浮点、负数、低于下限、超过上限或日期运算溢出均在所有环境启动失败。
- 写入固定 `retention_class="security_default"`、`retain_until=created_at + retention_days`；配置变长只影响新增事件，既有不得缩短。
- 不更新原事件。到期扫描仅追加 `audit.archive_eligibility_marked`，其 `resource_type="audit_event"`、`resource_id=<target id>`，metadata 含 `target_retain_until`、`policy_days`。
- 机器谓词：目标 `retain_until <= trusted_now`、存在 committed eligibility marker，且按 `(created_at, id)` 排序后不存在未被更晚 `audit.legal_hold_released` 配对解除的 `audit.legal_hold_placed`；三项全满足才可被未来归档规格选择。S01 无物理归档/删除。

### 8.3 确定性 redact

```python
@dataclass(frozen=True)
class RedactedText:
    text: str
    utf8_bytes: int
    sha256: str


def redact_audit_text(value: str) -> RedactedText:
    raise NotImplementedError
```

算法顺序固定：

1. 输入必须 str；解码失败、非 str、正则异常抛 `AuditRedactionFailure`，writer rollback 并返回 503，不能保存原文或尽力结果；
2. Unicode NFC，CRLF/CR 转 LF，移除 LF/TAB 外 C0/C1 控制字符；
3. 顺序替换 Bearer/Basic/API key/JWT token → `[REDACTED_TOKEN]`；邮箱 → `[REDACTED_EMAIL]`；中国大陆或带国家码手机号 → `[REDACTED_PHONE]`；连续 8 位以上数字 → `[REDACTED_NUMBER]`；
4. 按 Unicode code point 截到 256 字符；
5. `utf8_bytes=len(text.encode("utf-8"))`；`sha256=hashlib.sha256(text.encode("utf-8")).hexdigest()`。

正则使用 Python `re`、Unicode 模式和以下冻结 pattern；每个 pattern 全局替换，先后次序就是上文第 3 步，不得交换：

```python
CREDENTIAL_RE = re.compile(
    r"(?i)(?:\bauthorization\s*:\s*)?(?:bearer|basic)\s+[A-Za-z0-9._~+/=-]+"
    r"|\b(?:api[_-]?key|token|secret)\s*[:=]\s*[A-Za-z0-9._~+/=-]{8,}"
    r"|\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"
)
EMAIL_RE = re.compile(r"(?i)(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)")
LONG_NUMBER_RE = re.compile(r"(?<!\d)\d{8,}(?!\d)")
```

每个允许写入 `redacted_metadata` 的 key 必须在事件类型 schema 中显式声明；未知 key、嵌套自由文本、非有限数值或无法 canonical-JSON 序列化同样 fail-closed。所有自由文本值先过 `redact_audit_text`。

原文件、单元格、完整 prompt/output、credential、PII 不得传入此函数；它是末端防线，不是记录许可。

| input | exact `text` | `utf8_bytes` | `sha256` |
|---|---|---:|---|
| `联系 a.b+flow@example.com，手机 13800138000` | `联系 [REDACTED_EMAIL]，手机 [REDACTED_PHONE]` | 49 | `d33073982144f9c0c18dadf5cfbc19ab7a75511eac24b84aab7d0d0a746c5f92` |
| `Authorization: Bearer abc.DEF-123_xyz` | `[REDACTED_TOKEN]` | 16 | `265aaf89fab192cf70170814678ffcedc2476f24fda97f424e23f1c89db9cc33` |
| `订单 12345678；短号 1234567` | `订单 [REDACTED_NUMBER]；短号 1234567` | 41 | `f542c8590be85e8d0de33f0e36375f4d78b664b028cb7276edaa6823bd1e09b9` |
| `e\u0301\r\nOK` | `é\nOK` | 5 | `fa7c7668f78837dc314ad2892e64778f8b43b7521910104f85bb8455f6588b24` |

还须测试 257 个汉字截为 256、非法类型 fail-closed，以及各输出精确 byte count/SHA-256。

### 8.4 审计读取

analyst 只读本企业；rule_owner 只读本企业规则治理；finance_bp 只读 `actor_id=principal.actor_id` 且本人任务资源。AI/service_account 无通用审计查询权。过滤先 scope/enterprise，再应用其他 query。

## 9. correlation / request id 合同

1. `X-Correlation-ID` / `X-Request-ID` 均只接受 1–128 字节可打印 ASCII；trim 后校验，控制字符、逗号多值、空值、超长返回 400；
2. 两者都存在必须逐字相等，否则 400 `request_id_conflict`；
3. 仅一个则采用；都无则生成小写带连字符 UUID4；
4. canonical 值同时写 `request.state.correlation_id` / `.request_id`；审计、日志、模型、工具、publication context 只从 state 读取；
5. 所有响应含异常路径均回写 `X-Correlation-ID` / `X-Request-ID`，两者与 state 完全相等；不得在响应末尾另生成。

验收覆盖各单 header、相同/冲突双 header、非法 ASCII/长度、自动 UUID、正常/异常响应；断言 response 双 header、request.state、AuditEvent、日志 capture 五处完全相同。

## 10. 迁移与启动失败

- `0026_security_audit.down_revision == "0025_enterprise_cycle"`；新增 RoleBinding、AuditEvent、publication intent/outcome 字段、拒 UPDATE/DELETE trigger。
- 迁移只加不改现有事实。downgrade 可删新增对象，但生产执行另需授权，不是常规审计删除路径。
- identity JSON、RoleBinding 对账、legacy 截止、retention、审计 schema、inventory 装载失败均须接流量前 fail-fast；不得退回匿名、development allow-all 或旧 bearer。

## 11. 验收与精确命令

实现后本地门禁如下，缺文件/缺测试即失败，不能删参数绕过：

```bash
cd services/api
uv run pytest tests/security/test_authorization.py tests/security/test_principal_resolution.py tests/security/test_route_policy.py -v
uv run pytest tests/api/test_auth_boundary.py tests/integration/test_audit_atomicity.py tests/integration/test_security_schema.py -v
uv run pytest tests/publishing/test_publication.py tests/api/test_publishing_api.py tests/operations/test_operations_publication.py tests/operations/test_operations_public_api.py tests/integration/test_object_store.py -v
uv run pytest tests/api/test_copilot.py tests/api/test_orchestration_api.py tests/api/test_intake.py tests/api/test_investigations.py tests/api/test_metric_library.py tests/api/test_statements.py -v
uv run pytest tests/integration/test_migrations.py -v
uv run ruff check src tests
uv run mypy src
cd ../..
python3 scripts/documentation/require_approved_specs.py FLOW-SPEC-MODULE-BOUNDARIES-V1 FLOW-SPEC-FINANCIAL-FACTS-V2 FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1
make docs-check
git diff --check
```

最低断言：

1. Role × 完整 Action 全笛卡尔积；default deny、owner、自批、AI、scope、service account 和 reason 顺序；
2. identity digest/未知字段/空数组/重复/actor 冲突/role-service flag/DB 权威/development/legacy 截止；
3. router/TSV 双向一致；隐藏写 GET、copilot、orchestration、dashboard/workbench/workspace；`blocked:*` 不进入 handler；
4. 401/403/allow 独立 durable audit，audit fail 503，业务 rollback 不回滚 decision，body actor 不可伪造；
5. AuditEvent SQL/ORM 不可变、retention、marker、redact vectors、读取隔离；
6. publication 时序、Session 不偷 commit、batch/partial/idempotency/retry、故障注入；intent 未 durable 时 renderer/store 均 0 次；
7. object if-absent、同 key 异内容拒绝、下载 hash、失败不 published；
8. 0025→0026 upgrade/downgrade/upgrade、RoleBinding 唯一 active、trigger；
9. correlation 双 header/state/AuditEvent/log 一致，覆盖错误路径。

本文只有重新转 `approved` 后才能作为 Task 6 门禁；ABI、枚举、allow set、截止或 retention 偏差须先修订并重新审批。

## 12. 批准记录

- 2026-09-13：用户批准初版 V1.1 冻结值并授权执行。
- 2026-09-13：独立审查提出 P1/P2 后进入本轮精确化；因合同字节已变化，保持 `review` 等待复审与用户重新批准。
