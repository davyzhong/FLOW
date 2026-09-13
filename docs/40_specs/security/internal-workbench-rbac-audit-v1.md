---
doc_id: FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1
title: 内部工作台 RBAC 与追加式审计规格 V1
doc_type: specification
status: review
version: 1.0
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
- 路由与动作清单：intake、investigations、metric_library、publishing、objective_reports、statements、operations 中全部 freeze / publish / approve / review / mutate 入口；
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
5. 旧 Bearer 在兼容期内可用但**不得绕过任一发布路径**；兼容期截止日期在本规格转 approved 前由维护者填入：____（待定，Task 6 Step 1 冻结）；
6. 企业数据、配置、知识上下文、对象存储与审计日志按企业隔离。

## 6. 失败行为

| 情况 | 必须行为 |
|---|---|
| 无凭据/凭据无效 | 401 |
| 跨企业或角色不足 | 403，并写 deny 审计事件（含 reason） |
| 非 development 缺身份配置 | 启动失败（fail fast），不降级为匿名 |
| 未登记敏感路由出现 | 守护测试失败，合并阻断 |
| 审计写入失败 | 原操作失败（不允许「操作成功但无审计」） |
| AI 角色请求发布/冻结 | 403 + 审计事件，无例外通道 |

## 7. 迁移

- 迁移 0026：新增角色绑定表、AuditEvent 表与拒 UPDATE/DELETE trigger；只加不改，回滚为删表，存量业务数据不受影响；
- 旧 Bearer 兼容：解析层把旧 token 映射为受限 Principal（默认 service_account 最小权限），兼容期内并行；兼容期结束后删除映射分支（另行决策，见 §5 第 5 条）；
- 模型输入脱敏、审计日志访问范围与保留期限策略：本规格固定「必须存在且可配置」，具体阈值在 Task 6 Step 1 冻结为本规格的修订版。

## 8. 验收

1. `authorize` 纯函数单测覆盖矩阵全部单元格（角色×动作），含 deny-by-default 兜底；
2. 逐入口端到端测试：intake 提交、Finding/证据审批、规则审批、publishing/objective_reports/statements/operations 每个冻结/发布入口分别覆盖 401、跨企业/跨角色 403、合法 allow 与对应审计事件；旧 bearer 不得绕过任一发布路径；
3. 直接 SQL 尝试 UPDATE/DELETE AuditEvent 被 trigger 拒绝的测试通过；
4. 路由扫描守护测试：构造未登记敏感路由 fixture，测试正确失败；
5. `cd services/api && uv run pytest tests/security tests/api/test_auth_boundary.py tests/integration/test_security_schema.py -v` 全绿；
6. 本规格转 approved 后，Task 6 实现与本规格逐条对账，偏差回本规格修订。
