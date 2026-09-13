---
doc_id: FLOW-DESIGN-THREE-AGENT-ORCH-001
title: FLOW 三智能体并行重构编排设计
doc_type: design
status: approved
version: 1.0
created_at: 2026-09-13
updated_at: 2026-09-13
owner: FLOW
decision_refs: [D052, D053, D054]
knowledge_release: flow-knowledge-2026-09-12.1
supersedes: []
superseded_by: null
---

# FLOW 三智能体并行重构编排设计

## 1. 结论

S01 后半段采用“三智能体并行开发、主协调者串行集成”。三个执行者分别固定为 GPT-5.6 Sol、Kimi K3、GLM 5.3；执行者不直接修改 `main`，不分别更新权威状态文档，也不互相合并。主协调者独占共同合同、集成分支、状态真相和最终验收。

本设计只改变 `FLOW-PLAN-POST-U8-BOUNDARY-001` 的执行编排，不改变 S01 范围、三份 approved 规格或 `CURRENT_ROADMAP` 的唯一权威地位。

## 2. 当前基线与启动门

设计时可确认的共同基线为：

- U8 严格冻结提交 `914a473`，标签 `flow-u8-freeze-20260913`；
- S01 Task 2–4 已完成并经远端 CI 验证；
- Task 5 实现提交 `15c57c6`，迁移头应为 `0025_enterprise_cycle`；
- 设计创建时 `main` 为 `4ec50bc`；FLOW CI run `34755147722` 已成功。执行时仍须重新核对最新 main。

开始任何并行代码工作前必须完成 Gate 0：最新 `main` CI 全绿、工作区无范围外修改、状态文档与 Git 事实一致、安全规格未决项已冻结。安全规格发生任何字节变化时，必须先降为 `review`，经独立审查、用户明确批准后才能重新转为 `approved`；approved-spec 门禁不能替代用户批准。

## 3. 模型特点与岗位匹配

分工依据是“公开能力定位 + FLOW 首波校准”，不是品牌排名。

| 智能体 | 初始能力假设 | 首要岗位 | 约束 |
|---|---|---|---|
| GPT-5.6 Sol | 当前运行环境把它定位为可靠的日常代理型工程模型，适合严格按合同持续实现和验证 | 安全领域核心、授权纯函数、身份解析、0026 迁移、审计持久化与发布事务边界 | 除串行 lane 的 publishing/operations 外不拥有 API route；不拥有前端、路线图和最终合并 |
| Kimi K3 | Moonshot 官方资料强调 1M 上下文、长程 coding、知识工作和工具编排 | 全路由敏感入口盘点、route policy、跨文件接线、旧工作包与证据继承 review 备忘 | 任务必须限定文件白名单和明确停机条件，避免长程任务扩散 |
| GLM 5.3 | Z.ai 官方仓库强调复杂 coding 与长程工程任务的后训练增强 | 前端模块入口、模块 registry/ownership/AST 守护、最终技术验证 | 不自行解释产品状态；生成契约只能基于合并后的最终 API |

公开参考：

