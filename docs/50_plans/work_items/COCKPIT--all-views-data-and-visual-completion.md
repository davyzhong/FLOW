---
doc_id: FLOW-WI-COCKPIT-ALL-VIEWS-20261017-001
title: CFO 驾驶舱全视图数据与图表完整性改造
doc_type: work-item
status: active
version: "1.1"
created_at: 2026-10-17
updated_at: 2026-10-17
owner: FLOW
depends_on: [FLOW-WI-COCKPIT-CFO-001, FLOW-WI-DAMAI-FULL-YEAR-001]
acceptance_refs: [FLOW-VERIFY-PROJECT-PROGRESS-20261017-001, FLOW-VERIFY-COCKPIT-CHART-COVERAGE-20261016-001]
applies_to: cockpit
decision_refs: [D001, D040, D047, D052, D053]
supersedes: []
superseded_by: null
related_plan: null
confidentiality: project-internal
---

# CFO 驾驶舱全视图数据与图表完整性改造

> **执行状态：实施中。** 用户于 2026-10-17 明确要求立即执行，本工作包已调整为当前唯一队首；知识刷新 K2 顺延至本工作包完成后。内部阶段按下文顺序串行推进，不形成独立子队列。用户已要求为所有 CFO 驾驶舱视图补足可见经营数据与真实图形图表。本轮只建立计划，不修改产品代码或模拟数据。

**目标：** 让 CFO 驾驶舱每个主要页面一打开就能看到关键财务指标、可读图表、数据口径与来源；在公开披露不足时，允许使用明确标记、可重复且与公开事实勾稽的演示生成明细来验证更细粒度视图，不把生成数据说成菜鸟实际披露。

**实现方式：** 先定位用户当前页面与代码、接口、快照、种子的真实版本，查明缺失发生在哪一层；再把已登记的公开财务事实与发行包中现有的期间、财务/经营明细、预算、预测、组织和行动项数据按“披露事实 / 可复算派生 / 演示生成 / 情景目标”分层接入。用单次聚合 API 为每个页面供数，复用现有 ECharts 构建器和组件，补齐响应式图表、明细表、来源深链和行动项，最后用隔离账套逐路由验收。

**技术栈：** 当前 FastAPI 聚合接口、Next.js 页面、ECharts 6.1.0、现有 FLOW 指标字典/快照/权限与大麦物流 v2 发行包。默认不新增图表依赖、不另建指标事实源、不改数据库 schema。

## 问题基线

用户当前指出：CFO 总览缺少营业收入、营业利润、毛利率、经营现金流等核心数据；行动项列表为空；多个视图只有数字和文字，没有清晰、丰富的图形。前次验收截图也确有总览四张趋势图为空态、现金流变动桥为空态的情况。此前 51 图覆盖映射不能作为全图形已完成的证据。

仓库已经包含可优先复用的数据资产：菜鸟申请稿 FY2022/FY2023 三表、325 条来源事实登记、FY2019–FY2025 分部序列，以及大麦 v2 canonical 包中的 24 个期间、768 条财务实际、1,920 条经营实际、10,752 条预算、4,800 条应收记录和滚动预测侧车。现有数据包声明为 synthetic；这些行的数值用途、披露锚点、对账关系及与当前 Dashboard/Objective 快照的连接方式仍须在第一阶段逐项核验，不能只因文件存在便假设页面已能读取。

## 统一数据规则

