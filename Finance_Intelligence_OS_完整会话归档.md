# Finance Intelligence OS / AI 原生财务经营分析平台
## 当前会话完整归档（Markdown）

> 归档说明  
> 本文档整理自当前会话中围绕“财务驾驶舱、Excel/数据分析 Skill、AI 财务分析引擎、HTML/PPT 报告生成、Finance Intelligence OS”展开的全部核心讨论。  
> 目标是尽可能完整保留：用户原始需求、参考资料、链接、补充材料、对 huashu-excel 的研究、产品定位演进、系统架构、指标与语义层、分析 Skill、Investigation Playbook、Insight/Issue/Action 闭环、MVP 建议、技术路线与后续工作方向。  
> 文末附“可直接转入 Codex 的开发上下文摘要”。

---

# 一、最初需求：想做三类东西

用户最初提出，自己还没有完全想清楚最终产品形态，但看过多份资料以后，判断想做三类能力。

## 1. 财务领域经营驾驶舱

目标不是通用 BI，而是偏专业财务和经营分析的驾驶舱。

### 面向人群

- 总经理
- 财务总监
- 财务 BP / FP&A 等

### 核心功能

需要输入各种财务和经营数据，从多个维度和角度反映当前财务状况，并能够：

- 形成经营分析
- 形成财务分析
- 生成经营分析报告
- 生成财务分析报告
- 对数据做多维指标分析
- 支持图表展现
- 进行深入数据挖掘

### 产品形态

用户暂时没有完全确定是：

- Web 网站
- 网页应用
- 本地工具
- 其他交互形式

但明确倾向于：

> 一个后台数据处理系统 + 指标定义系统 + Web 前端多维数据展示。

用户同时强调：

> 功能本身其次，更重要的是专业财务数据分析能力。

---

## 2. 类似 Scale / Excel 数据分析工具

用户希望参考一种用于 Excel 数据加工和分析的 Skill / 工具。

真正感兴趣的并不是 Excel 处理本身，而是：

> 它比较理解各种数据分析方法，能深入做数据挖掘。

后续用户明确指出，这个 Skill 的具体代码仓库为：

https://github.com/alchaincyf/huashu-excel

---

## 3. 分析报告生成

用户希望数据导入并完成分析之后，可以输出正式报告。

可能形式包括：

- PPT
- HTML
- 后续可能包括 PDF / DOCX

---

## 4. 最初提供的 5 篇参考资料

用户提供：

1. https://mp.weixin.qq.com/s/AEhX1pkJhGyMmMC-oNQj8w
2. https://mp.weixin.qq.com/s/mN2YjzSnQUKJKZy3NjKf6w
3. https://mp.weixin.qq.com/s/YWmKQftjveqpNjOydDmT_A
4. https://mp.weixin.qq.com/s/ZMuBnCKvjM9UsqpG-nxzxA
5. https://mp.weixin.qq.com/s/7gYbxcW81EtUZQOvpZTOkw

最初这些微信文章无法直接从当前环境完整读取，因此早期讨论主要基于用户描述、公开产品交叉研究和后续补充资料。

---

# 二、第一次核心判断：不是三个产品，而是一个 Finance Intelligence Workspace

讨论中首先形成的核心判断是：

> “财务驾驶舱 + Excel/数据分析 + PPT/HTML 报告”不应该分别立项。

更合理的定义是：

# Finance Intelligence Workspace

即：

> 面向 CEO / CFO / Finance BP 的 AI 财务经营分析工作台。

三种表面形态分别承担不同角色：

| 用户原始设想 | 更准确的系统角色 |
|---|---|
| 财务驾驶舱 | 消费与交互层：看数据、看异常、钻取、追问 |
| Excel / 数据分析工具 | 分析计算层：清洗、统计、挖掘、诊断 |
| PPT / HTML 报告 | 表达与传播层：形成正式管理叙事 |

真正的核心资产不是这三个界面，而是中间的：

# Finance Analysis Engine

也就是：

> 数据进来以后，到底应该怎么算、看什么、发现什么、怎么解释、继续往哪里钻。

---

# 三、为什么不建议从“驾驶舱”本身开始

传统 BI 大致是：

```text
Data
→ Metric
→ Chart
```

例如：

- 收入：12.8 亿
- 利润：6200 万
- 毛利率：14.2%
- 同比：+7.2%

但用户真正想做的专业分析应该进一步演进为：

```text
Data
→ Metric
→ Signal
→ Diagnosis
→ Explanation
→ Decision
```

例如：

> 本月收入同比增长 7.2%，但经营利润同比下降 13.6%。  
> 收入增长主要来自华东区域业务量增长，而非价格提升。  
> 毛利下降 2.4ppt，其中约 1.3ppt 来自运输采购成本上升，0.7ppt 来自低毛利客户占比提高，剩余部分主要来自产品组合变化。  
> 若当前趋势持续，Q4 EBIT Margin 可能低于年度预算约 1.1–1.5ppt。  
> 建议重点检查 A/B/C 三个客户群以及华南运输采购价格变化。

这才属于 Analysis，而不是 Dashboard。

因此产品定位不宜只是：

> AI Financial Dashboard

而更适合：

- AI Financial Analyst
- Finance Intelligence Platform
- AI 原生财务经营分析工作台

---

# 四、市场方向：BI、Excel Agent、FP&A、AI Data Analyst 正在融合

讨论中参考了几类方向：

## 1. BI → AI Analyst

Power BI 等开始强化：

- Chat with your data
- AI Narrative
- 自然语言问数
- 自动总结
- 语义模型
- 报表与 Narrative 联动

但本质仍偏：

> BI + AI

而不是专门深耕 Finance Domain。

---

## 2. Excel Agent → Data Analyst

Julius / ChatGPT for Excel 等路线说明：

真正重要的不是帮用户写 Excel 公式，而是：

```text
Excel / CSV / DB
→ 自动清洗
→ EDA
→ 统计分析
→ 建模 / Forecasting
→ 图表
→ 报告
```

一个非常重要的架构原则：

> LLM 负责思考。  
> Python / SQL / Calculation Engine 负责算数。

避免：

> 直接把大量数据交给 LLM，让模型“自己算”。

---

## 3. FP&A → Finance Intelligence

类似 Cube / Anaplan 的产品强调：

- Actual vs Budget
- Forecast
- Scenario Planning
- Variance Analysis
- Driver Analysis
- Anomaly Detection
- Financial + Operational Planning
- AI Commentary

因此整个市场正在向交叉点融合：

> BI + FP&A + Spreadsheet + AI Data Analyst

而用户构想正处于这个交叉区域。

---

# 五、初步 6 层架构

第一版架构曾被整理为：

```text
┌──────────────────────────────────────┐
│ ⑥ Experience Layer                   │
│ Dashboard / Chat / Analysis / Report │
├──────────────────────────────────────┤
│ ⑤ Narrative & Publishing Engine      │
│ HTML / PPT / PDF / Management Brief  │
├──────────────────────────────────────┤
│ ④ Finance Analysis Engine            │
│ Variance / Driver / PVM / Forecast   │
│ Anomaly / Scenario / Profitability   │
├──────────────────────────────────────┤
│ ③ Finance Semantic & Metric Layer    │
│ KPI / Formula / Dimension / Hierarchy│
├──────────────────────────────────────┤
│ ② Data Modeling & Processing Layer   │
│ Clean / Map / Join / Aggregate       │
├──────────────────────────────────────┤
│ ① Data Source Layer                  │
│ Excel / CSV / DB / ERP / CRM / HRIS │
└──────────────────────────────────────┘
```

真正难的是第 ③ 和 ④ 层，而不是前端 Chart。

---

# 六、Finance Semantic Layer / Metric Registry

讨论中明确提出：

指标不能只作为“Excel 某个字段”。

例如现实中可能有：

```text
销售收入
主营收入
Revenue
营业收入
GMV
Net Revenue
含税收入
不含税收入
```

系统不能每次靠 LLM 临场判断。

应建立机器可理解的 Metric Registry：

```text
Metric: Revenue

Definition:
净营业收入

Formula:
Gross Revenue
- Discounts
- Returns
- Taxes

Dimensions:
Region
BU
Customer
Product
Channel
Month

Comparison:
YoY
MoM
Budget
Forecast
LY

Drilldown:
Company
 → BU
   → Region
     → Customer
```

指标体系至少要定义四类元素：

## 1. Metric

例如：

- Revenue
- Gross Profit
- EBITDA
- EBIT
- Net Profit
- Cash Flow

## 2. Dimension

例如：

