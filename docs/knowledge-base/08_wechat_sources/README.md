# 08 公众号素材库（财经 / 经营分析向）

本目录持续收录对 FLOW 有参考价值的微信公众号文章，初始来源：

| 来源 id | 公众号 | 账号 ID | fakeid | 定位 |
|---|---|---|---|---|
| `shujuxiong` | 数据熊 | gh_d55144ba7fe2 | Mzg2MTg5OTgzNA== | 财务分析实务与月度经营分析报告模板，按 4 个合集分类归档（见下） |
| `shuyan_fupanshi` | 数研复盘狮 | gh_78506a7234d3 | MzY5NTM2NTA5NA== | 经营分析报告、毛利/净利润专题复盘 |
| `花叔`（自动登记） | 花叔 | gh_13cc971d267c | Mzg2OTA1OTAxNA== | Excel 数据处理 skill 与数据方法（Huashu Excel 作者） |

### 数据熊的 4 个知识库合集

按公众号官方合集分类归档（`shujuxiong/<类别目录>/`，每类含独立 INDEX.md）：

| 类别目录 | 合集 | album_id | 篇数 |
|---|---|---|---|
| `01_财务分析` | 财务分析 | 3888472289255505920 | 84 |
| `02_财务管理` | 财务管理 | 3705887141604474885 | 138 |
| `03_财务报表` | 财务报表 | 3627226562623291398 | 26 |
| `04_经营分析` | 经营分析 | 3714603110065618949 | 191 |

- 合集清单（url/title/时间）存于 `albums/<topic>.json`，是目录归位与新文章自动分类的依据；
- 一篇文章属于多个合集时，物理归入优先级最前的类别目录（sources.yaml 顺序），meta.json 的
  `albums` 字段记录全部归属，各类别 INDEX.md 均可检索到；
- 跨合集重复 URL 不重复抓取（state 去重）；
- 不属于任何合集的文章保留在 `shujuxiong/` 平铺层（如早期手动种子）。

> 背景：项目"阶段 0"的五篇奠基研究材料（`02_research/original/`）经原始链接复核，
> 4 篇来自数据熊、1 篇来自花叔——这些账号正是项目早期灵感来源，全量归档价值高。
> 2026-09-02 起按用户提供的 4 个合集对数据熊做全量归档。

这些公众号与项目"阶段 0"的五篇研究资料（`02_research/original/`）主题同源，是下一阶段方向验证的重要外部参照。

## 目录结构

```text
08_wechat_sources/
├── README.md                 # 本文件：来源与更新协议
├── sources.yaml              # 来源注册表（抓取配置）
├── INDEX.md                  # 全量文章索引（自动生成）
├── queue/                    # 待抓队列：pending_<来源id>.txt，一行一个文章链接
├── state/seen_urls.json      # 已处理 URL 状态（幂等去重，自动维护）
├── logs/                     # excluded.jsonl / errors.jsonl / sync_report.jsonl
├── shujuxiong/               # 每个账号一个目录
│   └── <YYYYMMDD>_<标题slug>/
│       ├── article.md        # 正文 Markdown（YAML frontmatter + 来源信息）
│       ├── meta.json         # 结构化元数据（含图片清单与 sha256）
│       └── images/           # 正文与封面图片（imgNNN.* / cover.*）
└── shuyan_fupanshi/
```

## 与知识库其他目录的关系

- 本目录是**持续更新的外部素材库**，不是不可变档案；修正一律以新增文件完成；
- 从素材中提炼的结论应写入 `02_research/synthesis/`，原始素材留在本目录；
- 引用素材时注明公众号与原文链接；素材仅供内部研究学习，版权归原作者。

## 同步流水线

全部逻辑在 `scripts/wechat_kb/`：

```bash
uv run scripts/wechat_kb/sync.py            # 完整同步：发现→抓取→筛选→入库→索引→manifest
uv run scripts/wechat_kb/sync.py --dry-run  # 只发现与解析，不写库
uv run scripts/wechat_kb/sync.py --limit 5  # 限制本批处理篇数
```

### 文章发现通道

