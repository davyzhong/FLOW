---
doc_id: FLOW-WI-KNOWLEDGE-REFRESH-V2-001
title: 第二代静态知识刷新与战略重基线
doc_type: work-item
status: active
version: 1.2
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
- K0 审计 envelope 与微信旧批次回顾性验收已完成。K1 非微信覆盖、稳定截面、FLOW candidate 和战略裁决仍未完成。当前下一子步为 K1：先只读盘点 `processed/02_企业管理`、`processed/03_财务与会计`、`processed/04_跨境物流` 的图片覆盖和异常，并核对 allowlist/pathspec；本次路线图更新提交推送后再启动。
- 2026-10-17 只读 preflight：Davybase `main`=`6efcd6e2f0560e019f69dbbeada70e2532544f31`；审计实现在 `codex/knowledge-run-manifest-k0`，提交 `172a099`，K0 证据 `94fc05d`，交接/统计 `eb8c3d0` 均已推送。ObsidianWiki `main`=`e04d6833a623033a3601d36192f02dc15184eb6e`，K0 记录 1,365 条本地变化及内容哈希；全范围文件树摘要 `0a42346d276917c8b94f1b0c198ca5bfd68405c35c1656407bc10135e236c7f7` 复验一致。既存变化只读保护，不暂存、不提交、不覆盖，不能把 HEAD 单独称为完整工作区快照。
- `CURRENT_RELEASE` 继续为 `flow-knowledge-2026-09-12.1`。

## K0 完成：审计 envelope 与旧批次回顾性验收（2026-10-17）

实现 `davybase-knowledge-run/v1`、正文/图片 SHA-256 和互斥终态；apply 必须指定 run ID/manifest，dirty 代码或输入仓库 fail closed，dry-run 不写清单。历史 Git 输出快照实测 1,265 输入、1,241 篇 `done=true`；其中 2 篇各记 1 张失败图，严格终态为 1,239 成功、2 待复核、24 过滤。机器清单 strict PASS，32 篇确定性分层样本和 512 张图片逐项对账通过；清单 SHA-256 `c603baab83f7873c852681c69dfb314e7004e43b230ea832fb2a1e9043ce26bc`。872 项 pytest、Ruff、README 统计和链接检查通过；该实现 SHA 的 GitHub `ci.yml` 未运行。历史批次缺 prompt SHA-256，全部 1,265 篇 nonconformant，不计完整 L1 coverage。FLOW 仅保留汇总、定位符与哈希，不复制全文或图片。详见 Davybase 分支 `codex/knowledge-run-manifest-k0` 的验收证据。

ObsidianWiki 的 dirty working tree 不得被清理、重置或用 pull 覆盖；K0 不运行任何 `--apply`。pre-K1 快照同时记录 HEAD/tree、1,365 条 dirty 路径、其内容哈希及整个微信知识库范围文件树摘要，不能伪称仅有 Git HEAD 能代表全部 vault 内容。

## 当前执行子步：K1 非微信图片覆盖（队首待启动）

Davybase 当前没有 `scripts/run/image_coverage.py` 或 `config/knowledge_enrichment_scope.yaml`。
K1 从 TDD 实现 allowlist 与只读 coverage scanner 开始，再扫描
`processed/02_企业管理`、`processed/03_财务与会计`、`processed/04_跨境物流`，统计 Markdown、
含图文档、引用、可解析、已解释、待解释、过滤、缺失和失败，并生成只含路径定位符/哈希的报告。
同时核验 ObsidianWiki 1,365 条既存变化未变，生成候选 pathspec 并证明范围外/敏感路径为零。

K1 本阶段只读，不修改 ObsidianWiki。其现有 1,365 条变化使 `davybase-knowledge-run/v1`
apply 的干净输入仓库前置条件不满足；不得复制到临时库、忽略 dirty 状态或使用其他写入路径
绕过此门禁。完成覆盖 scanner、报告、pathspec 与独立审查后，先更新路线图给出后续处理方案和
可验证的写入边界，再进入后续任务。

## 全轨退出条件

- 三仓库身份、内容哈希、coverage、失败清单和敏感边界可重放；
- 15:00 accepted manifest、来源四维 diff、独立 reader 和 sealed lock 全通过；
- 用户逐项裁决，activation commit 的干净 worktree、门禁和远端 CI 全绿。

详细步骤见[统一完整实施计划 K 轨](../../superpowers/plans/2026-09-24-flow-integrated-execution-plan.md#10-k第二代静态知识刷新与战略重基线)。
