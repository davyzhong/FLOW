---
doc_id: FLOW-COMPETITIVE-MATRIX-CODE
title: 代码级方法论对照矩阵 · FLOW × 9 个竞品/方法论
doc_type: competitive-research
status: current
version: 2.0
created_at: 2026-09-15
updated_at: 2026-09-15
owner: FLOW
related: [./summary-and-positioning.md, ./optimization-checklist.md]
---

# 代码级方法论对照矩阵（v2.0）

> 配套 [summary-and-positioning.md](summary-and-positioning.md) 的方法论对照表。每个 ✅/❌ 都映射到具体文件路径和函数。下次做能力评估时按这张表查即可。

## 一、维度定义（17 个）

| # | 维度 | 含义 |
| --- | --- | --- |
| D1 | 杜邦三因子 | 净利率 × 资产周转率 × 权益乘数 |
| D2 | 杜邦五因子 | + 税后负担率 + 利息负担率 |
| D3 | 杜邦二级子项 | 每因子下 5 个子指标 |
| D4 | 同业对标 | 跨公司对比 |
| D5 | 行业基准 | 行业均值 / 标杆 / 末位 |
| D6 | 趋势分析 | 多期 + CAGR + 同比 |
| D7 | 情景 / 敏感性 | "如果...那么..." |
| D8 | DCF / EVA | 经济利润 + 估值 |
| D9 | BSC 四维度 | 财务 + 客户 + 流程 + 成长 |
| D10 | 战略框架 | BCG Matrix / 五力 / 战略地图 |
| D11 | 中文财报 | CAS / IFRS / 中文报表 |
| D12 | 私有部署 | on-premise + 数据合规 |
| D13 | AI 问数 | 自然语言查询财务数据 |
| D14 | 反向解析 | PDF → 事实库 |
| D15 | 指标版本化 | v0/v1/v2 评审集 |
| D16 | 公开 API | typed + OpenAPI |
| D17 | 覆盖矩阵 | 指标 × 公司 × 期间 |

## 二、FLOW 代码全景（前置地图）

### 前端（apps/web）

```
apps/web/
├── app/                                  Next.js 路由层
│   ├── metric-library/page.tsx            /metric-library 入口
│   ├── statements/page.tsx                /statements 入口
│   └── api/v1/[...path]/                  API 路由代理到后端
├── components/                           UI 组件
│   ├── metric-library/
│   │   ├── metric-library-app.tsx          主组件：指标字典 + 杜邦拆解
│   │   ├── metric-library.css              报告风样式
│   │   └── dependency-graph.tsx            指标依赖图（ECharts / SVG）
│   ├── statements/
│   │   ├── statement-app.tsx               财报浏览器主组件
│   │   ├── statement-view.ts               视图层（指标计算 + 杜邦因子）
│   │   ├── review-panel.tsx                治理复核
│   │   ├── charts/
│   │   │   ├── kpi-cards.tsx               KPI 卡带（圆形首字徽章）
│   │   │   ├── donut-chart.tsx             环形图（资产/资本构成）
│   │   │   ├── waterfall-chart.tsx         瀑布图（利润形成 / 现金桥）
│   │   │   └── grouped-bar-chart.tsx       分组柱图（现金流三活动）
│   ├── dashboard/
│   │   ├── dashboard-state.tsx             仪表盘状态机
│   │   ├── metric-grid.tsx                 指标网格
│   │   ├── margin-matrix.tsx               利润率矩阵
│   │   ├── trend-panel.tsx                 趋势面板
│   │   ├── profit-bridge-panel.tsx         利润桥面板
│   │   └── product-performance-table.tsx   产品业绩表
│   └── shell/
│       ├── app-shell.tsx                   AppShell 包装器（左侧工作流导航）
│       └── app-shell.css
└── lib/api/client.ts                       typed API client
```

### 后端（services/api）

```
services/api/src/flow_api/
├── metrics/
│   ├── calculator.py                      指标计算引擎
│   ├── repositories.py                    仓库层
│   └── source_rows.py                     数据源行映射
├── metric_library_store/
│   └── coverage.py                        覆盖矩阵逻辑
├── operations/
│   └── facts.py                           事实查询接口
├── publishing/
│   └── service.py                         发布 / 报告生成
├── data_contract/                         工作簿 / 解析 / 持久化
├── analysis/
│   └── service.py                         分析服务（趋势 / 同业对标）
├── copilot/                               AI 助手（待补）
├── security/                              鉴权
└── main.py                                FastAPI 入口
```

### 数据与脚本（scripts/ + config/ + docs/）

