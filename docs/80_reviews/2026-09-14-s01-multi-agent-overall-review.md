---
doc_id: FLOW-REVIEW-S01-MULTI-AGENT-20260914
title: S01 多代理执行进展整体复核报告（2026-09-14）
doc_type: review
status: open
version: 1.0
created_at: 2026-09-14
updated_at: 2026-09-14
last_reviewed_at: 2026-09-14
owner: FLOW
subject_ref: FLOW-WI-S01
findings: [F1-main-red, F2-security-incomplete, F3-route-policy-not-wired, F4-wave-order-bypassed, F5-verification-false-green, F6-scope-contamination, F7-authoritative-doc-drift]
applies_to: s01-parallel-agent-execution
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053, D054]
supersedes: []
superseded_by: null
source_refs:
  - docs/superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md
  - docs/70_operations/three-agent-parallel-execution-runbook.md
  - docs/40_specs/security/internal-workbench-rbac-audit-v1.md
related_code:
  - services/api/src/flow_api/security/
  - services/api/src/flow_api/api/auth.py
  - services/api/src/flow_api/api/router.py
  - apps/web/components/dashboard/workflow-nav.tsx
commit_refs: ["774799e", "168d15e", "b79bc64", "9cfec8b", "9081fda", "a49a10f", "9799485", "a4051ea"]
evidence_refs:
  - https://github.com/davyzhong/FLOW/actions/runs/34766068402
  - https://github.com/davyzhong/FLOW/actions/runs/34788225472
  - https://github.com/davyzhong/FLOW/actions/runs/34789803764
  - https://github.com/davyzhong/FLOW/actions/runs/34790577586
  - https://github.com/davyzhong/FLOW/actions/runs/34791653766
  - https://github.com/davyzhong/FLOW/actions/runs/34810868498
confidentiality: project-internal
---

# S01 多代理执行进展整体复核报告

## 1. 总结结论

S01 的确向前推进了很大一截，但**尚未形成可继续叠加的可信安全/模块 checkpoint**。当前应判定为：

- 产品方向没有跑偏：三层两模块、内部财务经营分析工作台、安全先行仍然正确；
- 工程执行明显跑偏：Task 6 尚未闭环，Wave 2 和额外产品功能已提前进入 `main` 或 integration；
- 首次审计时的 `main@b79bc64` 确实红色；随后多路候选被直接并入 main，并用开发身份播种等补丁把既有 16 个 CI job 修绿；
- 当前 `origin/main@774799e7` 的 CI run `34810868498` 为 success，但这不是完整门禁：required 清单中的 `module-boundaries-e2e` 缺失，route-policy 目标测试未进入 CI且在当前 main 独立复跑仍有 2 个失败；
- 当前 integration `168d15e` 已包含此前所有候选与 Library，main 又在其上追加 DuPont 和状态同步；它们不再是按原计划逐 Wave 形成的 checkpoint；
- 已有成果应分为“保留并修正”“只作底稿”“隔离为独立工作包”三类，不应整体推倒重来，也不能继续按交付文档宣称完成。

执行方式已经由用户改为**单一 Agent 串行修正**。原 Sol/Kimi/GLM 名称在本文中只标识问题域和历史责任边界，不再表示继续并行派工。单一 Agent 也必须逐 Gate、逐分支、逐次审查，不能把全部修复压成一个提交。

## 2. 审查快照与方法

首次冻结时间：2026-09-14 08:33（Asia/Shanghai）；当前状态复核到 `main@774799e7`、CI run `34810868498`。报告同时保留首次红线事件和最新主线事实，防止后续修复把过程性跑偏抹掉。

审查同时比较 main、integration、各执行分支的提交血缘、文件范围、批准规格、计划顺序、测试代码与 GitHub Actions。所有“完成”声明都必须能由实际代码和对应 SHA 的 CI 证明；交付清单本身不作为证据。

本轮另做三路独立只读审查：安全车道、Kimi 路由车道、GLM 模块/验收车道。三路结论在“主线红、Task 6 未完成、候选分支不可原样合并”上完全一致。

严重度定义：本文的 `P0` 表示“当前 checkpoint 立即停止合并/发布”，并不等同于已经发生生产事故或数据破坏；`P1` 是合并阻断缺陷；`P2` 是进入下一阶段前必须消歧或修正；`P3` 是可跟踪改善项。

## 3. 当前事实表

