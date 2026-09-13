---
doc_id: FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1
title: 内部工作台 RBAC 与追加式审计规格 V1
doc_type: specification
status: review
version: 1.1
created_at: 2026-09-13
updated_at: 2026-09-13
owner: FLOW
decision_refs: [D052, D053, D054]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: services/api
---

# 内部工作台 RBAC 与追加式审计规格 V1

- 依据：战略重构设计 V1.1 §4（用户与责任）、§4.1（权限与审计最低合同）、§11（部署、安全和模型边界）；产品原则；S01 计划 Task 6。
- 目标：deny-by-default 授权、企业级隔离、追加式审计，作为内部工作台及全部敏感入口的上线前置门禁。

## 1. 输入

- 请求凭据（credential）：旧 Bearer token（兼容期内）、新身份配置；
- 路由与动作清单：intake、investigations、metric_library、publishing、objective_reports、statements、operations、copilot、orchestration 中全部 freeze / publish / approve / review / mutate / model-call / build 入口；dashboard、workbench、workspace 等读取入口也必须登记只读豁免；
- 角色集合与权限矩阵（§3、§4）；
- 运行环境标识（development / 非 development）。

## 2. 输出

- 纯函数 `authorize(principal, action, resource) -> allow / deny(reason)`；
- 集中 FastAPI dependency `require_action(action, resource_loader)`；
- credential→Principal 解析与路由→action/resource 映射（route_policy）；
- 迁移 0026：角色绑定表与 AuditEvent 追加式存储（含拒 UPDATE/DELETE 的数据库 trigger）；
- 逐入口端到端安全测试与审计事件断言。

## 3. 对象

| 对象 | 字段 | 说明 |
|---|---|---|
| Principal | `actor_id`、`role`、`enterprise_id`、`is_service_account` | 由 credential 解析；非 development 环境缺身份配置时**启动失败**；development 保留 development principal |
| Role | 枚举 | `finance_bp` / `analyst`（经分专员）/ `rule_owner`（财务规则负责人）/ `ai_analyst` / `ai_cfo` / `service_account` |
| AuditEvent | `event_type`、`actor/role`、`enterprise_id`、`resource`、`decision(allow/deny)`、`reason`、`correlation_id`、`model_boundary`（模型/用途/输入边界/输出）、`created_at` | 追加式；敏感输入只记哈希/摘要 |

### 3.1 凭据与 Principal 配置合同

- 新身份配置使用 `FLOW_IDENTITY_BINDINGS_JSON`，值为对象数组；每项精确包含 `token_sha256`、`actor_id`、`role`、`enterprise_id`、`is_service_account`。配置与日志均不得保存原始 token；解析时对请求 token 计算 SHA-256 后做常量时间匹配。
- 企业资源要求 Principal 与资源均有 `enterprise_id` 且完全相等；任一缺失均拒绝。`enterprise_id = null` 只适用于显式标为 `public` 的资源，不代表跨企业通配。
- 旧 `FLOW_AUTH_TOKEN` 兼容映射为 `service_account`；企业范围必须由 `FLOW_LEGACY_ENTERPRISE_ID` 明确提供。非 development 环境配置旧 token 却未配置企业范围时启动失败。
- correlation id 使用 `X-Correlation-ID`；只接受 1–128 字节可打印 ASCII，缺失时生成 UUID4，非法值返回 400；授权、审计和外部副作用使用同一值。

### 3.2 发布与对象存储事务 ABI

publishing 与 operations 两条发布链固定为以下四阶段，不允许 route 或 service 自创第二套时序：

1. `prepare_intent(..., audit_context: AuditContext) -> PreparedPublication`：在调用方 Session 中写 PENDING 业务态与 audit intent，只 flush，不执行对象写、不 commit；
2. 调用 route 显式 commit，使 intent durable；intent commit 失败时不得调用对象存储；
3. `execute_object(prepared: PreparedPublication) -> ObjectOutcome`：只执行对象副作用，不改变正式 published 状态；
4. `finalize_success(prepared, outcome, audit_context)` 或 `finalize_failure(prepared, error, audit_context)`：在调用方 Session 中追加 outcome；仅 success 可把业务态转为 published，随后由 route 显式 commit。failure outcome 必须可持久读取，原请求返回失败。

`AuditContext` 精确包含 `actor_id`、`role`、`enterprise_id`、`correlation_id`、`action`、`resource_type`、`resource_id`、`model_boundary`；`PreparedPublication` 至少包含稳定的 attempt/resource id、enterprise id、对象键、内容 SHA-256 和 intent event id。audit writer、publication service 与 object store 都不得自行 commit。S01 不引入通用 outbox。

## 4. 权限矩阵（逐动作 allow/deny）

| 动作 | finance_bp | analyst | rule_owner | ai_analyst | ai_cfo | service_account |
|---|---|---|---|---|---|---|
| 数据提交/补充 | allow（仅本人任务） | allow（企业范围） | deny | deny | deny | 仅工具调用最小范围 |
| 查看本人任务退回原因 | allow | allow | deny | deny | deny | deny |
| 企业配置提议/维护 | deny | allow | 审阅受控配置 | deny | deny | deny |
| 正式规则提议 | deny | allow（不得自批本人变更） | allow | 仅 exploratory 候选 | deny | deny |
| 正式规则审批/退回/停用 | deny | deny（本人发起时） | allow | deny | deny | deny |
| Finding/证据调查、确认、驳回、例外 | deny | allow | 查看规则影响 | 生成候选 | 挑战/降级/冲突（不得提升证据等级） | deny |
| 回答被指派的补证问题 | allow | allow | deny | deny | deny | deny |
| 按任务读取最小必要输入/证据投影 | deny | allow | 按需只读 | allow（最小必要输入） | allow（专业版及证据投影） | allow（工具调用最小范围） |
| 报告发布（唯一人工发布权） | deny | allow | deny（无默认发布权） | **deny（禁止）** | **deny（禁止）** | deny |
| 跨企业访问 | deny | deny | deny | deny | deny | deny（默认拒绝，显式授权例外） |