1. **披露事实**：菜鸟/阿里原始披露值保留原始期间、原始单位、页表行定位、文件 SHA 与来源事实 ID。页面标注“公开披露”。
2. **可复算派生**：只由登记事实按指标字典公式计算，保存输入事实、公式/定义版本、期间和舍入规则；页面标注“计算指标”，可回溯分子、分母及来源行。
3. **演示生成明细**：公开资料没有月、组织、客户、产品等细度时，可从既有确定性 generator 生成场景明细；须标注“演示生成数据”，提供生成规则版本和随机种子/确定性身份，并对账到披露期间总额。不得描述为菜鸟逐月/逐笔实际数据。
4. **情景预算/预测**：可用现有预算和 forecast sidecar 验证目标/预测交互，但始终标注“演示情景”，与实际分离；不能混入披露事实或用来声称公开企业实际预算。
5. **行动项**：公开事实或数据差异可触发客观提示；责任人、截止日、处理状态若由模拟组织产生，须标注“演示行动项”。通过已批准 ActionItem 权限/审计路径读写，不绕过 RBAC，不伪造真实责任人。
6. 所有页面同一时间只呈现一种明确选择的数据口径；跨事实类型比较时用清晰标识和图例。无足够事实的指标显示具体缺口与所需输入，不以 0 或空白图冒充完整。

## 全部视图的目标内容

目标是让所有 CFO 驾驶舱视图都不再只是 KPI 卡和说明文字。每页至少有 **2 个真正渲染数据的视觉分析区**；总览和主要分析页目标为 3–4 个。单个视觉区可包含图表与支持明细表。这里的数量是页面完成度下限，不是重复堆放图形的理由；选择图形应回答不同的分析问题。

| 视图 | 必须常显的关键数据 | 目标图形与交互 | 数据/口径边界 |
|---|---|---|---|
| CFO 总览 `/cockpit` | 营业收入、营业利润、毛利率、经营现金流；同时展示净利润、期间、数据来源状态；行动项数量/优先级 | ①收入、毛利/营业利润趋势小多图（金额与比例分轴）；②经营现金流与净利润/现金转换比较；③利润差异/结构桥（具备构成时）；④风险及行动项优先级清单。点击 KPI 进入对应模块，点击行动项进入闭环详情 | 披露事实与生成的月度演示序列清楚分开；不能将两个财年点伪装成月度连续趋势。总览首屏必须显示四个指定 CFO 指标。 |
| 利润增长 `/cockpit` 当前入口，评估独立路由 | 营收、毛利、营业利润、净利润及增长比较 | 收入/利润时间序列、分部或产品贡献条形/矩阵、收入或利润变动瀑布图；维度筛选联动 | 产品/客户/月度分配仅在明确标记的演示层提供；所有合计与公开事实勾稽。独立页面是否拆路由在第一阶段核验后按现有 IA 决定，不新增重复事实源。 |
| 盈利能力 `/cockpit/profitability` | 毛利率、营业利润率、净利率、ROE 与三因子 | 毛利/营业利润/净利率时间序列；杜邦关系图；期间/分部利润率比较；点选因子查看公式与源行 | 杜邦值来自已冻结 Objective 快照；模拟月度分配需明确标签。缺平均余额时 ROE/因子显示 unavailable。 |
| 费用 `/cockpit/expenses` | 销售、管理、研发、财务费用、期间费用合计和费用率 | 月度分类堆叠柱图；各费用率趋势；预算与实际差异条形/瀑布图；点击费用项进入财报行或演示明细 | 披露科目与生成部门/月份明细标记不同；不凭空拆分利息、折旧或责任部门。 |
| 资产负债 `/cockpit/balance-sheet` | 总资产、总负债、权益、现金、应收、存货、资产负债率 | 资产/负债/权益结构图；资产结构 treemap 或堆叠条；杠杆与流动性趋势；点选结构块下钻科目 | 真实报告期和演示生成期间不得混画；币种、单位、报告期/时点口径显著显示。 |
| 营运资金 `/cockpit/working-capital` | 应收、存货、应付、DSO/DIO/DPO/CCC | 应收/存货/应付趋势；DSO/DIO/DPO/CCC 对照图；应收账龄或客户集中度条形图；点击桶/客户查看演示明细 | 账龄、客户明细来自 synthetic 数据时标示并与总余额对账；没有披露支持时不称为菜鸟真实账龄。 |
| 现金流 `/cockpit/cashflow` | 经营、投资、筹资活动现金流、期末现金、净现比 | 三类净额正负柱图；期初到期末现金瀑布桥；13 周现金预测/安全线图（演示情景）；点击条形回到现金流报表行 | 公开披露历史与未来演示预测采用不同图例；瀑布桥各项必须能与现金变动勾稽，不齐时不可显示为完整。 |
| 财务风险 `/cockpit/risk` | 流动/速动/现金比率、负债率、权益乘数及警示 | 偿债能力期间曲线；债务/资产结构图；阈值区间或风险矩阵；风险项按影响及来源排序 | 公开数据不能拆出的短债/利息保障/期限结构标 unavailable；演示阈值注明设定者与情景。 |
| 集团合并 `/cockpit/consolidation` | 各公开业务分部收入及可比期间 | 分部收入折线和组成堆叠图；分部收入/利润比较；合并抵销前后桥（仅限具备合成主体数据时） | 对外披露分部与模拟组织账套不同层次；页面标题/图例需防止误读为真实法人合并。 |
| 数据中心 `/data` | 财务/经营/预算/预测数据覆盖、来源批次和校验结果 | 期间×数据域覆盖热力图；来源与导入批次关系/质量概览；点击格子筛选缺项与校验失败 | 数据血缘与覆盖率按真实 manifest/校验结果生成；不得用静态百分比或假质量分。 |