- BU
- Region
- Product
- Customer
- Channel
- Legal Entity
- Cost Center
- Month

## 3. Relationship / Driver Tree

例如：

```text
Revenue
 ├ Volume
 ├ Price
 ├ Mix
 └ FX
```

或：

```text
EBIT
 =
Revenue
- Variable Cost
- Fixed Cost
- SG&A
```

## 4. Business Rule

例如：

```text
Gross Margin < Budget -2ppt
```

触发 Margin Warning。

或：

```text
AR > 90 days
```

触发 Collection Risk。

---

# 七、Analysis Skill Library：真正借鉴 huashu-excel 的方向

用户后来明确提供：

https://github.com/alchaincyf/huashu-excel

研究后形成的判断：

> 最值得借鉴的不是 Excel 能力本身，也不只是几个统计方法，而是它把“专业数据分析师如何工作”编码成了一套可执行的 SOP + Skill。

仓库整体目标可以概括为：

```text
体检
→ 清洗
→ 对齐
→ 分析
→ 对账
→ 交付
→ 验图
→ 质控
```

---

# 八、huashu-excel 的四层价值

## 1. 数据可靠性工程

它强调：

- 原始表结构识别
- 多层表头
- 合并单元格
- 文本数字
- 合计 / 小计
- 重复行
- 异常缺失
- 行数守恒
- 金额守恒
- 原表合计交叉验证
- 独立路径重新计算

一个关键思想：

> 先读原始单元格，再做 DataFrame。

因为直接 `read_excel()` 可能损毁中国式 Excel 原始语义。

特别重要的一点：

> AI 算错不会报错。错误数字和正确数字在交付时看起来一样“像真的”。

因此财务系统必须特别重视：

# Calculation Trust

---

## 2. Analysis SOP

huashu-excel 定义了接近标准作业程序的分析流程：

| Step | 阶段 | 核心问题 |
|---|---|---|
| 1 | 体检 | 数据到底是什么 |
| 2 | 清洗 | 数据能不能算 |
| 3 | 对齐 | 到底要回答什么问题、采用什么口径 |
| 4 | 分析 | 能发现什么、意味着什么 |
| 5 | 对账 | 数字凭什么可信 |
| 6 | 交付 | 怎么让人使用分析 |
| 7 | 验图 | 图有没有表达错误 |
| 8 | 质控 | 即使数字对了，结论有没有错 |

特别强调：

> 脚本只是“眼睛”，不是“大脑”。

每得到一个结果以后，应继续回答：

```text
看到了什么
→ 意味着什么
→ 下一步查什么
```

---

## 3. Multi-role Reasoning

huashu-excel 不把 AI 只定义成单一“数据分析师”，而要求其在不同阶段扮演：

- 领域专家
- 数据分析师
- 战略顾问
- 视觉设计师
- 前端工程师
- 质控人员

其中，领域专家不是负责算数字，而是回答：

> 这个数字到底算好还是坏？

例如：

> 毛利率 17.3%

仅有这个数字意义有限，更重要的是：

- 相对于去年怎么样？
- 相对于预算怎么样？
- 相对于同行怎么样？
- 相对于战略目标怎么样？
- 为什么是 17.3%？
- 不处理会变成多少？

这正是 Finance Domain Intelligence。

---

## 4. Evidence & QA

普通 AI Data Analyst 往往是：

```text
Data
→ Analysis
→ Conclusion
```

huashu-excel 强化为：

```text
Evidence
→ Reconciliation
→ Verification
→ Independent Review
```

并且明确区分：

### 数字正确

```text
明细求和 = 报告数字
```

### 结论正确

要进一步检查：

- 两个数字是否应该比较
- 时间窗口是否一致
- 是否存在 Simpson's paradox
- 是否遗漏关键维度
- 是否把相关性误说成因果
- 口径是否一致

因此财务分析平台必须追求三层信任：

```text
Calculation Trust
↓
Analytical Trust
↓
Decision Trust
```

---

# 九、独立 Reviewer Agent

从 huashu-excel 得到的重要启发：

> 原分析 Agent 不能自己检查自己。

应有独立 Reviewer Agent，从 Source Data 重新计算和验证。

财务场景中例如：

```text
Finance Analyst Agent
        ↓
生成：
Margin下降 -1.8ppt
        ↓
Finance Reviewer Agent
        ↓
重新从 source data 验证
        ↓
检查：
- Margin定义一致？
- Actual/Budget期间一致？
- FX口径一致？
- intercompany是否剔除？
- 一次性损益是否影响？
- product mix和customer mix是否重复解释？
```

只有 Reviewer 通过以后，Insight 才能进入：

- Dashboard
- Management Report
- PPT
- HTML

---

# 十、huashu-excel 与目标产品的本质差异

huashu-excel 更接近：

```text
General Analytics Methodology
```

它解决的是：

> How to analyze data professionally

而用户目标系统还必须解决：

> How to analyze finance professionally

因此完整目标应是：

```text
Finance Intelligence
=
General Analytics Methodology
+
Finance Domain Model
+
Finance Metrics
+
Finance Reasoning
+
Finance Analysis Recipes
```

---

# 十一、Finance Analysis Skills 三层结构

## Layer A — Analytical Foundation Skills

大量借鉴 huashu-excel：

```text
Data Profiling
Data Cleaning
Data Reconciliation
Outlier Detection
Distribution Analysis
Trend Analysis
Segmentation
Correlation
Regression
Forecast
Visualization
Reporting
Independent QA
```

---

## Layer B — Finance Analysis Skills

### Performance Analysis

```text
Financial Performance Review
Actual vs Budget
Actual vs Forecast
YoY
MoM
YTD
Run-rate
```

### Revenue Analysis

```text
Revenue Bridge
Price-Volume-Mix
Customer Growth
Product Growth
Region Growth
FX Impact
New vs Existing Business
```

### Profitability

```text
Gross Margin
Contribution Margin
EBITDA
EBIT
Customer Profitability
Product Profitability
Route Profitability
Contract Profitability
```

### Cost

```text
Fixed / Variable Cost
Cost Driver
Cost Variance
Unit Cost
Procurement Cost
Transportation Cost
Labor Productivity
```

### Working Capital

```text
AR Aging
DSO
AP
DPO
Inventory
DIO
CCC
```

### Cash

```text
Operating Cash Flow
Cash Conversion
FCF
Cash Bridge
Liquidity
```

### Planning

```text
Budget
Forecast
Rolling Forecast
Scenario
Sensitivity
What-if
```

---

## Layer C — Finance Investigation Playbooks

Skill 是：

> 怎么计算。

Playbook 是：

> 什么时候应该调用什么 Skill，按什么路径追查。

例如用户问：

> 为什么利润下降？

应形成调查树：

```text
EBIT ↓
│
├── Revenue?
│   ├── Volume
│   ├── Price
│   ├── Mix
│   └── FX
│
├── Gross Margin?
│   ├── Procurement
│   ├── Labor
│   ├── Freight
│   └── Product Mix
│
├── OPEX?
│   ├── Sales
│   ├── G&A
│   └── R&D
│
└── One-off?
    ├── Impairment
    ├── Restructuring
    └── Accounting Adjustment
```

Agent 的推理循环：

```text
Hypothesis
↓
Call Skill
↓
Evidence
↓
Validate
↓
New Hypothesis
↓
Drill Down
```

这才是真正的：

# AI Financial Analyst Reasoning Loop

---

# 十二、用户问的只是底线：AI 应主动发现没被问的问题

huashu-excel 的一个重要理念被高度认可：

最终应提供三种东西：

1. 用户问的问题
2. 用户应该问但没问的问题
3. 用户不知道自己需要知道的问题

例如 CFO 问：

> 为什么利润下降？

系统可能同时发现：

```text
Revenue ↑
Profit ↓
AR ↑
Cash Flow ↓
```

进一步推断：

> 公司可能为了拉收入，向低质量客户扩张。

这种跨指标联合发现才是 Finance Intelligence 与普通 ChatBI 的差距。

---

# 十三、“先懂数据，再问问题”

另一个重要方法：

不要用户一上传 Excel，就问：

> 你想分析什么？

而应该：

```text
先读数据
↓
先摸底
↓
发现 1–2 个现象
↓
再和用户对齐
↓
确定口径
↓
深入分析
```

因此上传后系统应先形成：

# Data Understanding Brief

示例：