矩阵的硬规则：

1. **deny-by-default**：没有明确 allow 即拒绝；路由代码不得散落角色字符串，一律经 `require_action`；
2. **规则不可自批**：rule 变更的提议者与审批者不得为同一 actor，无论角色；
3. **AI 无发布权**：两个 AI 角色无任何发布/冻结凭据；
4. **跨企业默认拒绝**：principal 的 enterprise_id 与资源不一致即 403。

## 5. 不变量

1. 所有敏感路由（freeze/publish/approve/review/mutate）必须在 route_policy 登记；OpenAPI/路由扫描守护测试发现未登记路由即失败；
2. 审计日志追加式：数据库 trigger 拒绝 UPDATE/DELETE，直接 SQL 测试证明不可变；
3. 至少记录：登录/授权变化、数据上传与哈希、映射确认、规则提议与审批、事实/证据修订、AI 模型与输入边界、工具调用、角色间冲突、人工 override、报告冻结与发布；
4. 敏感输入只记哈希/摘要，审计日志不保存明文敏感内容；
5. 旧 Bearer 在兼容期内可用但**不得绕过任一发布路径**；兼容期截止为 `2026-10-31T23:59:59+08:00`。超过该时间后，非 development 环境若仍仅配置旧 Bearer 必须启动失败；旧映射永远没有 freeze/publish/approve 权限；
6. 企业数据、配置、知识上下文、对象存储与审计日志按企业隔离。
7. 全挂载路由必须进入机器可读 inventory，记录 method、normalized path、实际副作用、action、resource loader、owner 或只读豁免理由；隐藏写 GET 按实际副作用保护。

## 6. 失败行为

| 情况 | 必须行为 |
|---|---|
| 无凭据/凭据无效 | 401 |
| 跨企业或角色不足 | 403，并写 deny 审计事件（含 reason） |
| 非 development 缺身份配置 | 启动失败（fail fast），不降级为匿名 |
| 未登记敏感路由出现 | 守护测试失败，合并阻断 |
| 审计写入失败 | 原操作失败（不允许「操作成功但无审计」） |
| audit intent 未 durable | 不执行对象存储或渲染副作用 |
| 对象存储/渲染失败 | 不形成 published；追加 failure outcome 后返回失败 |
| AI 角色请求发布/冻结 | 403 + 审计事件，无例外通道 |

## 7. 迁移

- 迁移 0026：新增角色绑定表、AuditEvent 表与拒 UPDATE/DELETE trigger；只加不改，回滚为删表，存量业务数据不受影响；
- 旧 Bearer 兼容：解析层把旧 token 映射为受限 Principal（默认 service_account 最小权限），兼容期内并行；兼容期结束后删除映射分支（另行决策，见 §5 第 5 条）；
- 在线审计保留期默认且最低为 365 天，只允许向上配置；S01 不提供 UPDATE/DELETE/物理归档路径，到期只允许标记 `archive_eligible`，物理归档另立规格。
- 审计读取按企业隔离：analyst 可读本企业事件；rule_owner 只读本企业规则治理事件；finance_bp 只读本人任务相关事件；AI 角色与 service_account 没有通用审计查询权。S01 只实现存储和访问策略守护，不新增通用审计浏览 UI。
- 脱敏阈值：不得记录原始文件、单元格值、完整 prompt、模型完整输出、凭据或个人信息；二进制/文本输入只记录 SHA-256、字节数、类型和稳定 artifact id；必要摘要最多 256 个 UTF-8 字符，并在写入前移除 token、邮箱、手机号和连续 8 位以上数字。`model_boundary` 只记录模型、用途、输入/输出 artifact id 与哈希。

## 8. 验收

1. `authorize` 纯函数单测覆盖矩阵全部单元格（角色×动作），含 deny-by-default 兜底；
2. 逐入口端到端测试：intake 提交、Finding/证据审批、规则审批、publishing/objective_reports/statements/operations、copilot 模型调用、orchestration build 每个敏感入口分别覆盖 401、跨企业/跨角色 403、合法 allow 与对应审计事件；旧 bearer 不得绕过任一发布路径；
3. 直接 SQL 尝试 UPDATE/DELETE AuditEvent 被 trigger 拒绝的测试通过；
4. 路由扫描守护测试：构造未登记敏感路由 fixture，测试正确失败；
5. `cd services/api && uv run pytest tests/security tests/api/test_auth_boundary.py tests/integration/test_security_schema.py -v` 全绿；
6. 本规格转 approved 后，Task 6 实现与本规格逐条对账，偏差回本规格修订。

## 9. 批准记录

- 2026-09-13：用户明确回复“批准安全规格，开始执行”。该批准适用于本 V1.1 冻结值；独立规格审查若要求改变上述合同，必须重新取得批准。