1. **seed 队列**（保底）：把文章链接粘到 `queue/pending_<来源id>.txt`，微信里"复制链接"即可；
   去重由 `state/seen_urls.json` 负责，队列文件可整批保留（--limit 截断不丢链接）；
2. **合集（album）**：`scripts/wechat_kb/fetch_album.py` 直接爬公众号合集公开接口（无需登录、
   不受 appmsg 200013 限流），自动翻页（倒序合集自动带 `is_reverse=1`、参数 `begin_itemidx`）：
   ```bash
   uv run scripts/wechat_kb/fetch_album.py --album-url "<合集链接>" \
       --out-queue docs/knowledge-base/08_wechat_sources/queue/pending_shujuxiong.txt
   ```
   数据熊两个合集已登记在 `sources.yaml` 的 `albums` 字段（财务分析 84 篇 + 财务管理 138 篇）；
3. **收件箱自动归类**：不确定来源的链接放 `queue/pending_inbox.txt`，抓取时按文章实际公众号
   自动归档并登记到 `sources.auto.yaml`；
4. **mp_platform 全量通道**：微信公众平台接口可枚举账号**全部历史文章**（含未进合集的）：
   - 会话 cookie（slave_sid）是 httpOnly，脚本读不到值，推荐用**浏览器页面内 fetch** 调
     `searchbiz` / `appmsg` 接口拉列表（同源自动带 cookie），把链接写入队列后再同步；
     操作步骤见 `wechat-kb-sync` 技能或 `wechat-article-harvest` 技能；
   - `sources.yaml` 已沉淀各账号稳定 `fakeid`，拉列表可跳过 searchbiz 直接分页 appmsg；
   - 列表接口有严格频率限制（`ret=200013`，冷却 1 分钟到 1 小时）：每页间隔 ≥4 秒、
     每会话每账号只 searchbiz 一次；正文抓取不受该配额影响；
5. **RSS**：`sources.yaml` 中给来源加 `feed:` 字段即可接入 wechat2rss 等付费源。

### 筛选规则

关键词加权打分（`classify.py`）：财务/经营分析强信号 ×3（标题）/ ×1（正文），泛管理弱信号低权重，
总分 ≥3 判定 relevant 入库，1.5–3 为 borderline 默认入库，<1.5 判定 excluded 仅记录不入库。
分类写入 frontmatter（财务分析 / 经营分析 / 预算与成本 / 报告与汇报模板 / 数据方法与工具）。

### 原始 HTML 的处理

原始网页 HTML 体积大（单篇 3MB+）且 95% 为平台脚本，只落 `work/wechat_kb/html_cache/` 缓存（不入
git）；知识库内以 `article.md + images/ + meta.json` 作为归档凭据，正文与图片均本地保存，图片记录
sha256 可溯源。此约定与 `02_research/original/` 保留完整 HTML 的做法不同，属有意的取舍。

### 图片体积与压缩

批量入库（合集回填）时加 `--recompress`：大于 200KB 的正文 PNG 自动转 JPEG q88（带透明通道的保留
PNG），幻灯片截图类体积降 70%+，meta.json 保留原图 URL 与压缩后 sha256 可溯源。2026-09 首批种子
文章（无压缩）保留原始 PNG 作为高保真样例。

### Obsidian 导出

`uv run scripts/wechat_kb/export_obsidian.py` 把素材库导出到本机 Obsidian 库
`/Users/qiming/ObsidianWiki/Clippings/微信知识库/`（仓库外，不提交）：按 公众号/合集 目录组织、
图片本地化到各合集 `attachments/`、frontmatter 对齐 Web Clipper 习惯、每公众号生成「目录.md」MOC。
幂等，内容未变的笔记自动跳过；每周同步有新增后建议顺手执行。

## 更新协议（每周）

1. 运行 `uv run scripts/wechat_kb/sync.py`；
2. 检查 `logs/` 与 `git status`，确认只新增了本任务范围的文件；
3. 若 INDEX.md、manifest 有变化，一并提交（提交信息建议 `wechat-kb: weekly sync <日期>`）；
4. 推送 `origin`。

对应技能：`/wechat-kb-sync`（含自动提交与推送步骤）。
