---
doc_id: FLOW-OPS-S01-RECOVERY-RESTART-20260914
title: S01 多代理恢复与再启动顺序（2026-09-14）
doc_type: operations
status: active
version: 1.0
created_at: 2026-09-14
updated_at: 2026-09-14
owner: FLOW
applies_to: s01-parallel-agent-execution
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053, D054]
supersedes: []
superseded_by: null
source_refs:
  - docs/80_reviews/2026-09-14-s01-multi-agent-overall-review.md
  - docs/superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md
related_code: []
commit_refs: ["b79bc64", "9cfec8b"]
evidence_refs: []
confidentiality: project-internal
---

# S01 多代理恢复与再启动顺序

> 执行模式更新：用户已决定后续交给单一 Agent。下列 Gate 保持不变，但全部串行执行；历史角色名仅用于识别文件边界和审查来源。

## Gate R0：冻结漂移

- 不向 main 或现有 integration 合并业务代码。
- 保留红线事故 main `b79bc64`、integration `9cfec8b` 及对应 CI；冻结当前修复起点 `main@774799e7`。
- 现有候选分支只读保存，不 rebase、不 force-push。
- 已完成的 delivery 降级和状态同步只作当前事实复核；权威状态保持 S01 active、Task 6 未关闭。后续 delivery 仍只允许合法状态。
- 复核 `168d15e` 已完成的安全规格 §12/approved 对齐与用户批准证据；代理不得自行解释或改写合同状态。

## Gate R1：恢复安全基线

`base_sha=774799e794476dad3a41acc5705838a2765476ca`。单一 Agent 从该 SHA 建 repair 分支，修复 default-deny、identity、durable audit、correlation，并只提供共享测试 Principal/RoleBinding factory/helper；全局 fixture 与 CI 作为协调子提交单独审查。不得用关闭认证或恢复匿名开发模式消除问题。

通过条件：approved-spec、docs、migration、security、API、全部 E2E 和 required CI 在同一 SHA 全绿；两轮独立审查清零 P1/P2。该 SHA 才能成为新的 Security checkpoint。

## Gate R2：完成 Task 6

Kimi 从 R1 SHA 建 route-policy-v3，完成真实入口接线；安全 owner随后从两者合并 SHA 串行接 publishing/operations。协调者接齐 security tests 到 CI，删除过渡 pending 例外。

通过条件：全 route inventory 双向一致；401/403/allow 均 durable audit；AI 无发布权；actor 不可伪造；跨企业、hidden-write GET、发布四阶段和失败回滚全部通过。此后才关闭 Task 6。

## Gate R3：完成 Wave 2

GLM 从 Task 6 green SHA 建 module-boundaries-v2；其 CI 绿色后再建 UI correction 窄分支。因 module-ui 已在 main，不重复 cherry-pick 07d82f2/9799485。协调者接入 architecture、导航 Vitest、module-boundaries E2E required job。

通过条件：模块 API/AST/ownership/契约、UI 和导航在同一 SHA 全绿，才发布 Wave 2 checkpoint。

## Gate R4：完成 Task 9/10

Wave 2 green 后，单一 Agent 先从该 SHA 建 full-verification-v2，分别证明“dump/既有 snapshot hash 与固定基线相等”和“恢复库唯一 marker 经 HTTPS 与 SQL 相等”，并完成真实 TLS、同库升级与全链命令。Task 9 技术证据通过并合并后，再从该绿色 SHA 建独立分支执行 Task 6B/Task 10 只读裁决备忘；最后统一更新 state、roadmap、S01、capability map 和交付记录。

## 独立支线

P5 Statements、Library、视觉改版和 DuPont 都已在 main，属于 S01 修复起点“继承但冻结的范围外增量”，R0–R4 不再修改。隐藏 RoleBinding 写入已移除；后续 14 样本证据、可复现生成和文案修正走独立工作包。

## R1 文件责任

- Security owner：security/auth/settings/main、0027、安全专属测试与共享认证测试 helper；
- Coordinator：`.github/workflows/ci.yml`、全局 fixture、legacy-exempt 文档合同修复和 checkpoint 发布；
- Kimi/GLM/其他 route owner：各自白名单内 API/E2E runner 与测试；
- 任一方不得为了“全绿”跨车道批量修改他人文件。

## 单一 Agent 每个 Gate 的回报格式

每完成一个 Gate 只提交以下事实：

1. `base_sha`、branch、commit、push 结果；
2. 变更文件清单与白名单差集；
3. 红灯测试与绿灯测试的精确命令/数量；
4. CI run id、head SHA、实际运行 job、skip 列表；
5. 未关闭 P1/P2 与残余风险；
6. 明确写“可合并”或“不可合并”，不得用“基本完成”替代。