> 我识别到这是 2025–2026 年月度 P&L。  
> 包含 8 个 BU、42 个 Cost Center。  
> Actual 与 Budget 均存在。  
> Revenue 有含税/不含税两个字段，需要确定正式口径。  
> 2026 年 4 月起 Cost Center 结构发生变化。  
> 当前看 EBIT 同比下降约 12%，主要发生在 BU3 和 BU5。  
> 建议本次首先分析利润下降与预算偏差。

用户确认后才正式分析。

---

# 十四、推荐的 Finance Skill Repository 结构

参考 huashu-excel 中：

```text
SKILL.md
references/
scripts/
```

的“Reasoning Knowledge + Deterministic Tools”分离思路。

建议未来 Finance Skill Repository 采用：

```text
finance-analyst/
│
├── SKILL.md
│
├── ontology/
│   ├── pnl.md
│   ├── balance-sheet.md
│   ├── cash-flow.md
│   ├── working-capital.md
│   └── operating-drivers.md
│
├── metrics/
│   ├── revenue.yaml
│   ├── margin.yaml
│   ├── ebitda.yaml
│   ├── dso.yaml
│   └── cash-conversion.yaml
│
├── recipes/
│   ├── variance-analysis.md
│   ├── pvm-analysis.md
│   ├── margin-analysis.md
│   ├── profitability.md
│   ├── working-capital.md
│   ├── forecast.md
│   └── scenario.md
│
├── playbooks/
│   ├── revenue-decline.md
│   ├── margin-decline.md
│   ├── profit-miss.md
│   ├── cash-shortfall.md
│   └── working-capital-risk.md
│
├── scripts/
│   ├── reconcile.py
│   ├── variance.py
│   ├── pvm.py
│   ├── bridge.py
│   ├── forecast.py
│   └── anomaly.py
│
└── qa/
    ├── accounting-checks.md
    ├── semantic-checks.md
    └── reviewer.md
```

---

# 十五、Metric 应机器可读

不应只在 Markdown 写：

> 毛利率 = 毛利 / 收入

而应该定义成：

```yaml
metric: gross_margin
label: Gross Margin

formula:
  numerator: gross_profit
  denominator: net_revenue

unit: percentage

dimensions:
  - business_unit
  - region
  - customer
  - product
  - month

comparison:
  - yoy
  - mom
  - budget
  - forecast

warning_rules:
  - condition: variance_budget < -0.02
    severity: high

analysis_playbook:
  - margin_bridge
  - price_volume_mix
  - customer_mix
  - cost_driver
```

进一步升级为：

```yaml
metric: gross_margin

formula:
  gross_profit / revenue

semantic:
  definition: 毛利/营业收入
  accounting_basis: management

dimensions:
  - company
  - bu
  - region
  - customer
  - product

comparisons:
  - yoy
  - mom
  - budget
  - forecast

thresholds:
  warning: -1ppt
  critical: -2ppt

dependencies:
  - gross_profit
  - revenue

driver_tree:
  - price
  - volume
  - mix
  - freight
  - procurement_cost

recommended_analysis:
  - trend
  - variance
  - margin_bridge
  - mix_analysis

recommended_visual:
  - waterfall
  - heatmap
  - trend

qa_rules:
  - numerator_denominator_period_match
  - consolidation_scope_match
```

关键思想：

> 指标本身就知道自己应该怎么被解释和分析。

---

# 十六、驾驶舱应从 Dashboard 升级为 Finance Cockpit

传统页面只是大量图表。

建议新的 Cockpit 首页更像：

```text
FINANCE COMMAND CENTER

Revenue        Gross Margin        EBIT
¥1.28B         18.4%               ¥92M
+7.2% YoY      -1.8ppt             -13.6%

Cash Flow      Working Capital     Forecast
¥120M          46 Days             FY ¥5.3B
```

下面重点不是再塞图，而是：

# AI Findings

例如：

**01 Margin deterioration**

Gross Margin declined 1.8ppt YoY.

Main drivers:

- Transportation cost ↑
- Customer mix deterioration
- South China region

[Investigate]

---

**02 Collection Risk**

AR >90 days increased ¥36M.

Main exposure:

- Customer A
- Customer B
- Customer C

[Investigate]

---

**03 Forecast Risk**

FY EBIT may miss budget by ¥42–58M.

[Run scenario]

因此管理层真正需要的是：

```text
What happened?
↓
Why?
↓
So what?
↓
What should I do?
```

进一步形成：

```text
Monitor
↓
Detect
↓
Diagnose
↓
Predict
↓
Recommend
```

---

# 十七、Agent 工作流

一个典型问题：

> 为什么这个月利润下降？

建议内部执行：

```text
用户问题
↓
Finance Agent
↓
识别目标指标：
Operating Profit
↓
确定比较基准：
MoM / YoY / Budget
↓
调用 Variance Skill
↓
识别主要贡献项
↓
调用 Driver Analysis
↓
自动 Drill Down
↓
运行 Python / SQL
↓
发现异常
↓
进一步验证
↓
形成结论
```

关键不是 Text-to-SQL，而是：

```text
Question
→ Analysis Plan
→ Calculation
→ Evidence
→ Conclusion
```

---

# 十八、Insight Store：分析只做一次，输出多种形态

讨论中明确提出：

不要 Dashboard、PPT、HTML 各自重新分析一次。

分析应该只发生一次。

例如标准 Insight：

```json
{
  "finding": "Gross margin declined",
  "metric": "Gross Margin",
  "variance": -1.8,
  "drivers": [
    "Transportation cost",
    "Customer mix"
  ],
  "evidence": [],
  "recommendations": []
}
```

同一个 Insight 可以被渲染成：

- Dashboard Insight Card
- HTML 经营分析段落
- PPT 页面
- Chat 回答

因此应有：

# Insight Store

示例：

```text
Finding #0231

Title:
South China margin deterioration

Statement:
Gross margin decreased 2.4ppt YoY.

Evidence:
Transportation cost +1.1ppt
Customer mix +0.8ppt
Other +0.5ppt

Confidence:
High

Source:
P&L 2026-07
Operating data 2026-07

Dimensions:
Region = South China

Recommended Action:
Review supplier contracts...
```

---

# 十九、Report Compiler / Report Recipe

报告不应重新分析，而应消费 Insight Store。

建议架构：

```text
Analysis Results
+
Insight Store
+
Narrative Rules
+
Report Template
↓
Report Compiler
```

典型 Management Review：

```text
Executive Summary
Financial Performance
Revenue Analysis
Margin Analysis
Cost Analysis
Cash Flow
Working Capital
Forecast
Risk
Recommendations
```

输出 renderer：

```text
HTML
PPTX
PDF
DOCX
```

报告本身也可以定义为 Recipe。

例如：

```yaml
report_type: monthly_business_review

sections:
  - executive_summary
  - performance_vs_target
  - top_positive_drivers
  - top_negative_drivers
  - forecast
  - risks
  - actions
  - decisions_required
```

这比“让 AI 自由生成 15 页 PPT”更稳定。

---

# 二十、用户补充的两类驾驶舱资料

用户后续补充了两个主要样板的详细内容。

---

## A. 单机版财务分析工具

特点：

- 面向集团型企业
- 单机版
- Excel / CSV 自动分析
- 中国财务报表格式
- 单文件离线运行
- 无需安装部署
- 数据本地保存
- 月度经营分析
- 财务汇报
- 管理决策

### 十大模块

- 集团总览
- 利润增长
- 盈利能力
- 费用
- 资产负债
- 营运资金
- 现金流
- 财务风险
- 集团合并
- 数据中心

### 联动筛选

- 期间
- 组织口径
- 币种
- 累计 / 当月

---

## 集团总览

示例指标：

- 营业收入 126,895 万元，同比 +12.6%
- 净利润 9,674 万元，同比 +13.1%
- 经营现金流 13,266 万元，同比 +18.7%
- 预算完成率 96.1%

可视化：

- 收入利润现金流趋势
- 经营单元矩阵
- 集团结构
- 风险预警
- 管理层关注事项

---

## 利润增长

核心：

- 毛利率 30.3%，同比 +0.9pp
- EBITDA 19,192 万元
- 净利润预算完成率 92.1%

分析：

- 收入利润毛利率趋势
- 净利润预算差异桥
- 收入结构
- 增长贡献 TOP5
- 管理建议

增长贡献 TOP5：

- 核心产品销售增长 45.2%
- 成长产品放量 26.6%
- 客户拓展 15.6%
- 价格提升 7.9%
- 新产品 3.3%

---

## 盈利能力

核心指标：

- 毛利率 30.3%
- 营业利润率 13.3%
- 净利率 7.6%
- 年化 ROA 5.4%
- 年化 ROE 12.6%
- EBITDA 率 15.1%

