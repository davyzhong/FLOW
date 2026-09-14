---
doc_id: FLOW-COMPETITIVE-CONSULTING
title: 管理咨询方法论框架 · 调研
doc_type: competitive-research
status: current
version: 1.0
created_at: 2026-09-15
updated_at: 2026-09-15
owner: FLOW
related: [./README.md, ./summary-and-positioning.md]
---

# 管理咨询方法论框架

> 调研时点：2026-09-15。覆盖被麦肯锡 / BCG / 长桥等系统化的财务分析方法论，以及他们各自的内部研究范式。

## 一、市场观察

管理咨询公司是 "经营分析框架" 的源头活水。每家咨询都有自己专属的方法论。

- **McKinsey**：BCG Matrix、7S、组织能力曲线、价值链分析
- **BCG**：BCG Matrix（市场份额 × 增长率）、波特五力、Decoding the DNA of Organization
- **Bain**：Net Promoter Score、Results Pyramid、Habitual Excellence
- **Deloitte**：4P / 4C / KPI 树
- **PWC**：客户体验、ESG 财务量化
- **国内咨询**：和君咨询"产业为本、战略为势、创新为源、金融为器"；长江商学院 CKGSB 教授案例

经营分析最相关的几个方法论：

## 二、DuPont Analysis（杜邦分析）

- **起源**：DuPont 公司 1912 年内部效率报告 → 1920s 推广
- **核心**：把 ROE 拆解为三因子（净利率 × 资产周转率 × 权益乘数）或五因子（+ 税后负担率 + 利息负担率）
- **为什么重要**：让"公司间 ROE 比较"从单一数字变成"驱动因子分解"
- **现代使用**：
  - CFA 课程必修
  - McKinsey Valuation (Koller) 核心方法
  - 几乎所有投资 / 信用分析 / 战略咨询都用
- **五个因子解读**：
  - **Tax Burden** (Net Income / EBT)：税务效率
  - **Interest Burden** (EBT / EBIT)：财务杠杆效果
  - **Operating Margin** (EBIT / Revenue)：核心经营能力
  - **Asset Turnover** (Revenue / Avg Assets)：资产利用效率
  - **Equity Multiplier** (Avg Assets / Avg Equity)：杠杆水平
- **对 FLOW 启发**：
  - ① FLOW 已经做了"杜邦三因子 + 五因子 + 二级子项"，是与咨询方法论对齐的差异化
  - ② 杜邦分析的常见延伸：
    - **PIMS** (Profit Impact of Market Strategy) — 用 ROI（= ROE 的近似）做市场策略评估
    - **8 种公司类型**（Cash Cows / Stars / Question Marks / Dogs + 4 衍生）
    - **资源—业务—组织三层分解**
  - ③ FLOW 应该在杜邦之外加 **VAS**（Value Added System）框架 — 把 ROE 进一步分解为"价值创造"

## 三、Valuation（McKinsey 估值方法）

- **核心**：DCF + 经济利润 (Economic Profit) + 估值乘数
- **五步估值法** (Koller et al.)：
  1. 行业分析（市场结构 + 竞争）
  2. 公司战略分析（差异化 + 护城河）
  3. 财务分析（杜邦 + 趋势）
  4. 预测财务（情景 + 假设）
  5. DCF 折现 + 估值乘数对比
- **对 FLOW 启发**：
  - ① 框架的"五步"逻辑可直接套用到 FLOW 的报告结构
  - ② FLOW 目前只到第 3 步（杜邦 + 财务），未来可补第 4 步（预测）+ 第 5 步（估值）
  - ③ DCF 模型需要"行业增长率 / 永续增长率 / WACC / 资本支出预测"，FLOW 当前没有这些数据

## 四、波特五力 / 价值链分析

- **波特五力**：
  - 供应商议价能力
  - 购买者议价能力
  - 新进入者威胁
  - 替代品威胁
  - 同业竞争强度
- **价值链分析**：
  - 主要活动（采购 / 生产 / 物流 / 营销 / 服务）
  - 支持活动（基础设施 / HR / 技术 / 采购）
- **对 FLOW 启发**：
  - ① FLOW 当前没有"五力"或"价值链"分析。可作未来版本：
    - "行业五力分析" 半自动生成（基于公开数据 + LLM）
    - "公司价值链分解" 把经营指标对应到价值链环节
  - ② 这类分析对 B 端用户更有价值（BP / 战略部），不一定适合 C 端