```
scripts/
├── build_static_library_site.py           静态资料库生成器（HTML / Widget）
├── p5_extract_*.py                        P5 反向解析（顺丰/京东物流/阿里）
├── p5_query_facts.py                      事实查询 + 覆盖矩阵生成
├── finalize_metric_dictionary*.py         指标字典 v0/v1 终稿
├── finalize_accounting_foundation.py      会计基础数据终稿
├── summarize_dashboard.py                 仪表盘汇总
└── ...

config/metrics/
├── metric_dictionary_v0_draft.yaml        通用 + 物流指标 v0
├── metric_dictionary_v1.yaml              v1 终稿
├── accounting_foundation_v1.yaml          167 科目
├── p5_metric_coverage_v1.yaml             P5 覆盖矩阵
├── ...

docs/
├── implementation/p5/                     P5 反向解析文档
│   ├── statement_facts.yaml               670 条事实
│   ├── metric_coverage_matrix.md         覆盖矩阵说明
│   └── item_alias_map_v1.yaml             别名映射
├── library/                               静态资料库生成产物
│   ├── index.html                          报告级长滚动（544 KB）
│   └── widget.html                         看板 Widget 变体
└── competitive/                            竞品调研（本文档所在）
```

## 三、代码级对照矩阵

| 维度 | FLOW 状态 | 实现位置（精确路径） | 关键函数 / 数据源 | 状态码 |
| --- | --- | --- | --- | --- |
| **D1** 杜邦三因子 | ✅ | `scripts/build_static_library_site.py:1079-1110` + `apps/web/components/statements/statement-view.ts:80-100` | `dupontFactors(company, period)` 返回 `{netMargin, assetTurnover, equityMultiplier, roe3}` | ✓ 已上线 |
| **D2** 杜邦五因子 | ✅ | `scripts/build_static_library_site.py:1115-1130` | `dupontFormula5()` 含 `{taxBurden, intBurden, ebitMargin}` | ✓ 已上线 |
| **D3** 杜邦二级子项 | ✅ | `scripts/build_static_library_site.py:1133-1170` | `dupontReportMini()` 输出毛利率 / 周转 / 杠杆子项 | ✓ 已上线 |
| **D4** 同业对标 | ✅ | `scripts/build_static_library_site.py:1180-1230` | `renderDupontAnalysis()` 5 公司对比表 + 柱图 | ✓ 已上线 |
| **D5** 行业基准 | ⚠ 部分 | 无独立实现；杜邦对比表用 5 家公司作为代理样本 | 当前数据：5 家公司 = 行业代理 | ⚠ 缺真实行业基准数据 |
| **D6** 趋势分析 | ⚠ 部分 | `apps/web/components/dashboard/trend-panel.tsx` + `services/api/src/flow_api/analysis/service.py` | 单家公司可看趋势；跨公司对比未实现 | ⚠ 需扩 |
| **D7** 情景 / 敏感性 | ❌ | 无 | — | ❌ 未实现 |
| **D8** DCF / EVA | ❌ | 无 | — | ❌ 未实现 |
| **D9** BSC 四维度 | ❌ | 无 | — | ❌ 未实现 |
| **D10** 战略框架 | ⚠ 部分 | `apps/web/components/metric-library/dependency-graph.tsx` 有指标依赖图，但不是战略地图 | 仅依赖图，缺 BCG / 五力 | ❌ 未实现 |
| **D11** 中文财报 | ✅ | `scripts/p5_extract_*.py` + `docs/implementation/p5/statement_facts.yaml` | CAS/IFRS 双准则；中文 PDF 抽取 | ✓ 已上线 |
| **D12** 私有部署 | ✅ | `infra/compose.yaml` + Helm chart（待补） | Docker Compose / K8s | ✓ 已上线 |
| **D13** AI 问数 | ❌ | 无；`services/api/src/flow_api/copilot/` 为空 | — | ❌ 未实现 |
| **D14** 反向解析 | ✅ | `scripts/p5_extract_sf.py` + `scripts/p5_extract_jdl.py` + `scripts/p5_extract_alibaba.py` | PDF → 事实库；`statement_facts.yaml` 670 条 | ✓ 已上线 |
| **D15** 指标版本化 | ✅ | `config/metrics/metric_dictionary_v0_draft.yaml` + `v1.yaml` + 决策编号 D040/D047 | YAML 版本管理 + docs/40_specs 决策日志 | ✓ 已上线 |
| **D16** 公开 API | ✅ | `packages/contracts/openapi.json` + `services/api/src/flow_api/main.py` | typed OpenAPI 3.1 + Python/TS SDK | ✓ 已上线 |
| **D17** 覆盖矩阵 | ✅ | `scripts/p5_query_facts.py` + `config/metrics/p5_metric_coverage_v1.yaml` + `apps/web/components/metric-library/metric-library-app.tsx:600-700` | 40 指标 × 15 快照 + 缺口标注 | ✓ 已上线 |

## 四、能力补足路径（17 维度 × "如何补"）

### P0 优先（直接商业价值）

**D5 行业基准数据** — 接入第三方
- 数据源：Wind 行业 API（最权威但贵）/ Choice 行业数据（中价位）/ 通联行业聚合（中价位）/ 自建爬虫（低成本但合规风险）
- 接入位置：新建 `services/api/src/flow_api/industry_benchmarks/` 模块
- 存储：`config/benchmarks/{industry}_benchmark_v1.yaml`
- 渲染位置：`scripts/build_static_library_site.py` 的 `renderDupontAnalysis()` 加行业行