- Kimi K3：[MoonshotAI/Kimi-K3](https://github.com/MoonshotAI/Kimi-K3)；
- GLM 5.3：[zai-org/GLM-5](https://github.com/zai-org/GLM-5)。

这些资料只能决定首轮分配。Wave 1 后按以下项目内指标调整：目标测试通过率、首次 CI 通过率、审查发现数、范围外文件数、合并冲突数、返工轮数。任何智能体出现范围外写入或无法复现实证时，主协调者收回该工作包。

## 4. 编排结构

```text
Gate 0：主协调者冻结安全合同与共同基线
  ↓
Bootstrap：Sol 先交付可依赖的安全 ABI + 纯授权核心
  ↓
Wave 1（三路并行）
  Sol：审计/身份/0026/发布事务边界
  Kimi：route policy + 敏感路由接线
  GLM：前端模块入口与导航
  ↓
主协调者按 Sol → Kimi 合并
  ↓
Sol 串行接入 publishing/operations 两条发布路由
  ↓
主协调者复验完整 inventory、安全与事务门禁，关闭 Task 6
  ↓
Wave 2
  GLM：Task 7 模块 registry/ownership/API
  Kimi：跨模块与敏感路由只读复审
  Sol：安全负向测试与事务语义复审
  ↓
主协调者按 Task 7 → Task 8 合并
  ↓
Wave 3
  GLM：Task 9 全链技术验证
  Kimi：Task 10 旧工作包只读裁决备忘
  Sol：安全与审计最终独立复核
  ↓
主协调者串行关闭 Task 9、Task 10 和 S01
```

并行是流水线，不代表所有工作同时合并。迁移、生成契约、路线图状态和最终关闭永远串行。

## 5. Gate 0 必须冻结的合同

### 5.1 安全 ABI

在代码分支建立前，安全规格先转 `review`，修订必须明确：

- `Role`、`Action`、`Principal`、`ResourceRef`、`Decision` 字段和枚举；
- `authorize(principal, action, resource) -> Decision`；
- `require_action(action, resource_loader)`；
- route registry 键为 `(HTTP method, normalized path)`；
- correlation id 的请求头、生成规则和审计传递方式；
- development principal、非 development fail-fast、旧 Bearer 映射；
- `public` 与 `enterprise` 两种资源范围；`enterprise_id=NULL` 不得解释为“可访问所有企业”。

默认提案：旧 Bearer 只映射为最小权限 `service_account`，兼容截止为 `2026-10-31T23:59:59+08:00`；到期后非 development 环境启动失败，除非使用新身份配置。修订完成后必须独立审查，并由用户明确批准最终字节；未批准时 Gate 0 保持阻塞。

### 5.2 审计事务语义

“操作成功但无审计”禁止出现：

1. 授权 allow/deny 事件必须先可靠写入；写入失败则业务动作不开始；
2. 数据库内动作由同一 Session 持有事务，审计 writer 只 `flush`，不自行 `commit`；
3. 对象存储、渲染等外部副作用使用 correlation id 与 intent/outcome 两阶段事件；intent 未持久化不得执行外部副作用；
4. outcome 失败也必须追加事件；不得把 intent 伪装为业务成功；
5. S01 不实现审计删除。在线保留期默认至少 365 天且只允许向上配置；到期仅可标记为可归档，物理归档另行规格化。

现有 publication 服务内部提交事务。Gate 0 默认选择“调用边界持有数据库事务 + intent/outcome 审计”，不在 S01 新建通用 outbox。为避免并行 ABI 猜测，Kimi 只盘点但不修改 `api/routes/publishing.py` 与 `api/routes/operations.py`；Sol 独占其 route、`publishing/publication.py`、`operations/publication.py` 和 `infrastructure/object_store.py`。Sol 先完成 service/事务测试；待 Sol 与 Kimi 两条主分支都合并后，再从该绿色集成 SHA 创建串行发布路由分支，使用最终 `route_policy` 接线。

固定调用序列为：`prepare_intent(...) -> PreparedPublication` 只写 PENDING 业务态与审计 intent 并 flush；调用 route 显式 commit 使 intent durable；`execute_object(prepared)` 执行对象副作用；随后 `finalize_success(...)` 或 `finalize_failure(...)` 写 outcome 并由 route 再 commit。service 与 audit writer 均不得自行 commit，正式 published 状态只能在 success outcome 同事务中形成。具体参数类型、`AuditContext`、correlation id 和四个签名必须在安全规格中冻结后实现。故障注入必须证明 intent 先于对象写、对象失败不产生 published、failure outcome 可持久读取。不得只在 route 尾部补日志来声称原子性。

### 5.3 路由语义

敏感路由不能只按方法或路径词识别。Gate 0 必须从最终 `api_router` 生成全量 inventory，并逐项记录副作用、owner 和豁免原因。Kimi 接线 intake、investigations、metric_library、objective_reports、statements、copilot、orchestration；其中 `copilot.py` 的模型调用/commit 和 `orchestration.py` 的 build/commit 必须有逐入口测试。publishing/operations 登记为 Sol 串行 owner。`dashboard.py`、`workbench.py`、`workspace.py` 等读取入口也必须出现在 inventory 中并明确判定为只读或敏感。现有部分 GET 会创建冻结快照，必须按实际副作用登记为 freeze，或者先改造成真正只读。

### 5.4 模块描述合同

产品可见 API 固定返回：

```json
{
  "modules": [
    {"id": "public_analysis", "name": "公开财报分析", "layer": "product", "status": "implemented"},
    {"id": "internal_workbench", "name": "企业内部分析工作台", "layer": "product", "status": "designed"},
    {"id": "professional_governance", "name": "专业治理底座", "layer": "governance", "status": "designed"}
  ]
}
```

`shared_core` 是内部架构 owner，不出现在产品可见模块列表。Task 8 可以用同字节静态 fixture 开发，不提前请求尚未合并的 API。

## 6. 文件所有权

| 所有者 | 独占范围 |
|---|---|
| Sol | `security/{__init__,principal,authorization,audit,models}.py`、`api/auth.py`、`settings.py`、`main.py`、ORM 注册、`0026_security_audit.py`、`api/routes/{publishing,operations}.py`、`publishing/publication.py`、`operations/publication.py`、`infrastructure/object_store.py` 及对应安全/事务测试 |
| Kimi | `security/route_policy.py`；`api/routes/{intake,investigations,metric_library,objective_reports,statements,copilot,orchestration}.py`；`api/schemas/{intake,investigation,metric_library,publishing,statement,copilot}.py`；`investigation/models.py`；全路由 inventory、路由扫描和 auth/API 测试 |
| GLM | Wave 1 的 `apps/web/app/{public,internal}/**`、`components/modules/**`、导航、专属 E2E runner 和前端测试；Wave 2 的 `modules/**`、`routes/modules.py`、`api/router.py`、ownership manifest、模块/AST 测试与由该 API 改变触发的生成契约；Wave 3 的 U8→0026 同库升级验证 runner 与机器证据 |
| 主协调者 | 三份规格、计划、`HANDOFF.md`、`.github/workflows/ci.yml`、`PROJECT_STATE`、`CURRENT_ROADMAP`、S01 work-item、计划视图、知识清单、交付记录、integration 分支和最终契约复验 |

同一文件不能同时拥有两个 owner。发现遗漏文件时先暂停，由主协调者登记所有权后再继续。

## 7. 分支与合并协议

- 共同集成分支：`codex/s01-parallel-integration`；
- Bootstrap：`codex/s01-security-abi`；
- Sol：`codex/s01-security-audit`；
- Kimi：`codex/s01-route-policy`；
- Sol 发布路由：`codex/s01-publication-route-wiring`；
- GLM 前端：`codex/s01-module-ui`；
- GLM 前端集成：`codex/s01-module-ui-integration`；
- GLM 模块边界：`codex/s01-module-boundaries`；
- Task 9：`codex/s01-full-verification`；
- Task 10 审查备忘：`codex/s01-work-item-disposition-review`。

同一波次的并行分支从主协调者为该 checkpoint 公布的同一 `base_sha` 创建独立 worktree；后续波次使用上一 checkpoint 的 CI 绿色 SHA。执行者只提交自己的白名单文件并推送自己的分支。已推送分支不 rebase：需要新基线时新建分支并 cherry-pick 已审提交。Kimi 的 Task 10 输出只能写入独立 review 文档，不能直接编辑 work-item、CAPABILITY_MAP 或状态页。主协调者使用普通 merge commit 串行集成，不 squash 不明来源的多个任务；禁止 force-push、`reset --hard` 和直接推 `main`。

合并顺序固定：安全 ABI → Sol 审计/0026/发布 service → Kimi 七组路由与 inventory → Sol 串行接入 publishing/operations route → 完整安全复验并关闭 Task 6 → GLM 模块边界 → GLM 前端集成分支 → Task 9 证据 → Task 10 review 备忘 → 主协调者应用裁决并关闭权威状态。

## 8. 质量门禁

每条车道至少满足：红灯测试证据、目标测试绿、lint/typecheck、`git diff --check`、文件白名单为零越界、提交和远端分支存在。Bootstrap 合并时，主协调者就把授权核心测试纳入 CI；随后再把新增 security integration、architecture、Vitest 和 Playwright 测试纳入 `.github/workflows/ci.yml`。由于 main 当前没有 branch protection required checks，FLOW 自己维护 `config/ci/required_jobs_s01.txt`，并用校验器确认目标 SHA 的 `FLOW CI` workflow `conclusion=success`、清单内每个 job 都是 success 且无 skip；不能把“required jobs”为零当作绿色。每个候选合并后本地跑目标/交叉测试；每个公开 integration checkpoint（Bootstrap、Task 6 security、Wave 2、最终）只推送一次并等待上述验证通过。

Task 9 必须从合并后 FastAPI 重新生成 OpenAPI/TypeScript，不能人工解决生成文件冲突。最终恢复验证使用独立 compose project：专属 PostgreSQL volume 恢复 U8/0024，专属 API 的 `DATABASE_URL` 指向该库，专属 nginx 暴露动态 HTTPS 端口；通过 HTTPS 读取恢复库独有的已知载荷并与 SQL/冻结哈希对账，证明链路没有误连常驻 `flow` 库。顺序是恢复与旧载荷核验 → 同库 upgrade 到 0026 → 企业周期/安全 schema/审计 trigger/HTTPS 再验证；trap 必须保留原始退出码并清理专属 project。

## 9. 失败与恢复

- 单车道失败：不合并，保留分支供修复；
- 合并失败：在 integration 分支普通 `git revert -m 1` 回退该 merge commit；
- 0026 失败：只在一次性验收库 downgrade，生产数据不做破坏性回滚；
- 契约冲突：丢弃冲突产物，从最终 API 重新生成；
- Task 9 证据失败：S01 保持 active，Task 10 不能关闭；
- 任一模型越界修改权威状态或不可变档案：拒绝该提交，重新派发窄任务；
- U8 两个标签及本地备份始终保持不动。

## 10. 非目标

本设计不授权公开模块 C 级完整报告链、内部工作台业务功能、真实企业三周期验证，也不改变旧 U9/O5、U10 的产品裁决权。它只提供 S01 Task 6–10 的安全并行方式。
