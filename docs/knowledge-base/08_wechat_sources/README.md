# 08 公众号素材库（财经 / 经营分析向）

本目录持续收录对 FLOW 有参考价值的微信公众号文章，初始来源：

| 来源 id | 公众号 | 账号 ID | biz | 定位 |
|---|---|---|---|---|
| `shujuxiong` | 数据熊 | gh_d55144ba7fe2 | Mzg2MTg5OTgzNA== | 财务分析实务、月度经营分析报告模板 |
| `shuyan_fupanshi` | 数研复盘狮 | gh_78506a7234d3 | MzY5NTM2NTA5NA== | 经营分析报告、毛利/净利润专题复盘 |

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
2. **mp_platform 全量通道**：微信公众平台接口可枚举账号**全部历史文章**。需要任一公众号账号登录
   `mp.weixin.qq.com` 后，把浏览器 Cookie 与 URL 中的 `token` 存为 `work/wechat_kb/mp_credentials.json`
   （`work/` 不入 git，凭据严禁提交）：
   ```json
   {"cookie": "slave_sid=...; ...", "token": "123456"}
   ```
3. **RSS**：`sources.yaml` 中给来源加 `feed:` 字段即可接入 wechat2rss 等付费源。

### 筛选规则

关键词加权打分（`classify.py`）：财务/经营分析强信号 ×3（标题）/ ×1（正文），泛管理弱信号低权重，
总分 ≥3 判定 relevant 入库，1.5–3 为 borderline 默认入库，<1.5 判定 excluded 仅记录不入库。
分类写入 frontmatter（财务分析 / 经营分析 / 预算与成本 / 报告与汇报模板 / 数据方法与工具）。

### 原始 HTML 的处理

原始网页 HTML 体积大（单篇 3MB+）且 95% 为平台脚本，只落 `work/wechat_kb/html_cache/` 缓存（不入
git）；知识库内以 `article.md + images/ + meta.json` 作为归档凭据，正文与图片均本地保存，图片记录
sha256 可溯源。此约定与 `02_research/original/` 保留完整 HTML 的做法不同，属有意的取舍。

## 更新协议（每周）

1. 运行 `uv run scripts/wechat_kb/sync.py`；
2. 检查 `logs/` 与 `git status`，确认只新增了本任务范围的文件；
3. 若 INDEX.md、manifest 有变化，一并提交（提交信息建议 `wechat-kb: weekly sync <日期>`）；
4. 推送 `origin`。

对应技能：`/wechat-kb-sync`（含自动提交与推送步骤）。
