# 机器交接：执行计划与两机协作协议（2026-09-07）

> **交接性质**：本机（Mac A，会话内工作至 2026-09-07 晚）暂停操作；用户将在另一台
> 机器（Mac B）同步本仓库并继续执行。本文档是两机的**信息交换载体**：
> 记录交接时点快照、接下来要执行的任务书、两机协作纪律、以及本机验证过的
> 可迁移经验。Mac B 开工前先读本文档，再按 [CONTINUATION_GUIDE](CONTINUATION_GUIDE.md)
> 的通用流程核对实时状态。

---

## 1. 交接时点快照（以 git 实时核对为准）

| 项 | 值 |
| --- | --- |
| 交接基线 | `9687a5e`（main，已推送；Mac A 停止操作） |
| 数据库迁移头 | `0019_mpm_review`（新增 `mpm_review` JSONB 列，已在 Mac A 本地库应用；Mac B 首次使用库时执行 `alembic upgrade head`） |
| 本地验证 | CI 单元选择器 **369 全绿**；ruff 全绿；mypy 150 文件无错误 |
| 远端 CI | 以 [GitHub Actions](https://github.com/davyzhong/FLOW/actions) 实时为准，不把本地绿外推 |

### 1.1 2026-09-07 单日完成的里程碑（按提交，全部已推送）

| 提交 | 内容 |
| --- | --- |
| `d455fcf` | KB：微信文章《经营分析和财务分析的区别》归档为研究资料六（D039 外部参照，逐卡转录 + 对照分析） |
| `9e4e04f` | 客观报告 v3 渲染器契约收尾（此前 4 个提交 CI failure 的根因修复） |
| `73be446` | **P00 完成**：基线刷新 + I01–I30/C01–C18 差异账本 + 留出组合冻结（tencent_fy2025 新期间 + sf_2026h1 新期间 + **zto_2026q1 新公司**自港交所下载冻结；yto 移 `regression:` 段） |
| `26ee0de` | 图表量纲链修复（10 倍错位三重根因）+ PDF 格式评审包 |
| `00e5655` | **P01 完成**：MPM 语义重构（7 条误标订正 + `mpm_review` 结构化判定 + 迁移 0019 + 导入器强制不变量）、净现比负净利降级、别名 resolver、C03/C04/C18 术语订正、C05/I08 盘点决定 |
| `8696e3e` | **PDF 格式定稿**：用户确认 8 项决策并实施（CDP 每页页脚+页码等，见 §2.3） |
| `8eedd93` | **P02 完成**：主题合同（四问×七专题+十指标子集）、比较合同（五类类型化不可比+预算完成率守卫）、四层覆盖率 |
| `9687a5e` | 指标库审计日志追加（测试运行产生） |

### 1.2 用户已确认的决策（执行中不得回退）

1. **PDF 格式 8 项决策**（2026-09-07 用户逐项确认，记录与实施证据：
   [`docs/implementation/objective-analysis/2026-09-07-format-review.md`](../../implementation/objective-analysis/2026-09-07-format-review.md)）：
   图表自动量纲 + 正文块内统一"亿"；封面两段式单位行；每页页脚+页码
   （CDP footerTemplate 方案）；紧凑连排；引擎表取整（比率4位/百分数2位）；
   红涨绿跌；资产环形图占选列合计；缺表章节保留显式"—"。
2. **MPM 语义**（P01）：`mpm: true` 是监管级断言，必须携带已核验结构化判定；
   管理常用指标只允许 `candidate`；静态字典不得授予监管标签。导入器加载即拒绝违规。
3. **D039–D049 决策链**继续有效；D045 双轨、D047 默认推荐策略、D049 客观基础优先。

---

## 2. 接下来要执行的计划（Mac B 按此操作）

### 2.1 P00 人工剩余（最高优先；阻塞 P05 独立验收，但不阻塞开发）

**独立逐行标准答案录入**——需要一位未参与抽取器开发的人员（或完全不接触
实现代码/解析输出的独立会话），按
[`validation/financial_reports/oracle-register.md`](../../../validation/financial_reports/oracle-register.md)
§1 规程，只读原始 PDF 逐行抄录：

| 待录样本 | 待录内容 | 说明 |
| --- | --- | --- |
| sf_2026q1 | 2 处"量级"值精确化（经营活动现金流量净额等） | manifest 中标注"量级"的行 |
| yto_2026q1 | 2 处"量级"值精确化（所有者权益、经营现金流净额） | 已移回归集，答案仍要精确 |
| tencent_fy2025 | 全部 key items（收入/归母盈利/Non-IFRS 盈利） | 282 页年报，留出 |
| sf_2026h1 | 收入/归母净利润/经营现金流净额/资产总计 | 半年报，留出 |
| zto_2026q1 | 收入/净利润/Adjusted 净利润/经营现金流净额 + Non-GAAP 调节 | 季度公告，留出 |

录完的答案文件放 `validation/financial_reports/oracle/<sample_id>.yaml`，
哈希登记进 oracle-register §4。**铁律：不得以被测抽取器的输出回填。**

### 2.2 P03：确定性拆解、联动提示和边界测试（4–6 人日，P0）

任务书原文见
[`docs/superpowers/plans/2026-09-07-next-stage-upgrade-plan.md`](../../superpowers/plans/2026-09-07-next-stage-upgrade-plan.md)
§3 P03。TDD 纪律：每条规则先写失败测试（正例+反例），再最小实现。要点：

1. **应收与收入增速联看**（I09）：两指标期间对齐（同期间流量）；应收增速
   高于收入增速时输出"联动提示"——提示复核，不自动断言回款恶化（C14：相关性≠原因）。
2. **可加和成本桥 / 驱动拆解**（C08）：拆解各分项之和必须还原总变化额；
   交互项要有明确分配规则；不能加总守恒时显示残差项，不得静默凑整。
3. **CAGR 间隔数**（C07）：n 年增速除以 n−1（期数减一），反例测试锁定。
4. **比率方向与阈值适用条件**（C06）：流动比率"约 2 为佳"类经验值只作提示，
   带行业/主体适用标注；禁止普适阈值硬判定。
5. **ROE 分母口径提示**（I12）：期末权益 vs 平均余额已注口径（渲染层已做）；
   分析层引用时必须携带口径标签并做反例测试。
6. **登记缺陷处置**（来自 PDF 评审轮，见 format-review 文档 §4）：
   - **JDL 归一化唯一键**：港股 IFRS 报表存在合法同名行项目（借款/租赁负债在
     流动、非流动分组下各一行），`uq_statement_normalized_item` 假设"每报表
     行名唯一"不成立。需契约决策：唯一键引入分组/序号维度（迁移）或归一化层
     合并同名行（保留分组语义）。**先决策再动 schema**。
   - **腾讯种子利润表缺行**：附录"除税前盈利 696.90 亿"与所列项目差 111.84 亿，
     疑缺"其他收益净额"类行——对照原文 PDF 补种子数据（D049：缺失不补造）。
   - **引擎"杜邦三分解"口径标注**：引擎值（净利润总额口径 ≈2.38%）与正文
     杜邦因子乘积（归母口径 2.26%）同名不同值，引擎条目名/口径说明需细化。
7. **rnd_exp 科目映射**（P01 盘点遗留）：研发费用在 2024 汇编中的准确科目
   编号待《应用指南汇编 2024》原文核对后补 `REPORT_ITEM_SUBJECTS`（importer.py）。

> **完成登记（2026-09-08）**：§2.2 可执行项全部完成，执行入口已转统一计划 U 系列
> （P03 = U2）。逐项证据：I09 联动提示 `c9c6ff0`；C08 可加和桥 `876ce01`；
> C07 CAGR `e089e36`；C06 阈值提示 + I12 口径标签 `8b15cd1`；6.2 腾讯利润表缺行
> `08cfa5c`（根因是归一化映射 `item_alias_map_v1` 缺"投资收益净额及其他"等三行，
> 非种子数据缺失；守恒锁定：逐行加总 = 除税前 69690）；6.3 杜邦口径标注 `f557547`
> （条目名/因子全链携带「净利润总额口径·期末权益·未年化」+ 锁定测试）。
> `tests/analysis` + `tests/statements` 119 passed（2026-09-08 复验）。
> 两项外部依赖移交统一计划断点：6.1 JDL 同名行项目唯一键契约决策（**待用户确认**，
> 建议：唯一键加入分组序号维度，保留披露原文分组语义）；7 rnd_exp 科目编号
> （待《应用指南汇编 2024》原文）。后续执行：统一计划 U3（= P04）。

### 2.3 已完成、另一台机器不得重做的

- **P00**：基线刷新、差异账本、留出冻结全部完成（`next-stage-baseline.md`）——
  剩余只有 §2.1 的人工录入。
- **P01**：MPM/语义订正已实施并测试锁定（`tests/metrics/test_mpm_classification.py`）。
- **P02**：主题合同（`config/analysis/objective_topics_v1.yaml` + `analysis/topics.py`）、
  比较合同（`metrics/comparison_contract.py`）、四层覆盖率
  （`metric_library_store/coverage.py`）已落地并测试锁定
  （`tests/analysis/test_topic_contracts.py`、`tests/metrics/test_coverage_layers.py`）。
- **PDF 渲染链**：v3 渲染器 + CDP 打印器已按用户 8 项决策定稿，
  是 `/reports` "导出客观分析 PDF"的实现基准（P08 接线时复用，不重写）。

### 2.4 P04–P12 概览（P03 后依依赖图推进）

P04 来源与快照投影 → P05 独立全行验证（**依赖 §2.1 人工录入完成**）→
P06 客观报告门禁 → P07 分析工作台 → P08 统一冻结与渲染（复用已定稿渲染链，
真实 PDF 打印已有）→ P09 完整旅程回归（用 §0 基线文档第 4 节缺陷清单做回归）→
P10 发布运行保障 → P11 阶段总验收 → P12 内部试点（另需数据授权）。
预算/同行/情景比较只在前提具备时可选（P02 比较合同已实现守卫）。

---

## 3. 两机协作纪律（信息交换协议）

1. **开工前**：`git pull --rebase origin main`；`git log --oneline -8` 核对
   最新提交；`git status` 清点工作区。本日已两次发生并行推进（另一会话/另一
   机器与 Mac A 同时提交），push 被拒时**一律 rebase 后再推**，禁止 force push。
2. **每个阶段性任务结束**：commit + push（AGENTS.md 收尾协议）。提交信息写清
   任务范围、测试证据；只提交本任务范围文件。
3. **共享文件冲突**：`var/metric_library_audit.jsonl` 为追加型日志，两边同时
   追加时 rebase 冲突取**并集**（保留双方行）；`99_manifest/*` 冲突时重跑
   再生脚本取结果。
4. **知识库变更**（新增/修改 `docs/knowledge-base/` 下文件）：更新对应 INDEX，
   并重新生成 `99_manifest/inventory.tsv` 与 `sha256sums.txt`
   （排除 `99_manifest/` 自身与 `.DS_Store`，格式见现有文件）。
5. **决策变更**：先查 `04_decisions/DECISION_LOG.md` 与影响图；新决定追加新
   D 条目，不改写历史。
6. **状态同步**：PROJECT_STATE 按其 §5 更新纪律维护；本交接文档对应章节执行
   完成后，在该节标注完成提交哈希，或按日期新增交接文档取代本文档的"接下来"部分。

## 4. 可迁移环境经验（Mac A 验证过的事实）

- **测试**：`cd services/api && .venv/bin/python -m pytest <路径> -q`；
  CI 单元选择器为
  `pytest tests --ignore tests/intake --ignore tests/dashboard --ignore tests/investigations --ignore tests/copilot`
  （全量约 21 分钟，369 项）。**必须从 services/api 目录跑**，从仓库根跑会因
  rootdir/相对路径混乱产生假失败。
- **数据库迁移**：`alembic` 命令需要环境变量，裸跑会报 pydantic missing：
  `DATABASE_URL=postgresql+psycopg://flow:flow_dev_only@127.0.0.1:5432/flow`
  （另 REDIS_URL/S3_* 见 `scripts/generate_objective_report_pdfs.py` 头部 defaults）。
- **PDF 生成**：`services/api/.venv/bin/python scripts/generate_objective_report_pdfs.py`
  （需 Postgres/Redis/MinIO 基础设施在跑 + 固定 Chromium；
  缺 Chromium 抛 `ChromiumNotFoundError`，定位顺序 FLOW_CHROMIUM_PATH →
  Playwright 缓存）。京东物流 FY2025 当前因同名行项目唯一键冲突被跳过（§2.2-6）。
- **渲染链教训**（改报告渲染前必读，均有测试/评审背书）：
  `objective_report_charts._scale` 输入必须是**元**（披露原单位需先经渲染器
  `yuan()` 换算，曾双重错位 10 倍）；matplotlib suptitle y>1 会被 savefig 裁切
  （已用 `bbox_inches="tight"`）；每页 CSS fixed 页脚会遮切正文（必须走 CDP
  footerTemplate）；打印 CSS 必须强制 `color-scheme: light`（否则 Chromium
  无头打印吃系统深色模式）。
- **网络**：微信文章抓取用 MicroMessenger UA + `data-src` 提取正文图；
  港交所披露易可编程下载（`titleSearchServlet.do` 按 stockId 查公告，
  prefix.do 解析股票代码→stockId，如中通 2057.HK = 1000057949）。
- **依赖**：`websockets` 已声明为直接依赖（CDP 打印用；版本锁定由 uv.lock 承担）。
- **本机特有、不可假设另一台机器相同**：本地 Docker（flow-postgres/redis/minio）
  常驻；MinIO 历史上有 host PUT 超时（2026-09-06 根因已修，当前正常）。

## 5. 完成登记

Mac B 执行 §2 各任务后：更新本文档对应小节（打勾 + 提交哈希），或按上述
协议新增日期命名的交接文档；同步刷新 PROJECT_STATE 与 manifest。
