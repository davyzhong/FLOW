---
doc_id: FLOW-VER-CFO-VIEW-COMPONENT-DESIGN-20261018
title: CFO 多视图图表组件复用与交互方案
doc_type: verification
status: draft
version: 1.0
created_at: 2026-10-18
updated_at: 2026-10-18
owner: FLOW
commit_refs: [5327c6a3db8f14a26d0e7e4e35e096c43661a014]
evidence_refs: [existing-echarts-builders, module-chart-dispatcher, chartbox-accessibility, cfo-chart-data-availability-v1]
applies_to: cockpit
---

# CFO 多视图图表组件复用与交互方案

## 设计结论

无需引入第二套图表库，也无需逐图自绘。项目已安装并按需加载 ECharts 6.1，低层 builders 已覆盖组合趋势、瀑布、杜邦树、donut、排名、账龄、热力矩阵和四象限；但页面模块的 `buildModuleChartOption` 只分发折线/柱图、瀑布、treemap 和 `ratio_bar` donut，部分成熟构建器没有接入页面契约。

建议按“数据问题 → 图型 → 已有 builder → 可读表格/链接”组织视图；先打通既有 builder 与 API 数据契约，重构同一图表不另造实现。图表统一增加可见图例/期间/单位/事实类别、非 hover 值表、缺数说明和来源/定义链接。交互以显式按钮、表格链接和键盘/触控可达目标为主；画布点击只作快捷入口，不让核心功能依赖 hover 或精准点击。

## 现有图表能力盘点

| 构建器/设施 | 现有用途 | 复用建议 | 当前缺口 |
|---|---|---|---|
| `buildCombo` | 时间变化、柱线双轴和缺失点 | 总览、利润增长、现金流、周转与偿债比率、分部序列 | 对齐期间和系列单位；不把不同事实类别无说明地放在同一序列；当前无直接事件回调 |
| `buildWaterfall` | 有起点/增量/终点的守恒差额 | 经营利润桥、现金变动桥 | 驱动项链接、输入值与总额核对需在画布旁的表格和详情入口提供 |
| `buildDupont` | ROE 因子树 | 保留盈利能力页既有杜邦，不复制 | 每个节点保持字典/快照/财报行链接；缺节点显示 unavailable |
| `buildDonut` | 单期组成占比 | 费用组成；需标明该期及样本来源 | 不能把年度比较数组混成单期组成；结构细分缺失不能补零 |
| `buildAgingBars` | 有序账龄段比例条图 | 大麦演示账龄，先与应收余额/期间对账 | 目前以百分比为主要输入，设计中同时提供绝对余额和逾期率表；必须显式合成演示标签 |
| `buildRankBar` | 横向排名 | 客户/产品/地区收入、毛利或应收排名，限定单一期间及口径 | 点击行下钻；总额/Top N 与“其他”对账；屏幕阅读表格备用 |
| `buildHeatmap` | 分类×期间或分类×指标矩阵 | 数据质量覆盖/异常矩阵；可选经营月度预算达成矩阵 | 当前色标固定 0–100；需按比例/金额语义自适应并把缺失与 0 分开 |
| `buildQuadrant` | 有明确横纵指标与阈值的散点象限 | 仅用于经营单元预算达成率×利润率等可复算合成演示场景 | 不用于臆造财务风险概率/影响矩阵；阈值须来自预算或显式治理配置 |
| `buildModuleChartOption` | API module chart 通用分发 | 扩展成有限、明确、带 schema 校验的 builder registry | 增加 rank/aging/heatmap/quadrant 类型的显式 adapter；不做未知类型静默降级 |
| `ChartBox` / `useEChart` | 按需加载、复用实例、响应式 resize、销毁和空态 | 统一承载所有主题图表 | 当前只给 canvas `role="img"` 和通用 aria 文本，无 click/focus 事件与数据表；必须配 DOM 控件/表格 |