## 实施阶段与验收

### 阶段 1：复现当前页面并找出缺数断点

**主要文件：** `HANDOFF.md`、`docs/50_plans/CURRENT_ROADMAP.md`、`apps/web/e2e/damai-demo.spec.ts`、`services/api/src/flow_api/cockpit/service.py`、`services/api/src/flow_api/cockpit/modules.py`、`services/api/src/flow_api/api/routes/cockpit.py`、`services/api/src/flow_api/api/schemas/cockpit.py`、`apps/web/components/cockpit/`。

- [ ] 固定当前实际运行 UI 的仓库目录、分支、代码 SHA、前后端 origin、数据批次/manifest、查询过滤器和浏览器页面；复现用户所见缺失，不以其他 worktree 截图替代。
- [ ] 沿“原始财报→source facts→canonical→seed/import→Objective/MetricSnapshot→API 聚合→页面”逐项追踪收入、营业利润、毛利率、经营现金流，记录各层行数/值/状态，明确缺失是数据未生成、快照未冻结、字段未投影、期间筛选错位、请求失败还是页面未渲染。
- [ ] 检查总览行动项表空的原因：ActionItem 是否未播种、过滤条件/权限隐藏、API 返回空或组件空态不明显；确定使用既有安全写入和审计机制的方案。
- [ ] 对 9 个视图逐项标记现有 KPI、图表槽、真实绘图、真实数据、缺失状态和跳转目标；把“有组件/有映射”与“页面有数据图”分开。
- [ ] 校验现有 24 期间 canonical 资产、月度实际/预算/forecast 的生成规则及与 FY2022/FY2023 披露总额的勾稽。对未通过对账的字段先修复发行源，不在 UI 补数据。

**阶段验收：** 输出单一数据—指标—图表—视图矩阵；4 项 CFO 核心指标均能指向权威数据/派生链或明确故障点；记录复现步骤、隔离数据批次和 SHA；未查清缺口前不开始视觉重排。

### 阶段 2：补实演示账套数据并让财务总览可用

**主要文件：** `config/damai/source_facts_v1.yaml`、`fixtures/damai/canonical/`（只由 generator 生成）、`fixtures/damai/manifest.json`、`services/api/src/flow_api/fixtures/damai/canonical.py`、`services/api/src/flow_api/fixtures/damai/generator.py`、`scripts/build_damai_demo.py`、`scripts/seed_damai_demo.py`、`scripts/verify_damai_demo.py`、`services/api/src/flow_api/cockpit/service.py`。