**D13 AI 问数** — RAG 实现
- 架构：LangChain / LlamaIndex + Qwen2.5 / DeepSeek-V3 / GPT-4o
- 数据源：事实库（670 条）+ 指标字典（49+15）+ 文档（30+ 篇）
- 向量存储：pgvector（已可用） / Chroma
- 代码位置：新建 `services/api/src/flow_api/copilot/` 的 `rag_service.py` + `qa_router.py`
- 入口：`apps/web/app/api/copilot/qa/route.ts`
- 前端：`apps/web/components/copilot/qa-panel.tsx`

### P1 增强（差异化）

**D6 趋势分析** — 多公司对比
- 已实现：单公司 trend-panel
- 待实现：跨公司趋势对比
- 代码位置：`apps/web/components/dashboard/trend-panel.tsx` 加 `multiCompany` 模式
- API：`services/api/src/flow_api/analysis/service.py` 加 `cross_company_trend()`

**D7 情景 / 敏感性**
- 新建：`apps/web/components/dupont/scenario-panel.tsx`
- 输入：5 因子调整假设（净利率 ±x pct / 周转率 ±y 倍 / 杠杆 ±z 倍）
- 输出：调整后的 ROE + 表格 / 雷达图
- 后端：`services/api/src/flow_api/analysis/scenario.py`（纯前端算也行）

**D8 DCF / EVA**
- 新建：`services/api/src/flow_api/valuation/dcf_engine.py`
- 输入：5 年预测 + WACC + 永续增长率
- 输出：DCF 估值 + EVA 趋势
- 位置：`apps/web/components/valuation/dcf-panel.tsx`

### P2 拓展（生态）

**D9 BSC 四维度**
- 数据模型：扩 `config/metrics/bsc_metrics.yaml`（客户 / 流程 / 成长指标）
- 渲染：`scripts/build_static_library_site.py` 加 `renderBSC()`
- 注意：客户 / 流程 / 成长指标需要公司主动上报，公开财报没有

**D10 战略框架**
- BCG Matrix：基于公司业务的「市场份额 × 增长率」
- 五力：基于公开行业数据
- 战略地图：基于 BSC 因果链
- 渲染：新建 `apps/web/components/strategy/` 三个组件

## 五、待办：FLOW v2 路线图（与代码位置一一对应）

| 任务 | 文件位置 | 验收 | 工作量 |
| --- | --- | --- | --- |
| 1.1 行业基准 | 新建 `services/api/src/flow_api/benchmarks/` | 3 个行业对照表 | 4-6 人月 |
| 1.2 AI 问数 | 新建 `services/api/src/flow_api/copilot/` + `apps/web/components/copilot/` | 100 条问数 ≥90% 命中 | 8-12 人月 |
| 1.3 数据扩张 | 扩 `scripts/p5_extract_*.py` + `docs/implementation/p5/statement_facts.yaml` | 80 份财报 + 5000+ 事实 | 6-9 人月 |
| 2.1 趋势扩 | 改 `apps/web/components/dashboard/trend-panel.tsx` + `services/api/src/flow_api/analysis/service.py` | 跨公司趋势对比 | 2-3 人月 |
| 2.2 敏感性 | 新建 `apps/web/components/dupont/scenario-panel.tsx` | 杜邦详情页有敏感性控件 | 2 人月 |
| 2.3 DCF / EVA | 新建 `services/api/src/flow_api/valuation/dcf_engine.py` | 每家公司都有 DCF + EVA | 6 人月 |
| 2.4 行业模板 | 扩 `scripts/build_static_library_site.py` 的 `renderIndustryTemplate()` | 5 个行业 dashboard 模板 | 3-4 人月 |
| 2.5 拖拽 dashboard | 新建 `apps/web/components/dashboard/editor/` | 拖拽式 dashboard editor | 12-18 人月 |
| 2.6 多业务线 | 扩 `apps/web/components/dupont/` + 业务段数据 | 5 家公司业务段杜邦 | 6-8 人月 |
| 2.7 BSC | 新建 `apps/web/components/bsc/` | BSC 四维度分析 | 6 人月 |
| 2.8 MD&A 自动写 | 新建 `services/api/src/flow_api/copilot/mda_writer.py` | 自动生成 MD&A 报告 | 6 人月 |

## 六、监控指标（每季度评估）

| 指标 | 当前值（2026-09） | 目标（2027-09） |
| --- | --- | --- |
| D5 行业基准覆盖行业数 | 0 | 3 |
| D13 AI 问数命中率 | 0% | ≥90% |
| D14 财报样本数 | 14 | 80 |
| D17 覆盖矩阵指标数 | 40 | 100 |
| 代码覆盖率（核心域） | — | ≥70% |
| 测试通过率 | 100% | 100% |
| 用户活跃（DAU） | — | 100+ |

## 七、维护建议

每季度更新一次本对照矩阵：
- 新增能力 → 在矩阵中加 ✅ + 代码位置
- 优化能力 → 更新代码位置 + 验收标准
- 退出能力 → 标 🗑️ 并记录原因
- 矩阵变更要写到 `docs/90_archive/matrix-history.md`

下次更新：2026-12。