图表基础设施已从 `echarts/charts` 注册 `ScatterChart`、`HeatmapChart` 和 `GraphChart`，故账龄条图、热力和散点不要求新包。是否需要重新设计某个 builder，以本方案后续页面合同和真实字段为准。

## 逐视图方案

| 视图 | 主要分析任务 | 首选视觉表达 | 复用和接线方向 | 必须的兜底和来源路径 |
|---|---|---|---|---|
| CFO 总览 `/cockpit` | 看营收/营业利润/毛利率/OCF、期间变化与待办 | 四项 KPI + `buildCombo` 趋势；变动图链接到利润/现金桥 | 复用总览 API 与趋势 builder；公开模式用 FY 两期点/柱，演示模式可选月度 | KPI 原始数值、变化口径、期间、事实标签一直可见；指标→快照→报表行 |
| 经营总览 `/` | 解释经营利润、产品/客户结构和毛利差异 | `buildWaterfall` 利润桥 + `buildRankBar` 产品/客户排名；毛利矩阵 | 复用已有 `operating_profit_bridge` 与经营分析结果；最终信息架构采用统一入口链接，不复制桥 | 驱动表与 waterfall 对账；行项→经营指标→明细/source record；清楚标记合成分配 |
| 利润增长（现散落于 `/`、`/cockpit`） | 识别增长趋势和驱动 | `buildCombo` 时间序列 + `buildWaterfall` 驱动差异 + `buildRankBar` 增长贡献 | 以同一 Revenue/Operating Profit 数据和桥接 API；是否独立页留给 IA 验收，不另算重复指标 | 月序列只属于演示事实；公开只有年度；贡献表需与桥末值一致 |
| 盈利/杜邦 `/cockpit/profitability` | 解释 ROE 的三个因子与两期变化 | 现有杜邦树 + `buildCombo` 收入/利润/毛利率趋势 | 保留现有 `buildDupont` 和快照计算；利润趋势根据已发布公开事实或单独演示模式供数 | 节点显示公式、输入和来源行；趋势图只绘可比期间 |
| 费用 `/cockpit/expenses` | 看费用结构、期间变化和预算偏差 | `buildDonut` 单期组成 + 年度柱/线比较；演示数据可做预算差异排序/瀑布 | 复用费用模块数据；月度预算需显式选择“演示数据”源；预算差异优先普通偏差条，不强套百分比颜色 | 公开 FY 两期和演示预算分屏；费用项目→科目映射→报表行/预算情景 |
| 资产负债 `/cockpit/balance-sheet` | 看时点构成、杠杆与余额变化 | 两期并排/100% 堆叠条 + `buildCombo` 杠杆变化 | 将 2 桶时点值的 treemap 改为比例/并列柱；仅在真正的层级细项可用时保留 treemap | 显示资产负债表时点；组成百分比合计校验；余额→标准科目→报表行 |
| 营运资金 `/cockpit/working-capital` | 看周转和资金占用，追到账龄/客户 | `buildCombo` 周转/余额趋势 + `buildAgingBars` 应收分桶 + `buildRankBar` 客户逾期/余额 | 利用 4,800 条合成应收记录；接入前核对期间账龄余额与财报应收是否同范围，不一致则只独立展示演示样本 | DSO/DIO/DPO/CCC 公式表；账龄图显示合成批次、时点、余额；客户→发票→source record |
| 现金流 `/cockpit/cashflow` | 解释期初至期末现金和现金/利润关系 | `buildWaterfall` 现金桥 + `buildCombo` OCF/净利润对照 | 复用已披露现金流量表行；不把只含月收入的预测侧车接入现金桥 | 起点+流量+汇兑=终点；收现比、13周预测保持明确缺失 |
| 风险 `/cockpit/risk` | 观察偿债/流动性比率变化和控制线状态 | `buildCombo` 比率趋势 + 明确字段的阈值表 | 只显示已有比率和治理阈值；`buildQuadrant` 不代表风险概率矩阵 | 未配置阈值显示“未配置”，不渲染“正常”；比率→输入公式→报表行 |
| 合并 `/cockpit/consolidation` | 观察被单独披露的菜鸟分部收入 | `buildCombo` 年度收入与同比柱/线 | 复用 `CN-SEG-*` 年度事实；实体间合并/抵销作为缺失块，不构造瀑布 | FY2026 边界断点可见；period→fact ID→年报来源 |
| 数据工作台 `/data` | 校验导入数据是否可用于分析 | 批次质量卡 + `buildHeatmap` 字段/期间覆盖或异常类别矩阵 + 异常分布条 | 聚合已有画像、映射、校验和发布状态；API 需提供字段计数、值域/重复/勾稽等汇总 | 表格呈现分母、缺失与 0 的区别；异常→批次→原始行；不将 UI 计数解释成财务绩效 |
| 分析 `/analysis` | 以证据回答四问并呈现 Findings | 有计算支持的证据迷你趋势/瀑布；其余用关键值表和证据引用 | 嵌入现有指标快照/分析运行数据；不复制驾驶舱全量趋势 | finding→run→metric snapshot→定义→源行；结论与客观证据分开 |
| 报告 `/reports` | 阅读和导出带来源的经营报告 | 报告叙事块内嵌主题图、关键表和来源脚注 | 复用已有报告 payload 的指标/图表类型；屏幕与导出使用同一数据合同 | 冻结快照重算一致；打印版不丢单位、来源、事实标签和缺失说明 |
| 指标库 `/metric-library` | 查指标定义、公式及适用条件 | 可搜索表格 + 展开公式输入/依赖列表；不添加趋势图 | 复用指标字典与现有 focus/entry 深链；若无正式指标 DAG，不造关系图数据 | 定义版本、单位、分子分母、不可用原因；来源链接回原图/页面 |