- [ ] 在既有确定性生成器上核对并补足财务明细映射，使收入、毛利、营业利润、净利润、经营现金流和现金余额都有可查询的期间/组织粒度；已有行可用则不重复生成。
- [ ] 以来源财报报告期汇总作硬约束，对生成的月度/维度明细做收入、利润、资产负债、现金流总额及平衡关系验证。逐字段保存 `reported` / `derived` / `synthetic_allocation` / `scenario` 分类、来源 ID、规则版本、粒度和 manifest 哈希。
- [ ] 检查指标字典映射与快照冻结顺序，使四项 CFO KPI 在默认总览范围内可读且标题、金额单位、变化对比正确；实际与预算/目标不得共用一个数值字段。
- [ ] 使用现有 ActionItem 领域模型、企业范围和授权接口播种少量可复现演示行动项；仅基于已登记 mock finding/场景，带 synthetic 标识、负责人、期限、状态和关联指标/分析运行；不能为没有事实的问题写因果断言。
- [ ] 保证重新初始化业务数据可复现，重复 seed 不重复增加快照、行或行动项；单企业隔离和原始来源保护继续成立。

**阶段验收：** 隔离 seed 与发行包核验通过；四项 KPI 非空、与财报/账本勾稽；总览至少有行动项或清楚的“本期无待办”解释（测试账套应有演示项）；测试数据批次、来源和合成标记全链可查。

### 阶段 3：统一聚合接口及可复用图表内容契约

**主要文件：** `services/api/src/flow_api/cockpit/service.py`、`services/api/src/flow_api/cockpit/modules.py`、`services/api/src/flow_api/api/routes/cockpit.py`、`services/api/src/flow_api/api/schemas/cockpit.py`、`apps/web/components/cockpit/cockpit-types.ts`、`apps/web/components/cockpit/charts/module-options.ts`。

- [ ] 定义每类视觉的 typed payload：分析问题、图形类型、期间/维度、系列和单位、source/metric/snapshot IDs、事实分类、空值原因、可点击目标、图旁数据表。
- [ ] 每页通过一个已有或扩展后的聚合接口返回首屏所需指标、图表、行动项与来源引用；避免一图一请求和 N+1；保持权限依赖、单企业范围、导入批次边界。
- [ ] 在 API/fixture 定向测试中校验四项 CFO 指标、每种 chart payload、期间覆盖、合计勾稽、空态 reason、来源 ID 和权限拒绝。

**阶段验收：** 所有用于视图的数据可从 API 契约独立验证；指标卡、图、表数值一致；任何图表 payload 缺单位、期间、来源分类或 snapshot/batch 身份时，契约测试失败。

### 阶段 4：逐页补充图形、图例、数据表与联动

**主要文件：** `apps/web/components/cockpit/cockpit-overview-app.tsx`、`apps/web/components/cockpit/module-page.tsx`、`apps/web/components/cockpit/profitability-page.tsx`、`apps/web/components/cockpit/action-panel.tsx`、`apps/web/components/cockpit/charts/builders.ts`、`apps/web/components/cockpit/charts/echarts-base.tsx`、`apps/web/components/cockpit/charts/module-options.ts`、`apps/web/components/cockpit/cockpit.css`、`apps/web/components/dashboard/workflow-nav.tsx`。

- [ ] 按上表顺序完成总览，再依次完成盈利能力、利润增长、费用、资产负债、营运资金、现金流、风险、合并和数据中心；新路由必须包 `<AppShell>`、登记导航与导航 E2E。
- [ ] 每页实现至少 2 个有数据、有单位、有期间、有标题结论的图形分析区；总览至少 3 个。收入/营业利润和率类指标分面或使用有明确标注的兼容坐标轴；趋势图必须有足够连续点，只有两期时标“年度对比”。
- [ ] 图表本身必须在验收数据下有可见绘图元素；不能用空白 ChartBox、只渲染标题、只有图表数据表或“暂无数据”块满足本验收。
- [ ] 为每张图提供同步数据表、易读 tooltip、来源/合成标签、口径/单位、键盘可达焦点和屏幕阅读器描述；点选 bar/line/segment/KPI 可进入明细、定义或 source row。
- [ ] 全局期间、组织、区域、产品、客户筛选以 URL 状态驱动相关视图；各页数据域不支持的筛选要禁用或说明，不静默失效。桌面、窄屏和键盘操作均验收。

