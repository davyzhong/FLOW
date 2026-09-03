# 08 公众号素材库（已移交 DavyBase，此处仅保留引用入口）

**2026-09-03 起，公众号 → Obsidian 知识库的能力整体移交 DavyBase 项目**
（多渠道知识抓取 → Obsidian 知识库，与该工程定位重合）。本仓库不再保留流水线与正文，
只保留本引用入口。

## 引用入口

- **内容仓库（Obsidian vault，多机同步）**：
  `/Users/qiming/ObsidianWiki/processed/微信知识库/`
  - 全库 417 篇笔记（数据熊 4 合集 412 篇：01_财务分析 84 / 02_财务管理 127+
    / 03_财务报表 17+ / 04_经营分析 182+；数研复盘狮；花叔）
  - 快捷入口：`obsidian://open?path=/Users/qiming/ObsidianWiki/processed/微信知识库/数据熊/目录.md`
- **全量引用索引**：[INDEX.md](INDEX.md)（每篇含 vault 笔记 file:// 与 obsidian:// 链接 + 原文链接）

## 管线归属

- 标准化工具（wxkb CLI）：`~/.zcode/skills/wechat-article-harvest/`（init/album/article/sync/moc/index），
  由 DavyBase 项目为基线继续演进；
- 交接说明（架构、踩坑、运维清单、FLOW 侧裁剪记录）：[HANDOFF.md](HANDOFF.md)；
- 流水线代码与状态文件的历史版本见本仓库 git 历史（`scripts/wechat_kb/`、本目录
  `albums/ queue/ state/ logs/`，最后版本见提交 `4579cc8`/`709d69a` 前后）。
