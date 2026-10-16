---
doc_id: FLOW-WI-KNOWLEDGE-REFRESH-V2-001
title: 第二代静态知识刷新与战略重基线
doc_type: work-item
status: active
version: 1.1
created_at: 2026-09-24
updated_at: 2026-10-17
owner: FLOW
depends_on: [FLOW-DESIGN-KNOWLEDGE-REFRESH-002]
acceptance_refs: [FLOW-PLAN-INTEGRATED-EXECUTION-20260924, FLOW-DESIGN-KNOWLEDGE-REFRESH-002]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: knowledge-system
---

# 第二代静态知识刷新与战略重基线

## 范围

验收 Davybase 图片批次，补齐非微信核心目录图片覆盖，取得稳定 15:00
Obsidian Git 截面，重建 FLOW 来源基线与 sealed knowledge candidate；用户完成
战略裁决后，才原子激活新 release、产品文档和路线图。

## 当前断点

- 批准规格和三仓库 preflight 已完成。
- K0/K1 机器验收、非微信覆盖、稳定截面、FLOW candidate 和战略裁决均未完成。当前唯一子步为 K0：审查 Davybase 已有的 `davybase-knowledge-run/v1` envelope 与 retrospective manifest 草稿，将通过审查的改动移植到最新 `origin/main`；随后验收既有 1,265 篇微信图片批次及至少 30 篇样本。
- 2026-10-17 只读 preflight：Davybase `main`=`6efcd6e2f0560e019f69dbbeada70e2532544f31`，工作区干净且 `git pull --ff-only origin main` 已确认最新；ObsidianWiki `main`=`e04d6833a623033a3601d36192f02dc15184eb6e`，fetch 后与 `origin/main` 同步，但K0 稳定快照记录 1,365 条本地变化，并用全范围文件 SHA-256 指纹复验一致。当前未发现相关批处理进程；这些本地变化作为只读输入保护，不暂存、不提交、不覆盖，不能把 HEAD 单独称为完整工作区快照。
- `CURRENT_RELEASE` 继续为 `flow-knowledge-2026-09-12.1`。

## 当前执行子步：K0 审计 envelope 与旧批次回顾性验收

执行合同见已批准统一计划 K 轨 Task 1/2（`docs/superpowers/plans/2026-09-18-static-knowledge-refresh-and-strategic-rebaseline-implementation-plan.md`）。Davybase 先实现/复核 `davybase-knowledge-run/v1`、内容 SHA-256 和严格互斥终态；再从 Obsidian 历史输出 Git 快照重建既有图片批次，生成 `retrospective=true` manifest。历史 Git 输出快照实测 1,265 输入、1,241 篇 `done=true`；其中 2 篇各记 1 张失败图，严格终态为 1,239 成功、2 待复核、24 过滤。旧记录缺失的代码 commit、input tree 或 prompt hash 必须标记 `nonconformant`，不计入完整 coverage。FLOW 仅保存汇总、定位符与哈希，不复制全文或图片。

ObsidianWiki 的 dirty working tree 不得被清理、重置或用 pull 覆盖；K0 不运行任何 `--apply`。pre-K1 快照同时记录 HEAD/tree、1,365 条 dirty 路径、其内容哈希及整个微信知识库范围文件树摘要，不能伪称仅有 Git HEAD 能代表全部 vault 内容。

## 退出条件

- 三仓库身份、内容哈希、coverage、失败清单和敏感边界可重放；
- 15:00 accepted manifest、来源四维 diff、独立 reader 和 sealed lock 全通过；
- 用户逐项裁决，activation commit 的干净 worktree、门禁和远端 CI 全绿。

详细步骤见[统一完整实施计划 K 轨](../../superpowers/plans/2026-09-24-flow-integrated-execution-plan.md#10-k第二代静态知识刷新与战略重基线)。
