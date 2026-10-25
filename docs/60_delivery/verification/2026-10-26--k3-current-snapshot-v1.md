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

下一步以 snapshot ID `obsidianwiki-20261026T003619+0800-4ea1c067` 新建 K3 source-input manifest，并从旧基线重建 source registry、source baseline 与四维 diff；构建前后再次核对当前 vault 指纹。通过后才开始逐条路由与语义审阅。`CURRENT_RELEASE` 继续保持 `flow-knowledge-2026-09-12.1`。
