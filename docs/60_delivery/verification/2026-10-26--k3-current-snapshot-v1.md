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

本报告创建时的后续步骤已完成：registry、baseline、delta 与累计 diff 均已按该 snapshot 构建并复验，详见下节。当前下一步为按工作包口径开展只读语义路由和 HIGH 全审；`CURRENT_RELEASE` 继续保持 `flow-knowledge-2026-09-12.1`。


## K3 来源基线与累计差异重建（2026-10-26）

以本报告的 accepted snapshot 和原有 allowlist（`processed/03_财务与会计`、`processed/02_企业管理`、`processed/04_跨境物流`、`processed/微信知识库`、`wiki`）运行 `source_baseline.py build-v2`。生成 9,673 篇来源，ID 唯一；类别为 wiki 6,413、domain-note 1,601、wechat 1,659。与 10-19 baseline 比较的增量为 9,671 篇保持存在、2 篇新增；正文、路径、图片/附录 enrichment 变化均为 0。

累计四维 diff 从 10-19 的 9,956 个 ID 基础应用上述增量，得 9,958 个 ID：新增 6,641、存在 3,032、删除 285；旧的 1,868 个正文变化与 1,310 个 enrichment 变化保持记录。本次新增两条均是 `added`，没有改写历史条目。增量 delta 另行保存，便于复验。当前 9,673 条的 `k_domain` 仍为 `pending-review`，`authority_level`/`sensitivity` 为 `unclassified`；来源自动登记不冒充语义审阅。

| 文件 | SHA-256 |
|---|---|
| `source-inputs-2026-10-26.yaml` | 已纳入知识库 `sha256sums.txt` |
| `source-id-registry-2026-10-26.tsv` | `7579a7e704f1946525b24b0c38c84922abaceb0430ef423df94ed2c1e1a72a3a` |
| `source-baseline-2026-10-26.tsv` | `dcc2b3d01b7fc5200294593c5797b9703c98465d2f0c4eee2ec2c98349a395d4` |
| `source-delta-2026-10-26.tsv` | `689b7761d048e24bf7a879d5d87f4fcd047a527e70b6fdce79ce81a136f49c91` |
| `source-diff-2026-10-26.tsv` | `9e781828298245be3c9b9e295eb5da825d04c6092393913a0fd8d03c36e70b90` |

同一 accepted manifest 重建至独立 `/tmp` 输出目录，registry/baseline/delta 与累计 diff 均逐字节一致。生成后重算的 vault HEAD/tree、状态 SHA、内容 SHA、文件数、字节数与 dirty 路径数全部匹配 accepted manifest，写句柄 0。source baseline 与 coverage validator 专项测试 14/14 通过；知识库清单重生成 2,182 项并 `--check` 通过。全量语义路由、HIGH 全读、MED/LOW 双审、coverage 闭合、知识综合与独立 reader 尚待完成；`CURRENT_RELEASE` 不变。
