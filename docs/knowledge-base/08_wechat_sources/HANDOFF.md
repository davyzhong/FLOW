# 交接说明：公众号 → Obsidian 知识库管线（供 DavyBase 项目接手）

> 本项目（FLOW）的定位是物流 Finance BP 的经营分析系统，公众号知识库属于外部素材能力，
> 与 DavyBase（多渠道知识抓取 → Obsidian 知识库）高度重合。本文档供 DavyBase 读取并
> 接手整条管线；接手后 FLOW 侧只需保留或移除本目录（均为独立可裁剪单元，无代码耦合）。

## 1. 现状一句话

数据熊、数研复盘狮、花叔 3 个微信公众号，412 篇合集文章（4 个合集）+ 种子文章已全部
抓取为 Obsidian 笔记（本地图片、wikilink 嵌入、frontmatter），存于：

```
/Users/qiming/ObsidianWiki/processed/微信知识库/     ← 内容唯一仓库（多机同步）
├── 数据熊/{01_财务分析, 02_财务管理, 03_财务报表, 04_经营分析}/<YYYY-MM-DD 标题>.md
│   ├── attachments/（图片，wikilink 嵌入）
│   └── 目录.md（MOC）
├── 数研复盘狮/  ├── 花叔/
```

全量引用索引（每篇的 obsidian:// 链接 + 原文链接）：
`docs/knowledge-base/08_wechat_sources/INDEX.md`

## 2. 两套实现（同一引擎谱系）

| | FLOW 仓库（项目专用） | 用户技能（标准化工具） |
|---|---|---|
| 位置 | `scripts/wechat_kb/` | `~/.zcode/skills/wechat-article-harvest/scripts/` |
| 入口 | `sync.py`（一条命令全流程） | `wxkb.py`（子命令 init/album/article/sync/moc/index） |
| 配置 | `docs/knowledge-base/08_wechat_sources/`（sources.yaml + queue/ + state/ + logs/ + albums/） | 任意目录的 `kb.yaml`（wxkb init 生成脚手架） |
| 分类 | 内置财经相关性筛选（classify.py，<1.5 分不入库） | 可选 `classify: finance`（classify_finance.py），默认 off |
| 状态 | 已生产运行（417 篇） | 已端到端验证（真实合集 84 篇清单 + 2 篇入库 + MOC） |

**DavyBase 建议以 wxkb 为基线**（配置驱动、无 FLOW 耦合），FLOW 的 sync.py 可作对照实现。

## 3. 能力清单（两套均已实现，除非另注）

- **文章抓取**：requests + 微信客户端 UA；被风控自动换桌面 UA 重试；正文转 Markdown
  （标题/表格 GFM/粗斜体/列表），图片下载 + 大 PNG→JPEG 压缩（--recompress）
- **列表发现**：① 合集公开接口（免登录、不限流，倒序合集协议
  `begin_itemidx`+`is_reverse=1`，见 fetch_album.py）② seed 队列 ③ 收件箱自动归类
  （按文章实际公众号自动登记来源）④ 公众平台接口（httpOnly cookie 需浏览器页面内
  fetch，200013 限流冷却小时级，每页≥4s）⑤ RSS 预留
- **Obsidian 输出**：frontmatter（author `[[wikilink]]`、tags 含 clippings）、图片本地化
  attachments/ + wikilink 嵌入（**必须 wikilink**——标准 md 链接遇空格/括号文件名会断）、
  每账号目录.md MOC、同名去重
- **幂等**：state/seen_urls.json 按 URL 去重；失败 URL 不入 state 自动重试

## 4. 关键坑（踩过的）

1. 本机 TUN 代理 fake-ip：DNS 返回 198.18.0.0/15，SSRF 防护需放行该段（wechatlib._is_dangerous_ip）；
2. mp.weixin.qq.com 直连 curl 会被风控，必须微信客户端 UA；
3. 公众平台会话 cookie 是 httpOnly，Python 读不到——列表接口只能浏览器页面内 fetch，
   或走合集公开接口（推荐，本案例 412 篇全靠它）；
4. `ret=200002` = 登录的不是公众号（如小程序账号）；`ret=200013` = 列表限流；
5. Obsidian 图片嵌入必须 wikilink（见上）；模块命名避开 `collections.py`（遮蔽标准库）；
6. 抓取节奏：正文篇间 ≥2.5s；列表页间 ≥4s；200013 冷却最长 1 小时。

## 5. 运维现状与接手清单

- 每周一 09:00 定时任务（ZCode automation `automation-93fdadc8-6b3c-40f7-9b51-0fdc0322208e`）
  在 FLOW 会话执行 `wechat-kb-sync` 技能 → DavyBase 接手后应将定时任务改为指向 DavyBase 的
  等价流程，并删除本条；
- `state/seen_urls.json` 是去重权威，迁移工具时必须带走（否则全量重抓）；
- 2 篇文章曾因网络瞬断失败（URL 在 queue 中，state 无记录），下次 sync 自动重试；
- 公众平台凭据（可选，仅合集外散篇回填需要）：`~/.config/wx-harvest/credentials.json`
  或环境变量 WECHAT_MP_COOKIE/WECHAT_MP_TOKEN；当前未配置；
- FLOW 侧无代码耦合：接手后可整体删除 `scripts/wechat_kb/` 与 `08_wechat_sources/`
  （或仅保留 INDEX.md 引用），不影响 FLOW 主工程；`99_manifest` 重建脚本会自动适应。

## 6. 联系上下文

- 设计决策与踩坑记录：FLOW 仓库 `docs/knowledge-base/08_wechat_sources/README.md`、
  `00_start_here/PROJECT_STATE.md` 阶段 20；
- 数据口径：412 篇合集条目对账 = 410 篇物理归档 + 2 篇待重试；跨合集重复 URL 取主归属
  （sources.yaml albums 顺序），meta/笔记 frontmatter 的 albums 字段记录全部归属。