## 跨视图交互合同

### 事实视图隔离

页面状态应允许选择“公开披露”或“大麦演示”，而不是在同一条折线中静默拼接。状态进入 URL（建议 `fact_view=disclosed|demo`，最终以现有筛选合同核对）；标题/单位行显示当前类别、期间和数据截止点。某些页面只有一种模式时直接固定该类别并解释，不显示无效切换控件。派生指标标明公式/版本；情景或预算必须显示情景编号。

### 图形、表格和跳转

每张图至少同时提供：

1. 一句分析问题型标题（不是“趋势图”）及可见结论/解释范围；
2. 图例、期间、单位、来源/事实类别和缺数理由；
3. 同值的 DOM 数据表（可聚焦、屏幕阅读器可访问、窄屏可滚动）；
4. 明确的“看指标定义 / 看来源明细 / 打开分析运行”链接；
5. 图表点点击时将期间/维度带入目标页 URL，返回时恢复原视图。

画布为 `role="img"` 时不承诺它本身具备键盘遍历；DOM 表、筛选器和链接必须提供等价操作。移动端不依赖 hover，不缩成不可读的整页并列图例。

### 视觉和移动适配

- 仅用现有 `CHART_THEME` 语义颜色：常态中性色、主线蓝、比较绿/金、警示橙、负向红、缺失灰；颜色同时有文字/形状/图例表达，不用颜色独立传达状态。
- 单位和值格式通过既有 `formatFinancialValue`，金额两位、计数整数、比例/天数按指标字典。ECharts tooltip 与 DOM 表用同一 formatter。
- 窄屏将并排小 multiples 纵向排序，表格提供横向滚动和固定首列；核心 KPI/数值不能隐藏在 hover 中。
- 客观事实密度优先于装饰图像；报告类图片只在来源允许且用于报告识别时展示，不用于填充缺数。

## 组件复用决策与实现边界

