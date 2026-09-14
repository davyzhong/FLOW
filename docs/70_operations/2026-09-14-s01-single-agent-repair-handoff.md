---
doc_id: FLOW-OPS-S01-SINGLE-AGENT-REPAIR-20260914
title: S01 单一 Agent 修正接管说明（2026-09-14）
doc_type: operations
status: active
version: 1.0
created_at: 2026-09-14
updated_at: 2026-09-14
owner: FLOW
applies_to: s01-single-agent-repair
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053, D054]
supersedes: []
superseded_by: null
source_refs:
  - docs/80_reviews/2026-09-14-s01-multi-agent-overall-review.md
  - docs/70_operations/2026-09-14-s01-recovery-and-restart-runbook.md
related_code: []
commit_refs: ["774799e", "168d15e", "b79bc64", "9cfec8b"]
evidence_refs: []
confidentiality: project-internal
---

# S01 单一 Agent 修正接管说明

## 接管目标

把多代理留下的分散成果收敛为一个可证明、可恢复、CI 全绿的 S01 实现。当前任务不是继续加功能，而是先恢复工程可信度。

## 开始前必须知道

- `main@b79bc64` 是历史红线事故；当前 `main@774799e7` 的 16 个既有 CI job 已绿，但 route-policy 目标测试仍有 2 个失败，且缺 `module-boundaries-e2e` CI job。
- 当前 integration `168d15e` 已混合旧候选与 Library，main 又追加 DuPont；它们不是按原 Wave 顺序形成的完成 checkpoint。
- 不得整包合并任何旧候选；按总报告的“保留/底稿/废弃/隔离”裁决手工迁移。
- 唯一修复起点固定为 `base_sha=774799e794476dad3a41acc5705838a2765476ca`。冻结后若 main 继续变化，停止并做增量审查。

## 串行顺序

1. **R0 冻结与校正**：停止 main/integration 业务合并；确认安全规格和 delivery 已校正；记录现有 CI 只覆盖 16 job，Library/DuPont 作为已继承范围外增量冻结。
2. **R1 安全修复**：读取 Sol 修正单；在窄分支修 default-deny、identity、durable audit、correlation、0027 和共享测试身份；恢复同一 SHA 全 CI 绿色。
3. **R2 路由与发布**：读取 Kimi 修正单；新建 route-policy-v3 接真实入口，再建独立串行分支接 publishing/operations；完成 Task 6。
4. **R3 模块与 UI**：读取 GLM 修正单；从 Task 6 green 做 module-boundaries-v2，再做 UI correction；接齐 CI，形成 Wave 2 green。
5. **R4 全链与裁决**：重做 full-verification-v2；通过后再做 Task 10 只读裁决和权威状态收口。
6. **独立支线**：P5 Statements、Library、视觉改版和 DuPont 均冻结继承，以后各自建工作包。

## 强制工作方式

- 每个 R Gate 使用独立 `codex/` 分支和 worktree；一个 Gate 不夹带下一个 Gate 的文件。
- 先写失败测试，再实现；先本地目标测试，再全链，再远端 CI。
- 每个 Gate 至少做规格符合性审查和代码质量审查；P1/P2 未清零不合并。
- 只承认与目标 commit 完全相同 SHA 的 CI；核对 required jobs 全 success、无 skip。
- 不 force-push，不改写已发布 0026，不用关闭认证、`curl -k`、mock-only 原子性或宽松断言换绿色。
- 提交标题与实际文件范围一致；每个 Gate 提交并推送后再继续。

## 完成定义

只有 R0–R4 依次通过、最终同一 SHA 的全部 required CI 绿色、U8 恢复验收成立、权威状态完成同步后，才可以宣布 S01 完成。任何“基本完成”“局部测试通过”“候选可用”都不是完成证据。