## 五、BCG Matrix / GE-McKinsey Matrix

- **BCG Matrix**（增长 × 份额四象限）：Stars / Cash Cows / Question Marks / Dogs
- **GE-McKinsey Matrix**（行业吸引力 × 业务实力三档）：9 象限
- **PIMS**：Profit Impact of Market Strategy，BCG 的实证基础
- **对 FLOW 启发**：
  - ① BCG Matrix 是"业务组合"分析，FLOW 当前没有"业务"维度（公司 / 业务线 / 业务段）
  - ② 如果 FLOW 客户有多业务公司（如阿里有云 / 电商 / 物流），可以加"业务线杜邦"
  - ③ PIMS 经验法则：「高市场份额 → 高利润率 → 高 ROE」可作行业基准

## 六、Balanced Scorecard（平衡计分卡 — Kaplan & Norton）

- **四维**：财务 + 客户 + 内部流程 + 学习与成长
- **为什么重要**：把财务指标 + 非财务指标放在一起，避免"只看财报"
- **对 FLOW 启发**：
  - ① FLOW 当前是纯财务指标（49 通用 + 15 物流 + 167 科目）。非财务指标（用户数、订单量、市场份额）是空白
  - ② 可作未来"经营快照"的扩展：
    - 财务维度（现有）
    - 客户维度（NPS / 客户留存 / 客单价）
    - 流程维度（订单履行率 / 履约时效）
    - 成长维度（员工人均产出 / 研发投入率）
  - ③ 但这些非财务指标需要公司主动上报——FLOW 是"公开财报分析"，路径不通。需要在内部版支持

## 七、战略地图（Strategy Map）

- 把 BSC 四个维度的"因果关系"画成图：
- 内部流程 → 客户满意度 → 财务回报
- 对应 KPI 体系是「目标 → 指标 → 行动」的层级
- **对 FLOW 启发**：
  - ① 可以做"指标依赖图"——FLOW 当前的 dependency graph 已经有这个雏形
  - ② 但 graph 还停留在「指标计算依赖」，没有「战略因果链」层

## 八、长桥证券 DuPont 教学

- 长桥（Longbridge）的 DuPont 课程是中国市场最系统的中文教学之一
- 三步 / 五步法对照、单公司案例、跨公司对比、行业基准
- 配套资源：Valuation (Koller, McKinsey) / Financial Statement Analysis (Penman) / Higgins / Nissim & Penman 学术论文
- 对 FLOW 启发：
  - ① FLOW 的杜邦拆解方法可对齐长桥教学（事实层 + 因子层 + 二级子项）
  - ② 行业基准（"杜邦 benchmark"）FLOW 当前没有，应作为对比数据源
  - ③ 学术研究（Nissim 2001, Soliman 2008）给的实证结论可作 FLOW 方法背书

## 九、SWOT / PEST / 7S

- **SWOT**：Strengths / Weaknesses / Opportunities / Threats（公司战略分析）
- **PEST**：Political / Economic / Social / Technological（宏观环境）
- **7S**：Strategy / Structure / Systems / Shared values / Skills / Style / Staff（组织诊断）

这些是定性框架，FLOW 当前是定量指标驱动，不太兼容。但可作为：

- 「公司报告」页加一个"SWOT 摘要" tab（用 LLM 从年报文本生成）
- 「行业分析」页加 PEST 模块（标准化行业模板）

## 十、对 FLOW 的核心启发

1. **杜邦是基本盘**：FLOW 已经做得很好（3 + 5 因子 + 二级拆解），需要继续加深：
   - 行业基准（"杜邦 benchmark"）
   - 多业务线（公司 × 业务段）
   - 趋势预测（DCF / 经济利润）
2. **加 VAS / 经济利润**：从"ROE 拆解" 升级到"价值创造拆解"。McKinsey 估值核心是经济利润（EVA），FLOW 可加
3. **平衡计分卡 (BSC)**：从纯财务 → 财务 + 客户 + 流程 + 成长。FLOW v2 路线
4. **战略地图**：依赖图 + 因果链。FLOW 当前的 dependency graph 是数据流，不是战略流
5. **行业基准**最关键：没有 benchmark，杜邦数据是空跑。FLOW 应有"行业杜邦对照表"
6. **情景分析 / 敏感性分析**：FLOW 当前的静态杜邦是"快照"，应加"如果...那么..."动态