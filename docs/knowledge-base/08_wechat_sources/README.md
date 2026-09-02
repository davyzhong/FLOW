# 08 公众号素材库（内容在 Obsidian vault，仓库只留流水线与链接）

**架构（2026-09-03 起）**：知识内容唯一存储于本机 Obsidian vault 并随其多机同步；
本仓库不存正文，只保留抓取流水线、来源配置、队列/状态/日志，以及指向 vault 的
链接引用索引。

- vault 内容根（`sources.yaml: content_root`）：
  `/Users/qiming/ObsidianWiki/Clippings/微信知识库/`
- 快捷入口：各账号「目录.md」MOC，如
  `obsidian://open?path=/Users/qiming/ObsidianWiki/Clippings/微信知识库/数据熊/目录.md`
- 全量引用索引：[INDEX.md](INDEX.md)（自动生成，每篇含 vault 笔记链接 + 原文链接）

## 来源

| 来源 | 公众号 | 账号 ID | 说明 |
|---|---|---|---|
| `shujuxiong` | 数据熊 | gh_d55144ba7fe2 | 4 个官方合集（财务分析/财务管理/财务报表/经营分析），412 篇已全量归档 |
| `shuyan_fupanshi` | 数研复盘狮 | gh_78506a7234d3 | 经营分析报告、毛利/净利润专题复盘 |
| （自动登记） | 花叔 | gh_13cc971d267c | Huashu Excel 作者，Excel 数据方法 |

数据熊 4 合集（`albums/*.json` 为清单与归位依据，跨合集文章取主归属）：

| 类别目录 | 合集 | album_id | 篇数 |
|---|---|---|---|
| `01_财务分析` | 财务分析 | 3888472289255505920 | 84 |
| `02_财务管理` | 财务管理 | 3705887141604474885 | 138 |
| `03_财务报表` | 财务报表 | 3627226562623291398 | 26 |
| `04_经营分析` | 经营分析 | 3714603110065618949 | 191 |

> 背景：项目"阶段 0"的五篇奠基研究材料中 4 篇来自数据熊、1 篇来自花叔——这些账号
> 正是项目早期灵感来源。

## 目录结构（本仓库内）

```text
08_wechat_sources/
├── README.md            # 本文件
├── sources.yaml         # 来源注册表 + content_root（vault 路径）
├── sources.auto.yaml    # 收件箱自动登记的来源
├── INDEX.md             # 引用索引（vault 笔记链接 + 原文链接，自动生成）
├── albums/              # 各合集清单 json（url/title/时间，归位与溯源依据）
├── queue/               # 待抓队列：pending_<来源id>.txt（去重由 state 负责）
├── state/seen_urls.json # 已处理 URL 状态（幂等；dir 字段为 vault 相对笔记路径）
└── logs/                # excluded / errors / sync_report / discovered
```

vault 内结构：`<公众号>/<合集目录>/<YYYY-MM-DD 标题>.md` + `attachments/`（图片本地化）
+ `目录.md`（MOC）。frontmatter 对齐 Web Clipper 习惯（author `[[wikilink]]`、tags 含
clippings）。

## 同步流水线

```bash
uv run scripts/wechat_kb/sync.py [--recompress]   # 发现→staging 摄取→写 vault→MOC/索引/manifest
uv run scripts/wechat_kb/fetch_album.py --album-url "<合集链接>" --out-queue <pending 文件>
uv run scripts/wechat_kb/export_obsidian.py --moc-only   # 只重建 vault 各账号目录页
```

发现通道：seed 队列 / 合集公开接口（免登录不限流）/ 收件箱自动归类 /
公众平台接口（httpOnly cookie 需浏览器页面内 fetch，200013 限流慢节奏）/ RSS。
新文章经 `work/wechat_kb/staging` 中转后直写 vault，仓库不落正文。

### 历史沿革

- 2026-09-02：建库并完成数据熊两个合集（财务分析/财务管理）208 篇入库；
- 2026-09-02：扩至 4 合集 412 篇全量归档（仓库内曾有正文副本）；
- 2026-09-03：内容整体迁移至 Obsidian vault（多机同步为唯一内容仓库），仓库改为
  流水线 + 链接引用；`99_manifest` 自此只覆盖仓库内文件。
