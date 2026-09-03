# 08 公众号素材库（交接中：待 DavyBase 接收后删除本目录）

**状态（2026-09-03）**：公众号 → Obsidian 知识库能力已决定移交 **DavyBase 项目**
（多渠道知识抓取 → Obsidian 知识库）。**DavyBase 尚未完成接收**，因此本目录与
`scripts/wechat_kb/` 流水线暂时保留（自 `e5919b4` 恢复）；**DavyBase 确认接收后，
按 [HANDOFF.md](HANDOFF.md) 第 5 节删除本目录与流水线**。

## 引用入口（长期保留，即使目录删除）

- **内容仓库（Obsidian vault，多机同步）**：
  `/Users/qiming/ObsidianWiki/processed/微信知识库/`
  - 全库 417 篇笔记（数据熊 4 合集 412 篇：01_财务分析 84 / 02_财务管理 127+
    / 03_财务报表 17+ / 04_经营分析 182+；数研复盘狮；花叔）
  - 快捷入口：`obsidian://open?path=/Users/qiming/ObsidianWiki/processed/微信知识库/数据熊/目录.md`
- **全量引用索引**：[INDEX.md](INDEX.md)（每篇含 vault 笔记 file:// 与 obsidian:// 链接 + 原文链接）

## 目录结构（交接期临时保留）

```text
08_wechat_sources/
├── README.md / HANDOFF.md / INDEX.md   # 指针、交接说明、引用索引（长期保留）
├── sources.yaml / sources.auto.yaml    # 来源注册表（含 content_root 与 albums 映射）
├── albums/                             # 4 个合集清单 json（url/title/时间）
├── queue/ state/ logs/                 # 待抓队列 / 去重状态 / 运行日志
scripts/wechat_kb/                      # 流水线（sync/fetch_album/export_obsidian/...）
```

- `state/seen_urls.json` 是去重权威——DavyBase 迁移工具时必须带走；
- 每周一 09:00 的旧定时任务已删除（DavyBase 接手后自行建立调度）；
- 标准化工具（wxkb CLI）位于 `~/.zcode/skills/wechat-article-harvest/`，DavyBase 以其为基线。

## 历史沿革

- 2026-09-02：建库；数据熊财务分析/财务管理两合集 208 篇入库；
- 2026-09-02：扩至 4 合集 412 篇全量归档（仓库内曾有正文副本）；
- 2026-09-03：正文迁移至 Obsidian vault（内容唯一仓库）；
- 2026-09-03：决定移交 DavyBase；流水线与配置自 `e5919b4` 恢复保留，等待接收确认后删除。