| 对象 | 实际状态 | 裁决 |
|---|---|---|
| `main@774799e7` | 现有 16 job CI 全绿；docs m1 PASS；独立运行 security/auth/module 目标集为 70 passed / 2 failed | 可作修复起点，不是完成 checkpoint |
| `integration@168d15e` | 已把旧安全、Kimi、GLM 候选和 Library 混合并入；16 job CI 绿 | 冻结，不再叠业务 |
| 红线事件 `main@b79bc64` | 0026 可往返、局部 security 44/44，但远端多个核心 job 因 401/文档门禁失败 | 历史事故证据，已用补丁修到表面绿色 |
| Security Bootstrap `9081fda` | CI `34766068402` 绿色；安全类型/矩阵骨架已进主线 | 保留，修正 default-deny |
| Security audit/pipeline | 0026、RoleBinding、协议和 pipeline 骨架已进 main；审计 writer 与真实事务闭环缺失 | 大修，不继续接 route |
| Kimi route-policy v2 `a49a10f` | 已通过 `91bfb56` 合入 main；真实 routes 仍没有 `require_action`；当前 main 的 route-policy/module 目标集有 2 个失败 | 保留底稿，必须做 v3 接线 |
| GLM module-ui `9799485` | Vitest 5/5、typecheck、E2E 15/15；已提前进入 main | 功能保留，补门禁/锚点 |
| GLM module-boundaries/full-verification `a4051ea` | 已通过 `f5d9c52` 合入 main；两个分支仍是同一旧基线链，测试覆盖不足 | 已继承但不验收，未来重建 v2 |
| P5 Statements `61ed5fc` | 独立 CI 当时绿色，但不属于 S01 白名单，部分 README 声明超出证据 | 独立工作包复核 |
| Library `df11b44` 起及 DuPont `c9f4c6c` | 已进入 main；种子脚本暗写身份已在 `168d15e` 移除，但功能持续越过 S01 冻结令 | 继承但冻结，独立工作包复核 |

## 4. 主要发现

### F1 / P1：主线由“红色”修成“现有 CI 绿色”，但门禁仍不完整

`main@b79bc64` 的 CI run `34790577586` 曾在 `unit`、`integration`、intake、investigation、dashboard、user-closure 等 job 失败。主要原因是身份改造进入主线后，旧测试、脚本和 E2E 没有显式 Principal 与 RoleBinding 种子，大量预期 2xx/4xx 变成 401。

后续 `26a948f` 系列补齐测试身份、修正文档合同和连接生命周期，当前 `774799e7` 的 16 个现有 job 已全绿，docs m1 也 PASS。但 `.github/workflows/ci.yml` 仍无 `module-boundaries-e2e`，也没有运行 `tests/security/test_route_policy.py`。用仓库核验器检查同一 run：`--phase task6` PASS，`--phase wave2` 明确因缺少 `module-boundaries-e2e` FAIL。因此本问题从 P0 红线事故降为 P1 门禁不完整，不能据此关闭 Task 6/Wave 2。

### F2 / P1：安全只完成骨架，没有形成安全闭环

- `authorization.py` 未执行批准规格要求的 action × resource 精确检查，analyst 对未知动作可能被允许；对应测试还固化了错误预期。
- identity JSON 未严格拒绝未知字段/重复 actor；legacy 截止会误伤新 token；legacy actor/enterprise 未冻结并精确绑定。
- `audit.py` 只有 Protocol，没有真实 durable writer；401/403/allow、503 fail-closed、脱敏、保留、读取隔离和 correlation 闭环均未实现。
- 新建的 `publishing/pipeline.py`、`operations/pipeline.py` 是未接线旁路，类型、状态、多格式、幂等和 intent/outcome 均与批准 ABI 不一致。
- `security-wiring` 的集成测试本身包含无效 SQL和 mock-only 假设，不能作为原子性证据。

因此 Task 6 不能关闭，现有 `security-audit`、`security-wiring` 不得继续合并。

### F3 / P1：Kimi 的 route-policy 是“登记器”，不是“已接线权限系统”

- v2 没有修改计划列出的真实 routes；生产入口中 `require_action` 使用数为零。
- 双向扫描只比较 method/path，不能发现 route 没挂 action/loader，因而可产生假绿色。
- principal 依赖先抛 401，后续 policy 无法写 401 durable audit；实际 AuditWriter 又从未注册。
- request body 的 actor/reviewer/operator 仍被业务代码信任；owner loader 名称含 owner，实际却返回 `owner_actor_id=None`。
- route-policy 测试未进入 required CI job；当前 main 的目标复跑仍失败。

首次对 v2 分支独立复跑 `pytest tests/security/test_route_policy.py tests/api/test_auth_boundary.py -q` 为 18 passed、3 failed。对当前 main 复跑 `pytest tests/security tests/api/test_auth_boundary.py tests/api/test_module_boundaries.py tests/architecture/test_module_imports.py -q` 为 70 passed、2 failed：实际挂载 66 个路由而测试硬编码 65，`/api/v1/modules` 已挂载却仍留在 `PENDING_MOUNT_ROUTES`。这同时证明当前 CI 没有运行该门禁。