杜邦分析：

```text
ROE 12.6%
=
净利率 7.6%
× 总资产周转率 0.71
× 权益乘数 2.33
```

经营单元盈利排名：

- 制造A 10.9%
- 服务D 8.7%
- 制造B 8.2%
- 贸易C 4.5%
- 海外E 3.8%

---

## 费用分析

- 期间费用 18,602 万元
- 期间费用率 14.7%
- 预算超支 932 万元
- 同比 +8.4%

构成：

- 销售费用 7,205
- 管理费用 5,786
- 研发费用 4,353
- 财务费用 1,258

预算执行：

- 销售费用 103.2%
- 管理费用 108.6%
- 研发费用 96.4%
- 财务费用 101.8%

---

## 资产负债

- 总资产 368,025 万元
- 总负债 210,368 万元
- 所有者权益 157,657 万元
- 资产负债率 57.2%
- 有息负债 85,600 万元

资产结构：

- 流动资产 42.5%
- 非流动资产 57.5%

债务期限：

- 1 年内 36.5%
- 1–3 年 34.4%
- 3 年以上 29.1%

---

## 营运资金

- DSO 48.6 天
- DIO 62.3 天
- DPO 39.8 天
- CCC 71.1 天

公式：

```text
CCC
=
DSO 48.6
+ DIO 62.3
- DPO 39.8
=
71.1 天
```

经营单元效率：

- 服务D 52.8
- 制造A 63.2
- 制造B 68.5
- 贸易C 76.4
- 海外E 89.6

---

## 现金流

- OCF 13,266 万元，同比 +18.7%
- ICF -9,674 万元
- FCF（筹资）5,830 万元
- 净现比 1.37
- 期末现金 28,636 万元

13 周预测：

- 最低现金余额 24,800 万元
- 安全线 20,000 万元

---

## 财务风险

- 资产负债率 57.2%
- 流动比率 1.68
- 速动比率 1.24
- 现金比率 0.86
- 利息保障倍数 6.8
- 净负债 / EBITDA 2.97

风险示例：

- 海外E 汇率敞口
- 贸易C 应收账龄
- 集团短债集中度

---

## 集团合并

- 管理汇总收入 139,295 万元
- 内部收入抵销 12,400 万元
- 合并营业收入 126,895 万元
- 收入抵销率 8.9%
- 纳入主体 6 家
- 内部交易匹配率 99.4%
- 未匹配 74 万元
- 抵销分录 12 笔

---

## 数据中心

- 已导入文件 5 个
- 有效数据 3,842 行
- 字段映射率 98.6%
- 校验规则 24 项
- 24 项通过
- 数据错误 0

支持：

- 利润表
- 资产负债表
- 现金流量表
- 所有者权益变动表

校验：

- 资产 = 负债 + 权益
- 现金流勾稽
- 利润表结转
- 内部往来核对

---

# 二十一、B. 总经理经营决策驾驶舱 / 企业经营管理平台

定位：

> 面向集团及多业务单元的企业级经营管理平台。

核心主线：

```text
看结果
→ 找差距
→ 查原因
→ 定措施
→ 验效果
```

整合数据域：

- 财务
- 销售
- 采购
- 生产
- 库存
- 人力
- 项目

底层能力：

- 数据中心
- 指标配置
- 多维下钻

数据导入：

- Excel
- CSV
- JSON

配套：

- 字段映射
- 数据校验
- 批次管理
- 质量监控

指标可配置：

- 指标名称
- 公式
- 口径
- 单位
- 目标值
- 预警阈值
- 版本留痕

多维分析：

- 组织
- 产品
- 客户
- 区域
- 渠道
- 项目

问题闭环：

```text
经营异常
→ 问题
→ 责任人
→ 改善措施
→ 完成期限
```

---

## 核心模块

### 经营总览

- 集团经营全局
- 营收
- 毛利
- 利润
- 现金流
- 等核心指标

### 目标与预测

- 预算
- 实际
- Forecast
- 缺口
- Rolling Forecast
- Scenario
- Gap decomposition

### 收入增长

- 新增订单
- 活跃客户
- 增长来源

### 盈利质量

- 毛利
- 经营利润
- 利润含金量
- 亏损清单

### 成本与费用

- 成本差异
- 费用预算
- 单位成本
- 降本进度

### 现金资金

- 现金流
- 资金分布
- 融资到期
- 现金预测

### 应收回款

- 逾期应收
- DSO
- 客户风险矩阵
- 回款预测

### 库存供应链

- 库存周转
- 呆滞库存
- 缺货风险
- 库龄

### 运营效率

- 产能利用率
- OEE
- 准交率
- 一次合格率

### 风险预警

- 风险热力图
- 重点风险
- 处置进度

---

## 补充能力

- 每个模块底部有“创建改善任务”
- 已启用 42 条预警规则
- 示例当天触发 9 条
- 规则命中率 96.8%
- 数据有更新时间
- 示例为当日 08:30
- 支持实时刷新

---

# 二十二、从驾驶舱资料得到的核心抽象

这些资料并不是简单 Dashboard，而是至少包含 7 类产品能力：

## 1. Finance Data Hub

- Excel / CSV / JSON
- 字段映射
- 数据校验
- 批次
- 数据质量
- 备份
- 多公司
- 多期间
- 币种
- 集团合并

## 2. Finance Metric Engine

```text
Metric
=
Definition
+ Formula
+ Dimension
+ Benchmark
+ Threshold
+ Version
```

## 3. Analysis Theme

不按纯会计报表组织，而按管理主题：

```text
经营总览
目标预测
收入增长
盈利质量
成本费用
现金资金
应收回款
库存供应链
运营效率
风险
```

关键判断：

> Accounting Structure ≠ Analysis Structure

会计报表是 Data Model。

经营分析主题才是 User Experience。

---

# 二十三、从 Analytics 走向 Performance Management

驾驶舱资料中的主线：

```text
看结果
→ 找差距
→ 查原因
→ 定措施
→ 验效果
```

被进一步扩展为：

```text
Monitor
看结果
↓
Detect
找差距 / 找异常
↓
Diagnose
查原因
↓
Decide
定措施
↓
Execute
落实责任
↓
Verify
验效果
```

这意味着产品逐渐从：

> Analytics

进入：

# Performance Management

---

# 二十四、两条产品路线

## 路线 A：AI Finance Analyst

核心：

```text
Data
↓
Analysis
↓
Insight
↓
Report
```

这是 huashu-excel 更接近的方向。

---

## 路线 B：Enterprise Performance Management

核心：

```text
Target
↓
Actual
↓
Variance
↓
Problem
↓
Action
↓
Owner
↓
Deadline
↓
Result
```

驾驶舱资料更接近这个方向。

---

## 用户的机会点：A + B

传统 EPM 擅长：

- Budget
- KPI
- Actual
- Forecast
- Reporting
- Workflow

但往往需要人自己分析。

AI Data Analyst 擅长：

> 分析

但分析完常常结束。

因此更长期的愿景可以定义为：

# AI-native Finance Performance Management

中文：

> AI 原生经营分析与管理平台

核心不是只告诉用户发生了什么，而是：

> 从发现问题一直推动到改善闭环。

---

# 二十五、推荐重新整理为 8 个财务经营分析域

不必机械照抄 10 / 11 个模块。

建议：

## 01 Executive Overview

回答：

> 公司现在到底好不好？

KPI：

- Revenue
- Gross Profit
- EBIT / EBITDA
- Net Profit
- OCF
- Working Capital
- ROIC / ROE
- Forecast Gap

## 02 Growth

回答：

> 增长从哪里来？

- Revenue Growth
- Price
- Volume
- Mix
- New Customer
- Existing Customer
- New Product
- Region
- Channel

## 03 Profitability

回答：

> 增长有没有质量？

- Gross Margin
- Contribution Margin
- EBIT Margin
- EBITDA Margin
- Customer Profitability
- Product Profitability
- BU Profitability
- Loss-making customers/products

## 04 Cost & Productivity

回答：

> 成本为什么变化？

- COGS
- Fixed / Variable
- OPEX
- Unit Cost
- Cost Driver
- Headcount
- Productivity

## 05 Cash & Working Capital

回答：

> 利润有没有变成现金？

- OCF
- FCF
- DSO
- DIO
- DPO
- CCC
- AR Aging
- Cash Conversion

## 06 Balance Sheet & Risk

回答：

> 资产质量和财务风险怎么样？

- Debt
- Liquidity
- Leverage
- Interest Coverage
- Asset Structure
- FX Exposure
- Debt Maturity

