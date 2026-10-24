---
doc_id: FLOW-VERIFY-K3-SOURCE-BASELINE-20261019
title: K3 来源基线与四维差异构建
doc_type: verification
status: verified
version: 1.0
created_at: 2026-10-19
updated_at: 2026-10-19
owner: FLOW
commit_refs: [e27ad1c0]
evidence_refs: "[obsidianwiki-k2-accepted-manifest, k3-source-inputs, source-id-registry, source-baseline-v2, source-diff-v2]"
applies_to: knowledge-refresh
---

# K3 来源基线与四维差异构建

## 范围和结论

本记录只验收 K3 的来源登记与确定性差异构建，不代表全量语义路由、HIGH 全文审阅、MED/LOW 双审、知识综合或 release seal 已完成。生成过程只读 ObsidianWiki，输出写入 FLOW。

来源输入绑定 K2 accepted manifest `obsidianwiki-20261019T075638+0800-0c0ac842`，vault 为 `/Users/qiming/ObsidianWiki`，代码旧截面为 `36274b2463aad9eae069af805e53e937c704c381`。Allowlist 包括财务、企业管理、跨境物流、微信知识库和 wiki（wiki 条目按规格关键词筛选）。

## 构建结果

| 结果 | 数量 |
|---|---:|
| 当前登记来源 | 9,671 |
| 差异 universe | 9,956 |
| 新增 / 仍存在 / 删除 | 6,639 / 3,032 / 285 |
| 正文变化 | 1,868 |
| 摘要或图片增强变化 | 1,310 |
| 可确认路径变化 | 0 |
| 重复 source ID | 0 |

当前 source registry 和 baseline 按 source ID UTF-8 字节序输出；正文先执行 Unicode NFC、换行 LF 规范化，再剥离外部入库工具生成的摘要与图片附录。此处只描述 ObsidianWiki 来源文件中的派生内容，不表示 FLOW 依赖该工具。旧来源只有在精确 locator 相同时继承旧 ID；不使用相似标题猜测改名。

基线同时登记来源 vault commit/tree、URL 或外部 ID、可读性及治理分类字段。自动生成阶段无法可靠确认的 `k_domain`、`authority_level`、`sensitivity` 均标为待审/未分类；历史摘要与图片模型版本缺证时标为 `not-recorded`。这些状态表示需要评审，不表示该来源已获采用或可用于发布。

| 文件 | SHA-256 |
|---|---|
| `source-id-registry-2026-10-19.tsv` | `c041c6922c78f143db788c98fc602e10f3ab6e33fa5eafd518d77bfec08d1b48` |
| `source-baseline-2026-10-19.tsv` | `901bee24f27c26e12e94518a99665d279dfdec1e333bc4c7a950651386a5af3b` |
| `source-diff-2026-10-19.tsv` | `ac987729a96d3cad33c6d773ca0021e379247574a156bd0c0d54306c595284e1` |

## 解释边界

旧基线不含完整的改名身份 registry；因此“可确认路径变化为 0”仅表示没有通过稳定身份确认的改名，不能推断没有发生改名。无法稳定匹配的路径会分别列为新增/删除。当前 1,310 项 enrichment 变化基于旧 Git tree 与 K2 当前工作区逐条正文/图片引用计算，缺失旧值不会被误当作变化。

此结果也不是逐篇判断价值或 HIGH/MED/LOW 的人工覆盖结论。剩余全量路由、HIGH 回读、MED/LOW 双审、失败集中度、coverage 闭合、reader 与 seal 仍需按 K3 验收完成；`CURRENT_RELEASE` 保持 `flow-knowledge-2026-09-12.1`。

## 可复验性与验证

同一 accepted 截面重复构建后，registry、baseline、diff 三个文件均逐字节一致。生成前后重算的 HEAD、tree、Git 状态 SHA、全工作区内容 SHA、文件数、字节数和 dirty 路径数均与 K2 manifest 完全一致；写入句柄均为 0。ObsidianWiki 没有被修改。

`python3 -m unittest scripts.tests.test_source_baseline scripts.tests.test_coverage_validator`：14 项通过；Ruff、Python compileall、文档 M1、知识库 inventory/hash 对账通过。报告只确认来源数据的技术登记与差异计算，不等同于独立语义审阅或 release seal。