**阶段验收：** 所有 9 个视图实际页面截图都能看到非空数据图；图表值与其下数据表、接口响应逐点相符；数据分类 badge 和跳转链正常；截图中没有无原因的空白图表区域。

### 阶段 5：全视图浏览器验收、截图和独立复核

**主要文件：** `apps/web/e2e/damai-demo.spec.ts`、`apps/web/e2e/navigation.spec.ts`、`apps/web/e2e/dashboard-visual.spec.ts`、`services/api/tests/cockpit/`、`services/api/tests/api/test_cockpit_modules.py`、`services/api/tests/api/test_cockpit_action_items.py`、`docs/60_delivery/verification/`、`HANDOFF.md`。

- [ ] 在一次性隔离 Compose 栈加载全量发行包，逐个打开 8 个 cockpit 路由和 `/data`，跑全局筛选、图表点击下钻、行动项操作、来源行追溯与导航返回旅程。
- [ ] 采集每个页面的长截图和首屏截图，至少覆盖桌面及窄屏；另外记录各图表可视标记数、可用数据点数、数据分类及图表—数据表核对结果。
- [ ] 验收加载、错误、空、无权限、部分缺数等态。完整演示批次保证必要图有可绘数据；单个真实披露数据缺失时不显示假线，并有明确原因与演示模式切换方式。
- [ ] 用全新上下文独立核对计划验收条款与 diff；只修复影响正确性或验收的缺口，不扩大范围。
- [ ] 更新本工作包、唯一路线图、HANDOFF 和本次验证报告；M1、文档链接、契约、相关 API/Web 测试和准确代码 SHA CI 全部通过后结案，并按 GitHub 仓库规则提交、立即推送。

**阶段验收：** 8 个 cockpit 页面 + `/data` 截图齐全；页面数值与 API/manifest 行级对账通过；用例覆盖四个指定 KPI、行动项、各视觉交互和披露/演示区分；隔离数据源、数据 manifest SHA、代码 SHA、CI run 均可追溯。常驻库、原始档案与并发 worktree 不受影响。

## 非目标与风险

- 不把模拟月份、部门、客户、预算、预测、行动责任人标成菜鸟公开事实。
- 不增加通用自助 BI/拖拽设计器；不改变已批准财务指标公式、租户权限、审计事实源。
- 不为“看起来丰富”重复画同一数据；每个图需明确回答趋势、比较、结构、驱动或异常中的一个问题。
- 如需数据库 schema/迁移、CI/CD 配置、破坏性数据操作或系统级依赖变更，另按项目红线取得明确授权后才能实施；本计划默认使用现有模型、fixture 和依赖。
- 本工作完成后才将旧的“51 图映射已验收”表述与实测视觉证据对齐；项目 C 级财报质量门禁和真实企业数据验收状态不因驾驶舱变更而改变。

## 队列关系与后续恢复

本项当前为 [CURRENT_ROADMAP 唯一队列](../CURRENT_ROADMAP.md) 的单一队首，系用户明确调整顺序并授权立即执行。知识刷新 K2 顺延至本工作包完成后；各阶段只作为本项内部执行步骤，不单独进入领取队列。工作包完成并推送后，再按路线图继续后续项目。

## 依据与相关材料

- [前次项目进展与驾驶舱差距报告](../../60_delivery/verification/2026-10-17--project-progress-and-cockpit-gap-assessment-v1.md)
- [CFO 驾驶舱 51 图覆盖映射验收](../../60_delivery/verification/2026-10-16--cockpit-51-chart-coverage-mapping-v1.md)
- [CFO 驾驶舱盈利分析与图表补全设计](../../superpowers/specs/2026-10-17-cfo-cockpit-visual-analysis-expansion-design.md)
- [大麦演示发行版 fixture 说明](../../../fixtures/damai/README.md)
- [大麦物流企业数据包 v2 说明](../../../data/enterprise/damai-logistics/v2/README.md)
- [初始参考资料总览](../../knowledge-base/02_research/original/00_研究资料总览.md)
