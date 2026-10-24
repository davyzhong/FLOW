---
doc_id: FLOW-VER-K2-OBSIDIAN-PREFLIGHT-20261019
title: K2 ObsidianWiki 只读预检记录
doc_type: verification
status: verified
version: 1.0
created_at: 2026-10-19
updated_at: 2026-10-19
owner: FLOW
commit_refs: [feb2dca1, 699e5c6c]
evidence_refs: "[obsidianwiki-git-status-readonly, k2-workspace-fingerprint, k2-wiki-scope-fingerprint, k2-writer-inventory, k2-recent-log-mtime]"
applies_to: knowledge-refresh
---

# K2 ObsidianWiki 只读预检记录

## 结论

工作包 7a 已关闭，K2 已转为唯一队首。2026-10-19 00:37（Asia/Shanghai）对 ObsidianWiki 完成只读预检。vault 有 1,377 条未提交路径，微信知识库范围内容指纹与 K0 基线不同，并检测到冻结器规则识别的潜在写入进程；当前不满足 accepted 快照条件。未对 ObsidianWiki 执行 pull、暂存、提交、清理、覆盖或内容写入。K2 的正式时间门禁必须等上海时间 14:30/15:00/15:30 的真实窗口。

## 只读证据

- 仓库 `/Users/qiming/ObsidianWiki` 当前分支 `main`；HEAD `e04d6833a623033a3601d36192f02dc15184eb6e`，HEAD tree `aa7d84d3fff59b0c1dd390fc872beb66cba40f52`；origin 为 ObsidianWiki GitHub 仓库。
- 工作区 dirty 路径 1,377：已跟踪修改 545、未跟踪 832、staged 0。K0 记录为 1,365 条 dirty 路径；当前完整工作区内容指纹 `6b277aca4ed1adef59f2846afde74e42202e47f0c9e49164f72d8600961eb100`。
- `processed/微信知识库` 当前内容指纹 `afd7ccf2b6466b8403a4118a3c3f36a1d6c66d05064931dce963c7daae9554a7`，32,637 个文件、3,952,541,809 字节；K0 基线为 `0a42346d276917c8b94f1b0c198ca5bfd68405c35c1656407bc10135e236c7f7`，32,625 个文件、3,945,394,427 字节。相较基线净增 12 个文件、7,147,382 字节，范围指纹已变化；因基线只保留了总体指纹，不能从中反推出这 12 个路径。
- Davybase 的 K2 冻结器只读 writer inventory 检出 `backupd`、`backupd-helper`、WeType FinderSync 和 `postersyncd` 进程名；未检出 Obsidian 或 Davybase pipeline 进程，launchd 列表也无 Davybase/Obsidian/pipeline 项。lsof 未返回非只读 vault 文件句柄。冻结器会按规则把匹配进程登记为潜在 writer，不能人工忽略该门禁。
- `.davybase` 最近状态库时间为 2026-10-18 18:46 CST，WAL 时间 18:45；Digest/Compile/ingest 进度文件最新为 2026-10-13 16:05；`logs/pipeline.log` 最新为 2026-10-13 16:05。未检出正在运行的 Davybase pipeline。
- Davybase `codex/knowledge-run-manifest-k0` worktree HEAD `b051c352b76a3f2c2150affffb7024fe00a51089`，工作树干净并与 origin 分支相同。FLOW 路线图状态提交 `feb2dca17f8f892781a421027e55d38975c44566` 已推送。

## 处置与下一步

在下一次真实时间窗内严格运行已推送的 `freeze_snapshot.py`：14:30 获取锁并记录 writer inventory；15:00 记录候选；15:30 复验 HEAD/tree/status 指纹及远端。如果 dirty 或潜在 writer 条件仍成立，只能生成 `rejected` manifest 和 SHA-256 sidecar，在 Davybase 独立分支提交并推送后释放锁；不得生成 accepted manifest、FLOW candidate 或改变 `CURRENT_RELEASE`。所有 vault 内容及 1,377 条既存变更保持原样。窗口未到之前不运行时间门禁子命令、不伪造时间。
