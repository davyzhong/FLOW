---
doc_id: FLOW-WI-MERGED-BRANCH-CLEANUP-20261025-001
title: 清理已合入 main 的历史远端分支
doc_type: work-item
status: active
version: 1.0
created_at: 2026-10-25
updated_at: 2026-10-25
do_not_execute: false
owner: FLOW
depends_on: []
acceptance_refs: []
applies_to: repository-maintenance
decision_refs: []
supersedes: []
superseded_by: null
related_plan: ../CURRENT_ROADMAP.md
confidentiality: project-internal
---

# 清理已合入 main 的历史远端分支

## 目标

减少 GitHub 分支列表中的历史分支，同时保证未合并工作、开放 PR 和明确暂停的工作仍可恢复。用户于 2026-10-25 明确授权本事项与路线图队首视觉任务并行；这是唯一允许并行的范围，不改变其他任务的串行顺序。

## 只读盘点基线

仓库 `https://github.com/davyzhong/FLOW`，基线 `origin/main=b068796f906cfbb91ac33775f5578194acc98a51`，当前活动分支 `codex/flow-visual-language` 比 main 多 21 个提交，关联开放草稿 PR #5，必须保留。其余 16 个旧分支均为 `origin/main` 的祖先；其中 `wip/zto-integration-20260929` 已合入但被项目状态记录为暂停，作为恢复指针保留。其余 15 个历史分支可在逐支复核 SHA 与祖先关系后删除。main 分支未启用保护规则；本工作不修改 main，也不重写 Git 历史。

## 清理清单

分三批逐支处理；每支删除前重新 fetch，读取远端 tip SHA，并确认 `git merge-base --is-ancestor <tip> origin/main` 成功。若 SHA 变化、祖先检查失败、出现开放 PR 或检查结果不明确，立即跳过该分支并记录，不强行删除。

批次 A：

- `codex/cfo-cockpit-reference-plan`
- `codex/cockpit-visual-completion`
- `codex/damai-logistics-data-audit`
- `codex/damai-logistics-implementation`
- `codex/flow-execution-convergence`

批次 B：

- `codex/single-machine-runtime-convergence`
- `flow/cockpit-acceptance-20261016`
- `flow/cockpit-c2-20261014`
- `flow/cockpit-c3-20261014`
- `flow/cockpit-d-20261015`

批次 C：

- `flow/finmetric-f3-20261014`
- `flow/source-registry-20261013`
- `flow/timeline-migration-20261013`
- `flow/u04-blind-review-20261016`
- `flow/u04-closeout-20261016`

保留 `main`、`codex/flow-visual-language`（直到 PR #5 完成并合入）、`wip/zto-integration-20260929`（暂停恢复指针）。PR #5 合并后删除视觉分支属于后续清理，不在本工作包授权清单内自动处理。

## 验收条件

- 仅删除上述 15 个已证明是 `main` 祖先且无开放 PR 的远端分支；每个删除成功后记录原 tip SHA。
- `main`、活动 PR #5 分支和暂停 ZTO 分支均保留；无 cherry-pick、merge、rebase、reset、强推或对 main 的写入。
- 清理后重新列出 GitHub 远端分支，核对删除数、保留数及 PR 关联；本工作包结果同步到 CURRENT_ROADMAP、HANDOFF 与 PROJECT_STATE。
- 过程若遇到不符合条件的分支，不扩大删除范围，并把客观限制记录为未完成项。
