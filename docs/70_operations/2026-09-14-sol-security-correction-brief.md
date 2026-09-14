---
doc_id: FLOW-OPS-S01-SOL-CORRECTION-20260914
title: GPT-5.6 Sol 安全车道修正说明（2026-09-14）
doc_type: operations
status: active
version: 1.0
created_at: 2026-09-14
updated_at: 2026-09-14
owner: FLOW
applies_to: s01-security-lane
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053, D054]
supersedes: []
superseded_by: null
source_refs:
  - docs/80_reviews/2026-09-14-s01-multi-agent-overall-review.md
  - docs/40_specs/security/internal-workbench-rbac-audit-v1.md
related_code:
  - services/api/src/flow_api/security/
  - services/api/src/flow_api/api/auth.py
commit_refs: ["9081fda", "11a7749", "6e3b876", "6aff4ac", "b6830eb"]
evidence_refs:
  - https://github.com/davyzhong/FLOW/actions/runs/34766068402
  - https://github.com/davyzhong/FLOW/actions/runs/34788225472
  - https://github.com/davyzhong/FLOW/actions/runs/34789803764
confidentiality: project-internal
---

# GPT-5.6 Sol 安全车道修正说明

> 执行身份说明：计划 owner 是 GPT-5.6 Sol，但现有安全提交的 Git author 是 `Mavis (MiniMax M3)`。接手者必须在交付记录中说明“任务 owner / 实际执行者 / 审查者”，不得继续让身份漂移。

## 当前裁决

- `9081fda` 已进入 main：保留骨架，不重复合并；必须在新分支修正 default-deny。
- `6aff4ac` 不合并、不 cherry-pick。
- `b6830eb` 不合并；迁移中的 UUID 修正已由 main `b79bc64`覆盖，其测试须重写。
- 在审计、身份和 CI 恢复前，暂停 publication route 接线。

## 必须修正

1. 以冻结的 `main@774799e794476dad3a41acc5705838a2765476ca` 新建 `codex/s01-security-contract-repair`，不得续写旧 audit/wiring 分支；冻结后若 main 再变化，先停机重新审查，不自动换 base。
2. 统一只保留一个 `ResourceRef`；`authorize` 先校验 Action 枚举和精确 action/resource 映射，未知动作与错误资源组合一律 deny。
3. 把 6 Role × 全 Action × 合法/非法 resource、首个 reason code 写成严格测试，删除“多个结果均可”的宽松断言。
4. identity JSON 使用 exact 五字段 schema：未知字段拒绝，token digest 与 actor 双唯一，配置 actor 冲突拒绝，enterprise UUID、role/service flag 双向校验。
5. 先识别 presented token，再只对命中的 legacy token应用固定 cutoff；新增固定 legacy actor/enterprise，数据库只允许精确匹配一条 active binding。新 token 不得被 legacy 截止误伤。
6. Session dependency 使用 yield/close；startup 验证配置、数据库 binding、audit schema 和 provider 可用性，development 也不得跳过合同。
7. 实现真实 durable AuditWriter：401/403/allow、独立短事务、audit failure→503、确定性脱敏、retention marker/legal hold、读取隔离。
8. 实现 correlation/request middleware：入站双 header 校验、request.state、正常/异常响应、日志和 AuditEvent 保持同一值。
9. 停止扩建两个旁路 pipeline。按批准规格的精确类型和四阶段函数重写既有 publication/operations service；每 format 的 intent/outcome、必填 Idempotency-Key、UUID7、source hash、冲突和重试全部进入真实表与审计。
10. `0026` 已进入 main 且 CI 实际执行过迁移往返，因此一律不再改写；所有合同补强进入 `0027_security_contract_fix`，加入 role/service、publication identity/outcome/retention 需要的数据库防线。
11. 用真实 PostgreSQL/ORM 重写 schema 和 atomicity 测试，精确断言 SQLSTATE、AuditEvent 行、commit/rollback 和 object-store 调用次数；禁止用 MagicMock 单独证明原子性。
12. Sol 只提供共享测试 Principal、RoleBinding seed/factory 和认证 helper。协调者负责全局 fixture 与 CI；各 route/E2E owner 只更新自己的白名单测试。Sol 不批量改写 Kimi/GLM 测试，也不得恢复匿名 development 换取绿色。

## 文件范围

Security repair 分支允许：

- Modify：`services/api/src/flow_api/security/{__init__,principal,authorization,audit,models}.py`、`services/api/src/flow_api/api/auth.py`、`services/api/src/flow_api/settings.py`、`services/api/src/flow_api/main.py`、`services/api/src/flow_api/infrastructure/models/__init__.py`；
- Create：`services/api/migrations/versions/0027_security_contract_fix.py`、安全车道共享测试 helper/fixture；
- Test：`services/api/tests/security/test_authorization.py`、`test_principal_resolution.py`、`tests/integration/test_security_schema.py`、`test_audit_atomicity.py` 及新增安全专属测试；
- Forbidden：`.github/workflows/ci.yml`、权威状态/路线图/HANDOFF、Kimi 所有 route/schema、GLM 前端/模块/验收文件、知识库 manifest。

后续 publication 串行分支另行授权，只允许既有 `publishing/publication.py`、`operations/publication.py`、`infrastructure/object_store.py`、两条 publishing/operations route 及对应专属测试；两个旁路 `pipeline.py` 的删除或迁移由协调者先形成明确处置单。

## 与 Kimi 的接口冻结

在 Kimi v3 开工前，双方必须共同落定并有红灯交叉测试：

- credential outcome 如何在 401 前进入 durable audit barrier；
- durable AuditWriter provider 的注入接口与失败语义；
- owner requirement 必须是 role+action+resource 条件，不是全局 action 集合。

## 交付门禁

- 批准安全规格 §11 的所有精确路径实际运行，无 skip；
- security 目标测试、全 API、全部 E2E、文档和迁移 job 在同一 SHA 绿色；
- 两轮独立审查 P1/P2 清零；
- 在此之前不得声明 Task 6、audit、publication transaction 已完成。