## 07 Planning & Forecast

回答：

> 年底会变成什么样？

- Budget
- Forecast
- Rolling Forecast
- Scenario
- Sensitivity
- Gap-to-target

## 08 Actions & Improvement

```text
Problem
↓
Action
↓
Owner
↓
Deadline
↓
Expected Impact
↓
Status
↓
Actual Impact
```

---

# 二十六、自动管理建议不能停留在“AI 文案”

不够好的建议：

> 管理费用超预算 8.6%，建议加强费用控制。

更理想的是：

> 管理费用 YTD 超预算 ¥8.6M，其中 ¥6.1M 来自总部咨询费和外包费用。  
> 进一步拆分发现，其中 ¥4.2M 属于三个一次性项目，因此 recurring run-rate 实际超预算约 ¥1.9M。  
> 如果 Q4 不新增类似一次性项目，全年管理费用预计超预算 ¥2.6–3.1M，而不是当前简单年化后的 ¥7.8M。  
> 建议：  
> 1. 将一次性项目从 recurring cost forecast 中剥离；  
> 2. 重点复核 X/Y 两个 Cost Center；  
> 3. 对 Q4 新增咨询采购设置审批阈值。  
> Estimated EBIT impact: ¥2–3M。

这才是：

# Evidence-based Recommendation

---

# 二十七、Issue 必须成为一等对象

驾驶舱中的“创建改善任务”不能只是 UI 按钮。

系统应真正存在 Issue Object。

例如：

```yaml
issue_id: I-2026-0082

title:
South China gross margin deterioration

metric:
gross_margin

status:
open

severity:
high

detected_at:
2026-08

variance:
-2.4ppt

root_causes:
  - transportation_cost
  - customer_mix

financial_impact:
8.2m

owner:
Finance BP - South China

actions:
  - supplier renegotiation
  - pricing review

target_date:
2026-09-30

expected_impact:
4.5m
```

完整对象链：

```text
Data
↓
Metric
↓
Analysis
↓
Insight
↓
Issue
↓
Action
↓
Outcome
```

---

# 二十八、Management Memory

如果系统能够记录：

```text
发现过什么问题
↓
采取过什么措施
↓
措施实际有没有用
```

例如：

发现：

> Freight Cost ↑

建议：

> renegotiate supplier rates

执行后：

```text
Freight Cost -6.4%
```

未来系统可以逐渐学习：

> 在当前企业、当前业务条件下，哪类 Management Action 有实际效果。

这可以逐步形成：

# Management Memory

这是传统 BI 很弱的能力。

---

# 二十九、Local-first 设计

参考资料强调：

- 无服务器
- 纯本地
- LocalStorage
- 单 HTML
- 数据不出本机

讨论中的判断：

## 对 Demo / MVP

很好。

优点：

- 部署简单
- 数据安全感强
- 不需要后台
- 上传 Excel 即可运行

## 对正式产品

LocalStorage 不够。

更适合：

```text
Browser
│
├ IndexedDB
│
├ DuckDB-WASM
│
└ Local File
```

强调：

> Local-first architecture

而不是：

> LocalStorage architecture

---

# 三十、DuckDB-WASM 路线

MVP 可以尝试：

```text
Excel / CSV
↓
Browser
↓
DuckDB-WASM
↓
SQL Analytics
↓
Charts
↓
AI Analysis
```

小到中等规模数据可以不依赖服务器。

财务数据天然敏感，因此可以形成卖点：

> Your financial data never leaves your machine.

---

# 三十一、AI 与本地安全之间的两种模式

## Local Secure Mode

```text
Data
↓
Local Calculation
↓
Local Model / Rule Engine
```

完全数据不离机。

## Private AI Mode

```text
Data
↓
Local Calculation
↓
仅发送 Aggregated Insights
↓
LLM
```

例如不发送 10 万行客户数据，只发送聚合结果：

```text
Region A:
Revenue -12.6%
Margin -2.1ppt
Top driver: transportation cost
```

兼顾分析能力和隐私。

---

# 三十二、驾驶舱参考资料的局限：分析深度仍然有限

多数页面还是：

```text
KPI
+
同比
+
预算
+
排名
+
趋势
+
一句结论
```

这属于：

# Descriptive + Light Diagnostic

真正系统应该继续向 Deep Diagnostic 发展。

例如：

普通驾驶舱：

> DSO = 62 days ↑ 9 days

目标系统自动：

```text
DSO ↑
↓
Which customers?
↓
Which invoice cohorts?
↓
Sales mix or collection deterioration?
↓
New invoices or old overdue?
↓
Payment terms changed?
↓
Top 10 overdue invoices
↓
Expected cash impact
```

输出：

> 72% 的 DSO 增量来自 4 个客户；  
> 两个客户账期没有改变，因此不是条款问题，而是实际回款延迟；  
> 预计未来 30 天形成约 ¥18M 现金缺口。

---

# 三十三、每个分析页面应标准化为 5 层

例如 Gross Margin 页面：

## Layer 1 — KPI

```text
Gross Margin
18.4%
-1.8ppt YoY
-1.2ppt vs Budget
```

## Layer 2 — Signal

> Margin deterioration detected.

## Layer 3 — Driver

```text
Price        +0.3
Volume        0
Customer Mix -0.6
Product Mix  -0.4
Freight      -0.7
Labor        -0.4
```

## Layer 4 — Drill-down

```text
Region
Customer
Product
Supplier
```

## Layer 5 — Action

```text
3 Issues
5 Actions
Expected EBIT recovery ¥8.3M
```

---

# 三十四、瀑布图不是本体，Driver Model 才是

多份参考资料反复使用瀑布图。

真正该沉淀的是：

# Driver Decomposition

例如 Revenue：

```text
Revenue Change
│
├ Price
├ Volume
├ Mix
├ FX
├ New Customer
├ Lost Customer
└ Product Change
```

EBIT：

```text
EBIT Change
│
├ Revenue Effect
│  ├ Price
│  ├ Volume
│  └ Mix
│
├ Gross Margin Effect
├ Variable Cost
├ Fixed Cost
├ OPEX
└ One-off
```

Cash：

```text
Operating Cash Flow
│
├ EBIT
├ D&A
├ AR
├ Inventory
├ AP
├ Tax
└ Other WC
```

因此系统核心资产之一应该是：

# Driver Tree / Analysis Graph

而不是图表模板库。

---

# 三十五、系统中至少存在 6 种核心对象

讨论后收敛为：

## Metric

例如：

- Gross Margin
- DSO
- Revenue
- EBITDA

## Dimension

- BU
- Region
- Customer
- Product
- Month

## Finding

例如：

> 华南毛利率较预算下降 2.3ppt。

## Driver

例如：

> Freight +1.1ppt / Mix +0.8ppt。

## Issue

例如：

> 华南运输采购成本异常。

## Action

例如：

> 对 Top 3 承运商重新议价。

整体：

```text
Metric
↓
Finding
↓
Driver
↓
Issue
↓
Action
↓
Outcome
```

---

# 三十六、分析深度成熟度模型

为了定义“专业财务分析”，提出 5 层：

| 层级 | 能力 | 例子 |
|---|---|---|
| L1 描述 | What happened | 毛利率 18.4% |
| L2 对比 | Where is the gap | 较预算 -1.8ppt |
| L3 诊断 | Why | 运价、客户结构、产品结构 |
| L4 预测 | What will happen | 年底 EBIT 预计缺口 4200 万 |
| L5 决策 | What should we do | 调价、降本、客户组合调整及财务影响 |

产品是否成立，关键在于：

> 稳定做到 L3，核心场景做到 L4/L5。

---

# 三十七、关于“只支持四张财务报表”的修正

如果产品是：

> Financial Statement Analyzer

只支持四张中国财务报表是合理 MVP。

但如果产品目标是：

> Finance BP / Finance Business Analysis

则不够。

因为只靠财务报表可以做到：

- 收入
- 毛利
- 利润
- 资产
- 负债
- Cash Flow
- DSO / DIO / DPO
- ROA / ROE
- 杜邦
- 偿债分析

但很难回答：

> 为什么？

例如 Revenue ↓ 需要：

- Customer
- Product
- Volume
- Price
- Order
- Region

---

# 三十八、MVP 数据建议：三层 Data Pack

## Data Pack A — Financial

```text
P&L
Balance Sheet
Cash Flow
Budget
```

## Data Pack B — Business Dimensions

```text
Customer
Product
Region
BU
Channel
Project
```

## Data Pack C — Operating Drivers

按行业不同：

