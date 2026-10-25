---
doc_id: FLOW-VERIFY-K3-CURRENT-SNAPSHOT-20261026
title: K3 当前 Obsidian 工作区稳定快照复核
doc_type: verification
status: verified
version: 1.0
created_at: 2026-10-26
updated_at: 2026-10-26
owner: FLOW
commit_refs: [davybase-f65df69]
evidence_refs: "[obsidianwiki-k2-2026-10-26-final, stable-working-tree-fingerprint, zero-writer-handles]"
applies_to: knowledge-refresh
---

# K3 当前 Obsidian 工作区稳定快照复核

## 结论

10 月 19 日 accepted manifest 的 Git 状态 SHA 与当前 vault 已漂移，因此不能将旧 K3 source baseline/diff 当作当前内容输入。按 K2 冻结器在 vault 外重新建立当前工作区快照；候选和复验的 HEAD、tree、Git 状态 SHA、完整内容 SHA、文件数、总字节数与 dirty 路径数均相同，写句柄均为 0，结果 accepted。ObsidianWiki 文件未被写入、暂存、提交或清理。

## 快照事实

| 字段 | 结果 |
|---|---|
| Vault | `/Users/qiming/ObsidianWiki`，branch `main` |
| snapshot ID | `obsidianwiki-20261026T003619+0800-4ea1c067` |
| HEAD / tree | `e04d6833a623033a3601d36192f02dc15184eb6e` / `aa7d84d3fff59b0c1dd390fc872beb66cba40f52` |
| Git 状态 SHA-256 | `5f058092c29641f9f4d60b46c07d36437798584e4c4c95864d7a3da629a3f82f` |
| 完整工作区内容 SHA-256 | `c84efd671e2b90e4f69152c3dd04a570d9c378d08fb7a3cb97b86e322f123df0` |
| 纳入文件 / 字节 | 112,010 / 4,260,351,293 |
| dirty 路径 | 1,475 |
| 候选 / 复验 | 完整指纹、数量均一致 |
| 写句柄 | 候选锁定 0；候选 0；复验 0 |
| 状态 | `accepted`；随后完成远端 push 并释放冻结锁 |
| Manifest SHA-256 | `ede08faabcf5c70222fec7c628f9ae778deba82dbdf5bdab26ad154184269e39` |
| Davybase 证据 | [`f65df69` 中的 manifest 与 SHA-256 sidecar](https://github.com/davyzhong/davybase/tree/codex/knowledge-run-manifest-k0/docs/evidence/snapshots) |

旧 accepted manifest SHA 为 `b7e566e68b1119117999fc9ef08f7fae657e6bcbc3d3482d77ea56caf0e44654`，记录 1,377 dirty 路径、111,912 文件和 4,240,118,843 字节。10 月 26 日前置只读扫描观察到 1,434 条 dirty 路径；冻结候选开始时已有 1,475 条。冻结器在候选/复验期间确认完整工作区指纹稳定，故新的 accepted snapshot 是之后 K3 的唯一输入。差异数值代表扫描时点变化，不用于推断具体文档的语义变化。

## 验收方法与下一步

Davybase `scripts/run/freeze_snapshot.py freeze` 运行于分支 `codex/knowledge-run-manifest-k0` 的提交 `f65df69`，将 manifest/sidecar 写入 Davybase 工作区；没有触碰 ObsidianWiki。manifest JSON 可解析，sidecar SHA 与本地 `shasum -a 256` 一致，提交已推送至 GitHub；之后冻结器 `release` 删除其外置锁文件。项目分支工作树干净。

本报告创建时的后续步骤已完成：registry、baseline、delta 与累计 diff 均已按该 snapshot 构建并复验，详见下节。当前已按工作包口径开展只读语义路由和 HIGH 全审；`CURRENT_RELEASE` 继续保持 `flow-knowledge-2026-09-12.1`。


## K3 来源基线与累计差异重建（2026-10-26）

以本报告的 accepted snapshot 和原有 allowlist（`processed/03_财务与会计`、`processed/02_企业管理`、`processed/04_跨境物流`、`processed/微信知识库`、`wiki`）运行 `source_baseline.py build-v2`。生成 9,673 篇来源，ID 唯一；类别为 wiki 6,413、domain-note 1,601、wechat 1,659。与 10-19 baseline 比较的增量为 9,671 篇保持存在、2 篇新增；正文、路径、图片/附录 enrichment 变化均为 0。

累计四维 diff 从 10-19 的 9,956 个 ID 基础应用上述增量，得 9,958 个 ID：新增 6,641、存在 3,032、删除 285；旧的 1,868 个正文变化与 1,310 个 enrichment 变化保持记录。本次新增两条均是 `added`，没有改写历史条目。增量 delta 另行保存，便于复验。基线初建时 9,673 条的 `k_domain` 为 `pending-review`，`authority_level`/`sensitivity` 为 `unclassified`；来源自动登记不冒充语义审阅。后续逐批审阅字段以对应语义台账及基线当前行值为准。

| 文件 | SHA-256 |
|---|---|
| `source-inputs-2026-10-26.yaml` | 已纳入知识库 `sha256sums.txt` |
| `source-id-registry-2026-10-26.tsv` | `ebd33a89055592314a6d24ea9ddce66dcd3caaca2ead33e301324844a17ec83b` |
| `source-baseline-2026-10-26.tsv` | `16db3241e5f911d4c38ce211b978802eaf4b0e5fbd04988ff962b6baec44acd9` |
| `source-delta-2026-10-26.tsv` | `689b7761d048e24bf7a879d5d87f4fcd047a527e70b6fdce79ce81a136f49c91` |
| `source-diff-2026-10-26.tsv` | `9e781828298245be3c9b9e295eb5da825d04c6092393913a0fd8d03c36e70b90` |

同一 accepted manifest 重建至独立 `/tmp` 输出目录，registry/baseline/delta 与累计 diff 均逐字节一致。生成后重算的 vault HEAD/tree、状态 SHA、内容 SHA、文件数、字节数与 dirty 路径数全部匹配 accepted manifest，写句柄 0。source baseline 与 coverage validator 专项测试 14/14 通过；知识库清单重生成 2,182 项并 `--check` 通过。全量语义路由、HIGH 全读、MED/LOW 双审、coverage 闭合、知识综合与独立 reader 尚待完成；语义批次 001–004 已记录 12 条 HIGH 候选（11 篇本地正文已读、1 篇元数据不足），均 pending-verification；`CURRENT_RELEASE` 不变。

## 语义审阅前复验快照（2026-10-26）

基线提交推送后原 manifest 锁已按流程释放，不能在无锁状态重跑 `verify`。随后按 Davybase 冻结器新建 accepted snapshot `obsidianwiki-20261026T005516+0800-d601b4d5`，Davybase 分支 `codex/knowledge-run-manifest-k0` commit `110fe57`。manifest SHA-256 为 `593715c832a538d9ba83df4e077b8dd9bace24f40d3c0d5262fc3779b20f0e77`；候选与复验内容 SHA 均为 `c84efd671e2b90e4f69152c3dd04a570d9c378d08fb7a3cb97b86e322f123df0`，状态 SHA `5f058092c29641f9f4d60b46c07d36437798584e4c4c95864d7a3da629a3f82f`，HEAD/tree、文件数 112,010、总字节数 4,260,351,293、dirty 路径数 1,475 均一致，写句柄 0。它与前一 accepted snapshot 的输入内容完全一致，因此不会改变来源内容；按最新快照 ID 重建后，registry SHA 为 `ebd33a89055592314a6d24ea9ddce66dcd3caaca2ead33e301324844a17ec83b`，baseline SHA 为 `16db3241e5f911d4c38ce211b978802eaf4b0e5fbd04988ff962b6baec44acd9`，delta SHA 仍为 `689b7761d048e24bf7a879d5d87f4fcd047a527e70b6fdce79ce81a136f49c91`；独立目录重复构建逐字节一致。另一次尝试因误传 HTTPS canonical remote 被门禁拒绝，拒绝证据同分支保留；使用仓库真实 `origin` 后通过。vault 未写入。


## 语义审阅批次 001（2026-10-26）

从既有 D-wiki HIGH 簇的代表主题中审阅三条来源：三表勾稽（K1）和杜邦分析（K2，related K3）的本地笔记正文已读；现金流分析（K2，related K1）本地文件只有 235 字节元数据，正文缺失，标记 `locator-only`，不得计为全文审阅。三条来源 SHA-256 均与 accepted snapshot baseline 的文件/正文指纹一致；权威级别与敏感级别保持 `unclassified`，处置均 `pending-verification`。逐条证据与理由见 `docs/knowledge-base/10_sources/semantic-review-2026-10-26-batch-001.tsv`。

## 语义审阅批次 002（2026-10-26）

从 A-finance HIGH 簇中审阅三篇本地完整笔记：杜邦分析模型、盈利能力驱动拆解、利润表分析与行业差异。三条 source SHA-256 均与 accepted snapshot baseline 文件及正文指纹一致；主域为 K2，权威级别 unclassified、敏感级别 public，处置 pending-verification。审阅发现杜邦案例文字将 414 亿元写成 41.4 亿元并将资产标为估算值，公式表缺少运算符；利润表行业收入确认说明过度概括。上述数值、公式表达和会计规则均不进入候选事实，待原始出版物与正式准则核验。逐条证据见 `docs/knowledge-base/10_sources/semantic-review-2026-10-26-batch-002.tsv`。


## 语义审阅批次 003（2026-10-26）

审阅 A-finance HIGH 簇 7 的三篇本地完整笔记：三大报表勾稽、现金流量表分析、资产负债表分析。三条 SHA-256 均与 accepted snapshot baseline 的文件及正文指纹一致；分别路由 K1、K2、K2，权威级别保持 unclassified、敏感级别 public、处置 pending-verification。三表勾稽笔记的现金流桥算例不闭合；现金流文章的案例算术可闭合，但阈值与行业判断仍属待核建议；资产负债表文章部分原则过于概括，ROE/EVA 定义不完整。不得把这些问题标记成已证实来源错误；只将其作为本地审阅风险，等待原始出版物与权威口径复核。

## 语义审阅批次 004（2026-10-26）

第四批审阅两篇现金流分析文章与一篇现金流量表编制笔记。三条 SHA-256 匹配 accepted snapshot baseline；分析文章路由 K2，编制笔记路由 K1，均保持 pending-verification。两篇分析材料给出的通用阈值缺少定义、数据依据或适用边界；编制笔记关于报表精度的宽泛说法未经准则支持。上述仅是对本地摘录的审阅结论，原始出版物和正式准则仍待核验。逐条记录见 `semantic-review-2026-10-26-batch-004.tsv`。
