---
doc_id: FLOW-WI-MERGED-BRANCH-CLEANUP-20261025-001
title: 清理已合入 main 的历史远端分支
doc_type: work-item
status: completed
version: 1.0
created_at: 2026-10-25
updated_at: 2026-10-25
do_not_execute: true
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

## 执行结果（2026-10-25）

15 个远端分支按三批完成删除。每个分支删除前均重新 fetch，读取精确远端 tip SHA，确认 tip 是 `origin/main` 祖先，并检查无开放 PR。删除后远端实际分支为 `main`、`codex/flow-visual-language`、`wip/zto-integration-20260929`；PR #5 仍开放为草稿，ZTO 暂停指针仍保留。

| 分支 | 删除前 tip SHA |
|---|---|
| `codex/cfo-cockpit-reference-plan` | `d3b2e4cb4332742ab60c5eab06ec36f0d441df47` |
| `codex/cockpit-visual-completion` | `27d8f566d7d130f67fa19ad2f745632f07b5d34c` |
| `codex/damai-logistics-data-audit` | `63d915759bab68c7b2b086e6c8c72a9d00b4817e` |
| `codex/damai-logistics-implementation` | `f62cf8eaed007ce59f18e0fef14a7c82a628a9c9` |
| `codex/flow-execution-convergence` | `96010a2c32233d1e19ec139c00de9651ac577a9c` |
| `codex/single-machine-runtime-convergence` | `013c072c6f4bbc7ad85f23ed15113c1b350b1341` |
| `flow/cockpit-acceptance-20261016` | `df6073a89b7c033add2050aff8e9ffaf243662c0` |
| `flow/cockpit-c2-20261014` | `07a07b7c106e400fa532fc99215b251e2fa2d325` |
| `flow/cockpit-c3-20261014` | `95427ae46f871c72fe48b8238161c9b9542cc2c7` |
| `flow/cockpit-d-20261015` | `14016297c6f5f1330d3ad50356f23d5bf00edc46` |
| `flow/finmetric-f3-20261014` | `5421f01afef435b98c6aadde1366de73e399de66` |
| `flow/source-registry-20261013` | `0fe3c6e09ecb61f81aa030604de8194f31348292` |
| `flow/timeline-migration-20261013` | `c824f55f247e6f470e10f11578a58fd4ae162ddd` |
| `flow/u04-blind-review-20261016` | `707733dd8e287e60ac4b4bbed151396babaf7eae` |
| `flow/u04-closeout-20261016` | `2c5e00ed816c01ea09ef9b491af8c44a62447087` |

## 验收条件

- 已删除上述 15 个经证明是 `main` 祖先且无开放 PR 的远端分支，并记录原 tip SHA。
- `main`、活动 PR #5 分支和暂停 ZTO 分支均保留；无 cherry-pick、merge、rebase、reset、强推或对 main 的写入。
- 清理后重新列出 GitHub 远端分支，核对为 3 个分支（main、活动 PR #5、暂停的 ZTO）；PR 关联符合预期。结果已同步到 CURRENT_ROADMAP、HANDOFF 与 PROJECT_STATE。
- 过程若遇到不符合条件的分支，不扩大删除范围，并把客观限制记录为未完成项。