```text
Volume
Price
Orders
Headcount
Transportation Cost
Inventory
AR
```

不需要第一版连接 ERP。

Excel 足够。

但必须有：

> 财务数据 + 经营驱动数据

才能真正做出深度诊断。

---

# 三十九、第一目标用户：Finance BP / FP&A

讨论中对用户角色进行收敛：

不建议 MVP 一开始同时面向：

- 总经理
- CFO
- Finance BP

更推荐第一 Hero User：

# Finance BP / FP&A

原因：

他们日常最频繁执行：

- 拉数据
- 做 Excel
- 做 variance
- 找原因
- 写结论
- 做 PPT
- 回答管理层问题

可以定义为：

> 一个每月需要花 2–5 天做经营分析和 Management Review 的 Finance BP。

产品承诺：

> 将 2–5 天的经营分析压缩到数小时甚至更短，并提高分析深度和可信度。

---

# 四十、CEO / CFO 的角色

Finance BP 是：

> Creator

CFO / GM 是：

> Consumer + Decision Maker

典型链路：

```text
Finance BP
↓
分析 / Drill Down / 验证
↓
Insight Store
↓
├ Dashboard → CFO / CEO
└ Report → Monthly Review
```

---

# 四十一、Web 与 PPT 不应二选一

## Web / HTML

定位：

> Working Surface

用于：

- 下钻
- 交互
- Ask AI
- Scenario
- 查看 Evidence

## PPT

定位：

> Communication Surface

用于：

- 月度经营会
- 董事会
- 管理层汇报
- 正式留档

架构：

```text
Analysis Workspace
↓
Insight Store
↙         ↘
Web        PPT
互动分析     正式汇报
```

---

# 四十二、PPT 不应完全“一键自动生成”

更好的工作流：

```text
AI发现 17 个 Findings
↓
自动评估 Materiality
↓
推荐 Top 7
↓
Finance BP:
✓ 纳入
✗ 忽略
★ 强调
↓
自动组成 Storyline
↓
Generate PPT
```

AI 负责：

- 分析
- 初步编辑
- Storyline 草稿

Finance BP 保留：

# Management Judgment

---

# 四十三、推荐的一级工作台信息架构

不是 10–20 个传统菜单。

建议按任务组织：

# FINANCE INTELLIGENCE

## 01 MONITOR

看经营状态

## 02 INVESTIGATE

分析问题

## 03 PLAN

预测 / Scenario

## 04 REPORT

生成管理报告

另有后台：

## DATA & MODEL

- 数据
- 指标
- 规则
- 口径

这种结构比：

> 总览 / 利润 / 费用 / AR / AP / 资产 / 负债……

更 AI Native。

---

# 四十四、Monitor 首页建议

示例：

```text
Revenue        Margin         EBIT        Cash
+8.2%          -1.7ppt        -12%        +4%

────────────────────────────────

TOP FINDINGS

🔴 EBIT forecast misses FY target by ¥42M

🔴 South China margin -2.4ppt

🟡 DSO increased 9 days

🟢 New product revenue +¥63M
```

关键 CTA：

> Investigate

而不是普通“查看详情”。

---

# 四十五、Investigate 核心体验

例如问题：

```text
Why did EBIT decline?
```

Agent 自动生成：

```text
Hypothesis 1
Revenue issue?
→ No

Hypothesis 2
Gross margin?
→ Yes

Gross margin -1.8ppt
↓
Freight         -0.7ppt
Customer Mix    -0.5ppt
Product Mix     -0.4ppt
Labor           -0.2ppt
```

用户继续点：

> 查看 Freight Cost

系统下钻：

```text
South China
↓
Top suppliers
↓
Supplier A +14.6%
Supplier B +9.2%
```

这是产品的 Hero Experience。

---

# 四十六、MVP 不需要 50 个页面

建议第一版可只有 6 个核心页面：

1. Upload & Data Mapping
2. Executive Monitor
3. AI Investigation Workspace
4. Scenario / Forecast
5. Report Builder
6. Metric / Model Configuration

只要跑通：

```text
数据
↓
发现
↓
诊断
↓
预测
↓
建议
↓
报告
```

就足以验证价值。

---

# 四十七、“十大模块”可降级为 Analysis Pack

不必做一级菜单。

例如：

# Profitability Pack

内部包含：

- Gross Margin
- Contribution Margin
- Customer Profitability
- Product Profitability
- Margin Bridge
- PVM
- Loss-making entities

未来继续扩：

- Working Capital Pack
- Revenue Growth Pack
- Cash Pack
- Cost Pack

这样扩展性更好。

---

# 四十八、产品内部代号与愿景

讨论中曾暂定：

# Finance Intelligence OS

核心公式：

> Trusted Data × Finance Knowledge × Analytical Reasoning × AI = Decision Intelligence

只有 AI：

> 容易胡说。

只有 Dashboard：

> 只会看数。

只有 Excel Skill：

> 只会执行分析任务。

只有财务指标：

> 仍是传统 FP&A。

四者结合，才能成为目标产品。

---

# 四十九、8 层系统架构版本

综合 huashu-excel、驾驶舱、Insight / Issue / Action 后，系统升级为：

```text
                FINANCE INTELLIGENCE OS

┌─────────────────────────────────────────┐
│ EXPERIENCE                              │
│ Cockpit │ Analysis │ Chat │ Report      │
├─────────────────────────────────────────┤
│ MANAGEMENT                              │
│ Issue │ Action │ Owner │ Outcome        │
├─────────────────────────────────────────┤
│ INSIGHT                                 │
│ Finding │ Evidence │ Risk │ Opportunity │
├─────────────────────────────────────────┤
│ FINANCE ANALYST                         │
│ Plan │ Hypothesis │ Diagnose │ Explain  │
├─────────────────────────────────────────┤
│ FINANCE SKILLS                          │
│ PVM │ Variance │ Margin │ Cash │ FCST   │
├─────────────────────────────────────────┤
│ FINANCE SEMANTIC MODEL                  │
│ Metrics │ Dimensions │ Driver Trees     │
├─────────────────────────────────────────┤
│ ANALYTICS FOUNDATION                    │
│ huashu-excel methodology                │
│ Clean │ Profile │ Stats │ Verify │ QA   │
├─────────────────────────────────────────┤
│ DATA                                    │
│ Excel │ CSV │ ERP │ CRM │ SCM │ HR     │
└─────────────────────────────────────────┘
```

并有贯穿全链路的：

# Evidence & Verification Layer

---

# 五十、参考文章被补齐后的研究结论

用户随后提供了另一套工具抓取结果。

这 5 篇微信文章被完整抓取，并把图片下载后逐张识读。

形成 6 个 Markdown：

- `00_研究资料总览.md`
- `01_集团财务总监驾驶舱_资料.md`
- `02_生产运营分析报告PPT_资料.md`
- `03_财务总监工作总结PPT_资料.md`
- `04_总经理经营决策驾驶舱_资料.md`
- `05_话数Excel数据分析skill_资料.md`

这些文件当时位于：

```text
/Users/qiming/.zcode/workspace/default/research/
```

用户后来要求直接读取这个目录；当前聊天环境无法直接访问其 Mac 本地路径，因此该任务被建议转到可访问本地目录的 Work/Codex 环境。

---

# 五十一、五份资料共同呈现的设计语法

补充研究总结指出：

## 1. 结论先行

驾驶舱每页底部有：

> 经营结论

PPT 页面标题本身就是判断句，例如：

> OEE 降至 72.6%，80% 的缺口来自可用率和速度损失。

话数 Excel 报告首屏也直接写：

> 表面的营收增长是新品补出来的。

因此产品核心资产不是 Chart，而是：

# 数据 → 判断句

的生成能力。

---

## 2. 归因范式

多份资料使用瀑布图完成因子分解：

- 预算差拆成价格 / 销量 / 结构 / 成本 / 费用
- 收入缺口拆成时间性差异 vs 结构性差异

但进一步讨论已经把这上升为：

> Driver Model / Driver Tree

---

## 3. 异常挂“钱、人、期限”

风险和问题常常包含：

- 事项
- 影响金额
- 责任人
- 截止日
- 状态

部分材料甚至有：

> 措施收益验证

例如：

- 已验证收益
- 待验证收益

这进一步支持 Issue / Action / Outcome 对象化。

---

## 4. 数据可信是前置工程

huashu-excel 强调：

> AI 算错不会报错。

重要方法：

- 原始单元格体检
- 表内合计行作免费校验和
- 独立 Agent 拆台复核

这与财务领域天然的：

- 勾稽关系
- 合计
- 审计
- 管理口径
- 财务口径