当前 `route-inventory-v1.tsv` 已追加 `/metric-library/coverage` 和 `/api/v1/modules`，但实现仍把已经挂载的 `/modules` 留在 pending，并将其作为匿名只读豁免；这与批准安全规格“仅 health 匿名”冲突。协调者不能用更新 TSV 行数替代真实 route 依赖接线。

v1 违反安全文件所有权且存在更严重 fail-open，应整体废弃；v2 可手工移植到 v3，但不可整包合并或标记 verified。

### F4 / P1：GLM 提前跨越 Task 6 / Wave 2 门禁

module-ui 在 Task 7 之前进入 main；随后 module-boundaries/full-verification 又被直接合入。两者都从 Gate 0 的旧 `b8a3edd` 开始并串在同一提交链，而计划要求分别从 Task 6 green、Wave 2 green 创建新分支。当前主线 CI 仍未运行 architecture、导航 Vitest 和 module-boundaries E2E 的完整组合。

### F5 / P1：模块边界与 Task 9 存在“假验证”

- AST 测试只扫三个 facade 和少量目录，没有按 ownership manifest 判定所有 import 的 source/target owner，也缺原路径违规 fixture、声明文件存在性和更广现有树覆盖。
- `/api/v1/modules` 未进入安全 inventory，也未挂最终权限策略；批准安全规格只允许 health 匿名。
- U8→S01 runner 使用固定 project/端口、curl `-k`、先升级后验证旧载荷，没有恢复库唯一 sentinel，也未比较 HTTPS/SQL/冻结期望 hash，不能证明 API 未误连常驻库。

### F6 / P1：范围污染与隐藏安全副作用

`522fe6c` 的提交标题是更新交付清单，实际带入大量代码、契约和生成数据；`df11b44` 又曾在财报种子脚本中静默创建 active service-account RoleBinding 和随机 enterprise。`168d15e` 已移除该隐藏写入，但 Library、视觉改版、DuPont 仍在 Task 6 未关闭时继续进入 main。P5 Statements、Library 可以作为独立产品增量保留，但 S01 修复期必须冻结，不再夹带新功能。

### F7 / P2：权威文档已经滞后或过度宣称

`774799e7` 已把 PROJECT_STATE、CURRENT_ROADMAP 和 S01 更新到 Task 6 维持不关闭，`GLM-S01-DELIVERY.md` 也已降为 draft，这部分漂移已纠正。但协调台账声称 `2570bf8` 为“17/17 全绿”，实际两个 run 都只有 16 个 job；它也把已合入但未真正接线的 route-policy/模块边界描述得过于接近完成。状态页的“Task 6 未关闭”是当前可信结论，台账的 job 数和完成清单不是完成证据。

安全规格曾存在 frontmatter `approved` 与 §12“保持 review”的矛盾，已在 `168d15e` 对齐批准记录。该修正可保留；执行 Agent 不得自行改写冻结合同。

## 5. 保留、返工与隔离

| 分类 | 内容 |
|---|---|
| 保留并修正 | 9081fda 的类型骨架；0026 基础表/trigger；write-if-absent 思路；Kimi 的 TSV 解析/loader 查询素材；9799485 UI；registry 的三模块描述 |
| 只作底稿 | 两个 pipeline；route-policy v2；module-boundaries AST/manifest；Task 9 runner；各交付清单 |
| 整体废弃 | Kimi v1 `0841ff9`；Sol startup `6aff4ac`；wiring 测试 `b6830eb` 原实现 |
| 从 S01 隔离 | `61ed5fc`、Library/视觉改版和 DuPont 均已在 main，只能作为“继承但冻结的范围外增量”；S01 修复期不再修改，任何 Dashboard 外部注册声明单独举证 |

## 6. 恢复优先级

1. 冻结 main/integration 的继续业务合并，以 `774799e7` 作为单一修复起点；保留 `b79bc64` 红线事故证据。
2. 新建单一 security-contract-repair 分支，修正授权、身份、审计和测试身份；把 route-policy 目标测试接入 CI并恢复真正覆盖当前功能的绿色。
3. 从绿色安全 checkpoint 新建 route-policy-v3，完成真实 route 接线；随后由安全 owner 串行完成 publishing/operations。
4. Task 6 同 SHA 全 job 绿色后，才创建 module-boundaries-v2；Task 7 绿色后再迁移 UI。
5. Wave 2 绿色后重写 full-verification-v2；最后才更新权威状态和关闭工作包。
6. P5 Statements、Library、视觉改版和 DuPont 都已随 main 继承但在 S01 内冻结，后续修正各走独立工作包和验收。

详细执行方式见 [单一 Agent 修正接管说明](../70_operations/2026-09-14-s01-single-agent-repair-handoff.md)、[恢复与再启动顺序](../70_operations/2026-09-14-s01-recovery-and-restart-runbook.md) 以及三份问题域修正单。
