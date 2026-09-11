# 09 竞品与产品素材｜INDEX

登记日期：2026-09-11。本目录收录财经分析 / 经营分析 / BI 类产品的调研素材，供 FLOW 的界面布局、图表格式、分析方法、指标公式四个方向借鉴。调研方式为公开网络资料（官网、官方文档、第三方评测），非产品实测；截图为官网营销页快照，功能以官方最新版本为准。原始素材保存在本目录，后续订正以新增文件或文档内更新完成，不删改既有调研结论。

## 产品清单

| 编号 | 产品 | 厂商 | 类型 | 一句话定位 |
|---|---|---|---|---|
| C01 | [Power BI](C01-powerbi.md) | Microsoft | 国际综合 BI | 桌面三栏开发结构 + DAX 计算 + 交叉筛选联动 |
| C02 | [Tableau](C02-tableau.md) | Salesforce | 国际综合 BI | 可视化分析标杆，Story 故事线叙事形态 |
| C03 | [Qlik Sense](C03-qlik-sense.md) | Qlik | 国际综合 BI | 关联引擎 + 绿/白/灰选择状态 + Master Items 指标治理 |
| C04 | [SAP Analytics Cloud](C04-sap-analytics-cloud.md) | SAP | 国际综合 BI | 财务语义最深：科目层级一等公民 + Value Driver Tree + 差异图 |
| C05 | [Looker](C05-looker.md) | Google | 国际综合 BI | LookML 语义层 + AI 回答强制附定义与 SQL 的可验证范式 |
| C06 | [帆软 FineBI](C06-finebi.md) | 帆软 | 国内 BI | 财务模板体系最全：三大报表套用、CFO 驾驶舱、杜邦树、瀑布图 |
| C07 | [Quick BI](C07-quickbi.md) | 阿里云 | 国内 BI | 指标洞察全自动多维归因 + 仪表板一键 AI 解读 |
| C08 | [观远数据](C08-guanduan.md) | 观远 | 国内 BI | 卡片级智能洞察 + 跨仪表板洞察 Agent + 订阅推送 |
| C09 | [永洪 BI](C09-yonghong.md) | 永洪 | 国内 BI | 「数据解释」显式归因范式 + 数据点级洞察入口 |
| C10 | [网易有数](C10-wangyi-youshu.md) | 网易 | 国内 BI | PPT 式多页报告 + 报告级全局筛选 + 知数查数到决策闭环 |
| C11 | [Anaplan](C11-anaplan.md) | Anaplan | FP&A | 假设输入与结果同屏联动的计划建模平台 |
| C12 | [Board](C12-board.md) | Board | FP&A | 因果链差异分析 + 三表一致性校验 + FP&A Agent 主动监控 |
| C13 | [Workday Adaptive Planning](C13-workday-adaptive.md) | Workday | FP&A | 使用者/建模者分离 + 首页任务待办的工作流驾驶舱 |
| C14 | [Pigment](C14-pigment.md) | Pigment | FP&A | 滑块/开关式 What-if 情景引擎，拖动即时重算 |
| C15 | [先胜业财](C15-xiansheng.md) | 先胜 | 国内 FP&A | 与 FLOW 重叠度最高的国内对手：「建模、追问、核验、行动」四步闭环 + 法管同源组织树 |
| C16 | [Metabase](C16-metabase.md) | 开源 (AGPL) | 开源 BI | Question 最小分析单元 + Metabot 答案附可查 SQL |
| C17 | [Apache Superset](C17-superset.md) | 开源 (Apache-2.0) | 开源 BI | Explore 实时预览 + 同环比下沉为图表配置 + 注释层 |
| C18 | [Redash](C18-redash.md) | 开源 (BSD) | 开源 BI | 查询工作台三栏布局 + 查询历史全程留痕 |
| C19 | [DataEase](C19-dataease.md) | 开源 (GPLv3) | 开源 BI | 仪表板与大屏双设计器分离 |
| C20 | [积木报表](C20-jimu-report.md) | 开源 (AGPL) | 开源报表 | 类 Excel 设计器独占中国式复杂报表 + JimuChatBI Text2DSL |

截图位于 `screenshots/`（26 张，文件名 `cNN-产品-描述.png`）；个别产品因官网反爬未取得截图，已在对应文档「截图」节记录待补 URL。

## 四维度借鉴矩阵（方向性索引，细节见单文档第 8 节）

| 维度 | 第一梯队借鉴对象 | 关键机制 |
|---|---|---|
| 界面布局 | Power BI（配置态三栏）、DataEase（双设计器）、Superset（实时预览）、Workday（角色分离） | 配置态/阅读态分离、组件库+画布+属性面板、Draft/Published |
| 图表格式 | 帆软（杜邦树/瀑布/三大报表模板）、SAC（差异图/驱动树）、积木报表（类 Excel 复杂报表） | 财务专用图表型别、中国式报表网格 |
| 分析方法 | Board（因果链+三表校验）、Quick BI/永洪（归因两范式）、Pigment（What-if 滑块）、Superset（同环比配置化） | 量价成本传导链、显式归因表单、情景沙盒 |
| 指标公式 | 帆软（四维指标体系）、SAC（科目层级模型）、Qlik（Master Items 认证口径）、先胜（指标-核算-分析-考核一体化） | 指标元数据（口径+责任组织+考核维度）、科目树折叠 |

## 跨产品共识结论（对 FLOW 最有行动价值的 5 条）

1. **可验证 AI 是行业标配而非加分项**：Looker、Metabase、积木报表的 AI 问数均强制附「指标定义 + 生成 SQL」供核验。FLOW 的指标库天然是语义层，四问分析应输出「用了哪些指标、什么口径、什么过滤」的核验链。
2. **归因交互有三种成熟范式**：Quick BI 全自动多维分解、永洪显式声明候选维度出 TOPN 贡献、Board 量/价/组合/成本传导链。FLOW 四问「为什么」环节应组合采纳：显式圈定归因范围 + 固定拆解框架 + 可视化归因报告。
3. **投屏驾驶舱 ≠ 阅读报告 ≠ 固定报表，三形态应拆分**：DataEase/积木报表双设计器、帆软固定报表 vs 自助分析双轨均验证此拆分。FLOW「驾驶舱 + 报告中心」方向正确，报告中心需补类 Excel 固定报表模板形态。
4. **驾驶舱应挂 AI 解读入口**：Quick BI/观远把「解读这块板/这张卡」做成一级交互（单卡粒度比整板粒度更准），并可订阅推送到企微/钉钉。FLOW 四问分析应挂到驾驶舱卡片与数据点上。
5. **财务报告自动生成已产品化**：网易知数「查数→问数→分析→归因→报告→决策建议」闭环、数百名销售个性化报告案例。FLOW 报告中心应补「报告级全局筛选贯穿 + 一键解读 + 摘要订阅」三件套。

## 与其他知识库目录的关系

- 分析方法与指标公式的**知识理论层**（怎么做财务分析、公式怎么定义）见 [02_research 财经分析知识地图](../02_research/2026-09-11-finance-knowledge-map.md)，文章原文入Obsidian 知识库（Davybase 管线管理）。
- 本目录是**产品证据层**：别人把这些知识做成了什么产品、值得抄什么交互与设计。