高度契合。

---

# 五十二、PPT 参考资料带来的额外启发

## 生产运营分析报告

是一套完整：

```text
问题
→ 归因
→ 因果链
→ P0 止损
→ P1 稳定
→ 30/60/90 天路线图
```

## 财务总监工作总结

结构更接近：

```text
结论
→ 分析
→ 税务 / 内控治理
→ 下期计划
→ 管理层决策事项
```

值得借鉴的写法：

- 收入缺口拆成“可追回 vs 真损失”
- 毛降本与净改善分开
- 敏感性货币化
- 最终收口为“需要管理层拍板的事项”

这说明：

> 报告本身就是一个分析程序，而不只是页面模板。

---

# 五十三、对 MVP 的进一步收敛

第一版不应追求“大型财务系统”。

避免一开始就接：

- SAP
- Oracle
- CRM
- HR
- Procurement
- Bank
- Treasury

否则大量时间会耗在 ETL。

MVP 可以从：

> Excel / CSV

切入。

核心目标：

```text
上传数据
→ 自动理解
→ 数据质量检查
→ 字段 Mapping
→ Finance Model
→ 指标计算
→ 自动发现 Top Findings
→ AI Drill-down
→ Root Cause
→ Management Action
→ 一键加入月度经营报告
```

---

# 五十四、建议的 MVP 核心分析能力

早期曾建议 5 类：

1. Financial Overview
2. Variance Analysis
3. Driver Analysis
4. Anomaly Detection
5. Forecast

后续结合用户资料进一步强调：

- Revenue & Growth
- Profit & Margin
- Cash & Working Capital
- Scenario / Forecast
- AI Investigation

---

# 五十五、建议优先构建的 3 张“大脑地图”

讨论最后收敛为：

## Map 1 — Finance Domain Map

定义：

> 财务经营分析有哪些领域。

例如：

```text
Performance
Growth
Profitability
Cost
Cash
Working Capital
Balance Sheet
Risk
Planning
```

## Map 2 — Metric & Driver Map

定义指标之间的逻辑关系。

例如：

```text
ROE
├ Net Margin
├ Asset Turnover
└ Financial Leverage
```

以及 Revenue / EBIT / Cash Driver Tree。

## Map 3 — Analysis Skill & Playbook Map

定义：

> 碰到什么问题应该怎么分析。

例如：

```text
Profit Miss
↓
Variance
↓
Revenue / Cost
↓
PVM / Cost Driver
↓
Dimension Drill Down
↓
Forecast Impact
↓
Recommendation
```

这三张地图完成之后：

- 驾驶舱
- AI Agent
- PPT
- HTML
- Report Builder

都可以从同一套“财务分析大脑”自然生成。

---

# 五十六、建议的近期下一步

当前讨论中最一致的判断是：

> 不要先写大而全 PRD，也不要先堆 Dashboard 页面。

最值得先做的是：

# Finance Analysis Capability Map v0.1

目标拆分：

- 8–10 个 Finance Domain
- 30–40 个核心指标
- 20 个 MVP Analysis Skills
- 10 个 Investigation Playbooks

每个 Skill 建议定义：

| 字段 | 内容 |
|---|---|
| Finance Domain | 属于哪个财务主题 |
| Business Question | 回答什么管理问题 |
| Metric | 涉及哪些指标 |
| Data Required | 需要什么数据 |
| Method | 用什么分析方法 |
| Driver Tree | 如何拆分原因 |
| Drill-down | 向什么维度继续下钻 |
| Calculation | 由 SQL / Python 如何执行 |
| Evidence | 证据结构 |
| Visualization | 推荐图形 |
| Narrative | 如何生成结论 |
| QA | 如何验证 |
| Action | 可能生成什么经营动作 |

---

# 五十七、可直接用于后续 Codex 开发的产品定义

## 产品愿景

# AI-native Finance Intelligence & Performance Management Platform

中文可理解为：

> AI 原生财务经营分析与绩效管理平台

## MVP 产品

# AI Financial Analysis Workspace

中文：

> AI 财务经营分析工作台

## 第一目标用户

> Finance BP / FP&A

## 第二目标用户

- CFO
- 总经理
- 经营管理层

## 核心用户价值

将 Finance BP 每月需要 2–5 天完成的：

- 拉数据
- 对数据
- 做指标
- 做差异
- 找原因
- 做预测
- 写结论
- 做 PPT

压缩到一个可复用、可验证、可追溯的 AI 分析工作流中。

---

# 五十八、核心产品原则

## Principle 1 — Trusted Data First

没有数据可信，就没有 AI Finance。

## Principle 2 — Calculation ≠ Reasoning

Python / SQL 负责算。

LLM 负责：

- Planning
- Hypothesis
- Diagnosis
- Explanation
- Recommendation

## Principle 3 — Metric is a semantic object

指标不只是公式。

指标要包含：

- 定义
- 口径
- 维度
- Benchmark
- Threshold
- Dependency
- Driver Tree
- Analysis Recipe
- QA

## Principle 4 — Insight is a first-class object

分析结果不能只存在于一段 AI 文本里。

## Principle 5 — Issue / Action / Outcome are first-class objects

要把经营改善闭环正式建模。

## Principle 6 — Evidence-backed narrative

任何管理结论都要有证据链。

## Principle 7 — Independent QA

分析 Agent 和 Reviewer Agent 分离。

## Principle 8 — Analysis once, publish everywhere

同一 Insight 支撑：

- Dashboard
- Chat
- HTML
- PPT
- PDF

## Principle 9 — Task-oriented UX

一级入口优先是：

- Monitor
- Investigate
- Plan
- Report

而不是传统财务菜单堆叠。

## Principle 10 — Local-first, not LocalStorage-only

本地安全是策略，不是技术限制。

---

# 五十九、建议的 MVP 系统页面

## 1. Upload & Data Mapping

能力：

- Excel / CSV
- Schema Detection
- Profile
- Cleaning
- Mapping
- Reconciliation
- Data Understanding Brief

## 2. Executive Monitor

能力：

- 核心 KPI
- Top Findings
- Top Risks
- Forecast Gap
- Investigate CTA

## 3. AI Investigation Workspace

能力：

- Question
- Analysis Plan
- Hypothesis
- Skill Invocation
- Drill-down
- Evidence
- Root Cause
- Confidence
- Reviewer QA

## 4. Scenario / Forecast

能力：

- What-if
- Sensitivity
- Rolling Forecast
- Gap-to-target
- Driver Simulation

## 5. Report Builder

能力：

- AI 推荐 Findings
- Materiality
- 人工筛选
- Storyline
- HTML / PPT

## 6. Metric / Model Configuration

能力：

- Metric Registry
- Formula
- Semantic
- Dimensions
- Threshold
- Version
- Driver Tree
- Analysis Recipe
- QA Rules

---

# 六十、未来可能的数据对象模型

## Metric

```yaml
id: gross_margin
name: Gross Margin
definition: 毛利/营业收入
```

## Finding

```yaml
id: finding_0231
metric: gross_margin
statement: South China gross margin declined 2.4ppt YoY
confidence: high
```

## Driver

```yaml
finding_id: finding_0231
drivers:
  - freight: -1.1ppt
  - customer_mix: -0.8ppt
  - other: -0.5ppt
```

## Issue

```yaml
id: issue_0082
title: South China transportation cost abnormal
severity: high
financial_impact: 8.2m
```

## Action

```yaml
issue_id: issue_0082
action: Renegotiate Top 3 supplier rates
owner: Finance BP / Procurement
deadline: 2026-09-30
expected_impact: 4.5m
```

## Outcome

```yaml
action_id: action_x
actual_impact: 3.9m
status: verified
```

---

# 六十一、可能的后端 / 本地技术架构草案

MVP 可考虑：

```text
Browser
│
├── Excel / CSV Parser
├── DuckDB-WASM
├── IndexedDB
├── Finance Metric Engine
├── Python / SQL-like calculation layer
├── Skill Runtime
├── AI Agent Orchestrator
└── Chart / Report Renderer
```

正式产品可继续扩展：

```text
Local-first
↓
Private Cloud
↓
Enterprise Deployment
```

并加入：

- 多用户
- 权限
- 审计
- 数据血缘
- 企业主数据
- 版本
- 任务协作
- 安全策略

---

# 六十二、当前阶段最值得解决的核心问题

不是：

- Chart 选什么库
- Web 用 React 还是 Vue
- PPT 用哪种模板

而是：

## 1. 财务分析领域到底有哪些 Domain？