| 能力 | 选型 | 不采用的原因 |
|---|---|---|
| 图表渲染/交互 | 复用现有 ECharts 6.1 与按需 `echarts/core` 注册 | 已覆盖目标图型、有现有测试与配色，无需再引入第二个渲染器 |
| 数据适配 | 扩展现有 `CockpitModuleChart` / `buildModuleChartOption`，将缺失 builder 接入显式 type adapter；复杂跨域需要新载荷时先改 API 合同 | 不在每个 React 页面手写 option，不在页面内重复计算指标 |
| 图表值表与深链 | 扩展现有 `module-page.tsx` / `ChartBox`，使用普通 HTML table、链接和 URL query 状态 | ECharts canvas 不为键盘可访问表格和业务授权负责，另引入 table/widget 库不能解决来源契约 |
| 数据过滤 | 延续现有 API `ActiveFilters` 与 URL query 参数；引入公开/演示事实类别作为显式字段 | 不新增前端临时状态事实源，不混淆筛选状态与财务事实 |
| 异步状态 | 复用现有 API 缺数状态、载荷 `unavailable` 和页面空态 | 不再造一套 loading/error 状态系统 |

不新增 npm/Python 依赖、不改数据库 schema、不改 CI。图表点 drilldown 与服务端新聚合如需超出现有 API 合同，须在进入实现时优先复用既有数据查询和来源权限，记录精确字段后再改。本报告是 4.3 设计出口，不会自动授权非计划中的迁移或来源事实改写。

## 4.4 实施候选顺序

按用户的客观事实优先原则，后续实现建议从风险最低、已有真实/演示数据可复核项开始：

1. **图形表达修正**：资产负债结构图语义；现有组合趋势/瀑布/杜邦对照值表、标题、单位和缺数标签。
2. **已有合成业务数据利用**：质量/来源标识明确后接预算差异、产品/客户排名和 24 月经营趋势；先解决订单计数分摊小数语义，不能把 fractional contribution 标为订单数。
3. **账龄接入**：只作为大麦合成数据模块；先验证 5 档汇总与应收期末数的关系、账龄快照日期和逾期规则，再画 aging bar 并链接发票明细。
4. **交互/追溯**：图旁数据表与指标/来源 link 先形成完整路径；随后事件点击、URL 状态、键盘/触屏和返回定位。
5. **保留缺口态**：没有风险概率/影响、现金周预测要素、实体间交易抵销的页面继续显示受限原因与字段清单。

不得把“已实现建构器”当作“已接入数据/已验证图表”的证据；4.4 的截图/浏览器工作流遵循项目当前暂停决定，除非用户后续恢复。

## 验收基线

- ECharts 仍只有一个渲染基础层；无新依赖。
- 每个已选图型能列明问题、API 字段、单位、期间、事实类别、组件和缺失态。
- `CockpitModuleChart` 只接受有限图型；未知图型显示可解释 unsupported 状态，不默认为空白。
- 每张图有同值数据表和 DOM 链接；不依靠 hover 才看到核心数值。
- 公共披露年度图和 synthetic 月度图由显式模式状态隔离；账龄/预算标签不能遗漏。
- 拟开发缺口须与 4.2 数据盘点相符；不新增风险矩阵、现金预测、集团抵销事实。

## 证据入口

- 4.2：[CFO 各视图图表需求与数据可用性盘点](2026-10-18--cfo-chart-and-data-availability-v1.md)
- 模块分发器：`apps/web/components/cockpit/charts/module-options.ts`
- builders：`apps/web/components/cockpit/charts/builders.ts`
- ECharts 与容器：`apps/web/components/cockpit/charts/echarts-base.tsx`
- 页面适配：`apps/web/components/cockpit/module-page.tsx`
- 图表 API 合同：`apps/web/lib/api/client.ts` 中 `CockpitModuleChart`
- 视觉/交互设计规格：`docs/superpowers/specs/2026-10-18-single-machine-visual-prototype-design.md` §3