## 2. 每个 Domain 有哪些核心 Metric？

## 3. 每个 Metric 的 Driver Tree 是什么？

## 4. 每类异常对应什么 Analysis Skill？

## 5. Skill 如何编排成 Investigation Playbook？

## 6. Insight / Evidence / Issue / Action 如何结构化？

## 7. Reviewer Agent 如何独立复核？

## 8. 如何从同一个 Insight Store 输出 Web / PPT / HTML？

---

# 六十三、当前已知研究资料位置

用户在本机保存了前面所有参考文章资料，目录为：

```text
/Users/qiming/.zcode/workspace/default/research/
```

已知研究文件：

```text
00_研究资料总览.md
01_集团财务总监驾驶舱_资料.md
02_生产运营分析报告PPT_资料.md
03_财务总监工作总结PPT_资料.md
04_总经理经营决策驾驶舱_资料.md
05_话数Excel数据分析skill_资料.md
```

以及各 Markdown 引用的相关图片。

后续如进入 Codex / Work 环境，应优先直接读取这些本地文件并将其作为正式产品研究背景资料。

---

# 六十四、推荐下一阶段工作包

建议后续在 Codex 中按以下顺序推进：

## Workstream A — Domain Design

产出：

- Finance Domain Map
- Metric Map
- Driver Tree Library

## Workstream B — Skill System

产出：

- Analytical Foundation Skills
- Finance Analysis Skills
- Investigation Playbooks
- Reviewer / QA Rules

## Workstream C — Data Model

产出：

- Metric Schema
- Finding Schema
- Evidence Schema
- Issue Schema
- Action Schema
- Outcome Schema

## Workstream D — MVP UX

页面：

- Upload
- Monitor
- Investigate
- Plan
- Report
- Model Config

## Workstream E — Runtime

实现：

- Excel / CSV ingest
- DuckDB / calculation
- Skill execution
- Agent orchestration
- Evidence trace
- Report rendering

---

# 六十五、一句话总结当前项目

> 这不是“上传 Excel → 自动生成 Dashboard”的工具。  
> 它的目标是把资深 Finance BP / FP&A / CFO 的分析方法编码成一个 AI 系统：能够理解财务与经营数据、识别关键异常、选择正确分析方法、逐层定位根因、执行预测和情景分析、形成有证据支持的管理建议，并把同一套 Insight 同时发布到 Web 驾驶舱、Chat 和管理层 PPT / HTML 报告中；进一步把 Insight 转成 Issue、Action 和 Outcome，形成经营改善闭环。

---

# 六十六、后续开发时建议坚持的产品边界

第一阶段不要试图做：

- ERP
- 财务核算系统
- 大而全 EPM
- 通用 BI
- 全行业数据平台

第一阶段重点做：

> “AI-native Financial Analysis Workspace for Finance BP / FP&A”

先证明：

1. 数据能可靠读懂；
2. 指标能统一；
3. AI 能做专业诊断；
4. 结论可追溯；
5. 报告能直接复用；
6. 管理层愿意基于它采取行动。

如果这 6 点成立，再向完整 Finance Intelligence OS 扩展。

---

# 附录 A：当前重点术语表

| 英文 | 中文 / 含义 |
|---|---|
| Finance Intelligence OS | 财务经营智能操作系统 |
| Finance Analysis Engine | 财务分析引擎 |
| Finance Semantic Model | 财务语义模型 |
| Metric Registry | 指标注册中心 |
| Driver Tree | 驱动因素树 |
| Analysis Skill | 分析技能 |
| Investigation Playbook | 调查 / 诊断剧本 |
| Insight Store | 洞察存储 |
| Finding | 分析发现 |
| Evidence | 证据 |
| Issue | 经营问题 |
| Action | 改善动作 |
| Outcome | 实际效果 |
| Management Memory | 管理动作与结果记忆 |
| Report Recipe | 报告结构配方 |
| Finance Cockpit | 财务经营驾驶舱 |
| Data Understanding Brief | 数据理解简报 |
| Calculation Trust | 计算可信 |
| Analytical Trust | 分析可信 |
| Decision Trust | 决策可信 |
| Local-first | 本地优先 |
| Materiality | 重大性 |
| PVM | Price-Volume-Mix |
| DSO | 应收账款周转天数 |
| DIO | 存货周转天数 |
| DPO | 应付账款周转天数 |
| CCC | 现金转换周期 |
| OCF | 经营现金流 |
| FCF | 自由现金流 |
| ROE | 净资产收益率 |
| ROA | 总资产收益率 |
| EBITDA | 息税折旧摊销前利润 |
| EBIT | 息税前利润 |

---

# 附录 B：后续最推荐先做的 10 个 Investigation Playbook

1. Revenue Miss / Revenue Decline
2. Gross Margin Deterioration
3. EBIT / Profit Miss
4. OPEX Over Budget
5. Customer Profitability Deterioration
6. DSO Increase / Collection Risk
7. Working Capital Deterioration
8. Cash Shortfall
9. Forecast Miss
10. Balance Sheet / Liquidity Risk

---

# 附录 C：后续最推荐先做的 20 个 Analysis Skills

1. Data Profiling
2. Data Reconciliation
3. Variance Analysis
4. YoY / MoM / YTD
5. Budget vs Actual
6. Forecast vs Actual
7. Revenue Bridge
8. PVM Analysis
9. Margin Bridge
10. Cost Driver Analysis
11. Customer Profitability
12. Product Profitability
13. AR Aging
14. DSO / DIO / DPO / CCC
15. Cash Bridge
16. Trend Analysis
17. Anomaly Detection
18. Rolling Forecast
19. Scenario Analysis
20. Sensitivity Analysis

---

# 附录 D：当前阶段推荐的核心架构图

```text
                    FINANCE INTELLIGENCE OS

┌─────────────────────────────────────────────────────┐
│ EXPERIENCE                                          │
│ Monitor │ Investigate │ Plan │ Report │ Chat       │
├─────────────────────────────────────────────────────┤
│ MANAGEMENT                                          │
│ Issue │ Action │ Owner │ Deadline │ Outcome         │
├─────────────────────────────────────────────────────┤
│ INSIGHT                                             │
│ Finding │ Driver │ Evidence │ Risk │ Opportunity    │
├─────────────────────────────────────────────────────┤
│ FINANCE ANALYST                                     │
│ Plan │ Hypothesis │ Skill Routing │ Diagnose │ QA  │
├─────────────────────────────────────────────────────┤
│ FINANCE ANALYSIS SKILLS                             │
│ Variance │ PVM │ Margin │ Cost │ Cash │ Forecast   │
├─────────────────────────────────────────────────────┤
│ FINANCE SEMANTIC MODEL                              │
│ Metric │ Dimension │ Formula │ Driver Tree │ Rule  │
├─────────────────────────────────────────────────────┤
│ ANALYTICS FOUNDATION                                │
│ Profile │ Clean │ Map │ Reconcile │ Stats │ Verify │
├─────────────────────────────────────────────────────┤
│ DATA                                                │
│ Excel │ CSV │ ERP │ CRM │ SCM │ HR │ Planning     │
└─────────────────────────────────────────────────────┘

                Evidence & Verification
              ───────────────────────────
                   贯穿全链路
```

---

# 附录 E：给 Codex 的直接启动提示

可直接将下面内容作为后续 Codex 会话的工作说明：

> 我正在设计和开发一个名为 Finance Intelligence OS 的 AI 原生财务经营分析系统。第一阶段目标用户是 Finance BP / FP&A，核心目标不是做一个传统 Dashboard，而是把资深财务分析师的工作方法编码成系统：Excel/CSV 导入 → 数据体检/清洗/对账 → 财务语义模型与指标引擎 → Analysis Skills → Investigation Playbooks → AI 根因分析 → Evidence/QA → Insight Store → Scenario/Forecast → HTML/PPT 报告 → Issue/Action/Outcome 管理闭环。  
> 本地研究资料位于 `/Users/qiming/.zcode/workspace/default/research/`。请首先阅读该目录下全部 Markdown 和关键图片，然后以本归档作为产品上下文。  
> 下一阶段优先完成：Finance Domain Map、Metric & Driver Map、Analysis Skill Map、10 个 Investigation Playbook、数据对象 Schema，以及 MVP 6 个页面的信息架构与技术设计。  
> 产品原则包括：Trusted Data First、Calculation ≠ Reasoning、Metric is a Semantic Object、Insight/Issue/Action are First-class Objects、Independent QA、Analysis Once Publish Everywhere、Task-oriented UX、Local-first。

---

**归档结束**
