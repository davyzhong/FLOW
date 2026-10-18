---
doc_id: FLOW-WI-SINGLE-MACHINE-VISUAL-20261018-001
title: 单机原型架构简化与全视图视觉升级
doc_type: work-item
status: active
version: 2.2
created_at: 2026-10-18
updated_at: 2026-10-18
owner: FLOW
depends_on: [FLOW-SPEC-SINGLE-MACHINE-VISUAL-20261018-001]
acceptance_refs: [FLOW-DECISION-D055]
applies_to: repository
decision_refs: [D052, D053, D054, D055]
supersedes: [FLOW-WI-COCKPIT-ALL-VIEWS-20261017-001]
superseded_by: null
related_plan: null
confidentiality: project-internal
---

# 单机原型架构简化与全视图视觉升级

> **当前状态：第 1–3 阶段完成；第 4 阶段 4.1–4.4 已结案，4.5 真实性、数值和追溯核验实际执行中。** 4.4 首轮已复用单期分类横条 builder，修正资产结构图型、标量值表期间列，并添加指标定义深链；前端测试/类型/构建与 API 路由专项通过，另将一处旧 cockpit fixture 对齐至 `objective.v3` 快照合同；具体进度以 CURRENT_ROADMAP 为准。4.4 验收记录：[模块图表适配与追溯验收](../../60_delivery/verification/2026-10-18--cfo-module-chart-adapter-acceptance-v1.md)。4.5 当前发现企业发行包源 manifest 指纹与 `fixtures/damai` 不一致，且发行版经营订单/件量小数；源 fixture 已整数化。 第 2 阶段准确代码 SHA `b0e1eb787592ff84bc4c19873a1e61cad1f9f3e6` 的 CI run `39099573268` 18/18 jobs success；第 3 阶段最终状态 SHA `20a511f66e4bfe65ab02edc091c7b49e2cbcbe67` 的 CI run `39125304357` 18/18 jobs success。4.1 矩阵验收与准确 SHA data-contract 两次取消后的隔离替代验证见[验收记录](../../60_delivery/verification/2026-10-18--cfo-reference-matrix-ci-and-isolated-validation-v1.md)。第 3 阶段实现与验证记录见[单机运行收敛验收记录](../../60_delivery/verification/2026-10-18--single-machine-runtime-convergence-v1.md)。唯一状态/顺序见 [CURRENT_ROADMAP](../CURRENT_ROADMAP.md)。本工作包替代旧全视图驾驶舱任务的剩余队列；既有 9 页、25 个画布、18 组路由/视口浏览器验收作为回归基线保留，不沿用取消/失败的 CI 运行作成功证据。

## 目标

将 FLOW 当前产品阶段收敛为单机单用户财务分析验证原型：减少运行服务和安装步骤，保住公开事实、客观计算、证据追溯和分析报告主链路；同时以用户已确认的 A+C 方向，让驾驶舱和报告视图达到高密度、精致、可读、可追溯的视觉完成度。

## 已批准选择

- 单机、单用户；多用户、组织/岗位/角色权限验证暂缓。
- SQLite 单文件为结构化数据权威源，应用本地文件目录保存原始文件和报告。
- 移除 Redis、Celery、MinIO；Excel 作为交换与备份形式，不作为业务关系和追溯的数据库。
- 视觉使用 A「高管编辑部」+ C「财务报告画布」；复用现有 ECharts，默认同时保证桌面与手机竖屏。

## 新增视觉参考（2026-10-18）

- 素材：微信公众号「数据熊」《集团财务总监经营驾驶舱》，2026-10-18，<https://mp.weixin.qq.com/s/P2_yh7sZOUMmQq7eNJrYdQ>。用户已将原文与 11 张图片单篇保存至 Obsidian；FLOW 只借鉴页面组织、图表类型和分析叙事，不复制截图数字、财务结论、阈值或设计素材。
- 素材摘要由 AI 生成且未逐项对照原图；图片内数据为演示示例，故仅作为视觉参考，不能作为来源事实、行业基准或指标定义。
- 对照远端页面目录，FLOW 已有 8 个 `/cockpit` 路由（总览、资产负债、现金流、合并、费用、盈利能力、风险、营运资金）及 `/data` 数据中心。参考文中的“利润增长”暂映射到总览和盈利分析，先做能力/数据覆盖核查，不预设新增独立页面；任何新增页面必须由可验证的用户场景和现有数据覆盖缺口支持。
- 参考图表类型可作为候选：经营趋势与同比、利润桥、收入/费用结构、杜邦关系、资产负债结构、营运周期与账龄、现金变动桥与预测、风险矩阵、合并抵销桥、数据导入校验。每一种只在指标定义、期间粒度和来源事实足够时实施；年度披露不能展开伪装成月度实际曲线。预算、账龄、13 周预测及合并抵销等缺少数据时标明 unavailable 和所需数据。
- README 截图采集与自动化工作流按用户要求继续暂停，本计划不恢复该流程；概念板与已有验收截图仅保留既有用途。

## 队列内执行步骤与验收

### 1. 现状与依赖审计（已完成，2026-10-18）

正式审计：[单机原型架构依赖与页面现状审计](../../60_delivery/verification/2026-10-18--single-machine-architecture-dependency-audit-v1.md)。共盘点 19 个页面路由、9 页/25 画布浏览器回归基线、32 个 PostgreSQL migrations、SQLite 方言和金额精度风险、对象存储及队列实际调用点，并只读登记主 checkout 四个未提交改动。未连接或修改任何数据库。

- 对照所有交互路由、页面状态、API 数据、指标目录、图表系列、数据表、报告和可用来源，建立页面/指标/图形/追溯覆盖矩阵。
- 对照 SQLAlchemy 最终模型与当前 PostgreSQL migration head，列出 Postgres 专用 DDL/DML、JSON/UUID、Decimal 精度、外键/约束/并发锁等 SQLite 风险。
- 逐调用点盘点 S3/MinIO、Redis/Celery、Docker Compose、Nginx 与启动脚本；区分实际业务能力、基础设施桩和测试专用环境。
- 盘点主 checkout 未提交改动，记录路径、基准差异与集成处置，未经用户指示不得覆盖/清理。
- 新增或修订正式决策时同步更新决策完整性门禁，避免测试仍将历史编号上限写死。

**通过条件：** 审计有机器可查的页面/功能/依赖清单；每个拟移除组件都有完整替代路径和测试点；决策完整性测试覆盖当前索引全部编号；旧全视图测试失败/取消与本轮新 CI 分开记录。

### 2. SQLite 与本地内容存储隔离验证（实现完成，待准确 SHA CI）

- 在一次性隔离 SQLite 数据库上验证模型建表/升级、UUID 与 JSON、外键、Decimal 精确读写、事务回滚和并发单用户行为。
- 以最小的真实样例验证公开报告装载、指标快照、财报/FactTrace 查询、驾驶舱聚合、报告冻结与恢复。
- 替换对象存储契约为本地内容寻址文件目录，覆盖同一 SHA 幂等、字节冲突、缺文件、下载和完整性错误。
- 构造 SQLite + 文件目录备份包，恢复到新隔离目录并重验来源/报告/驾驶舱结果。
- 先完成当前 ORM schema 对账和可重复的 SQLite 初始化/升级方案，再决定历史 32 个 PostgreSQL revisions 的归档方式；不同时维护两套运行 schema。

**本地与 CI 执行证据（2026-10-18）：** 新增 SQLite 通用模型注册、JSON/UUID 方言适配、定标整数 Decimal（SQLite）/原生 NUMERIC（PostgreSQL）、SQLite 外键连接钩子、文件内容寻址存储、自校验备份恢复，以及复用现有 Alembic 的 SQLite 专用基线链。SQLite 空库迁移创建 61 张模型表，重复 `upgrade head` 不重复执行基线；CFO 角色约束与 `0032` 迁移对齐。两期大麦财报导入、归一化、指标快照、客观冻结后备份恢复到新目录，来源字节/哈希、FactTrace、报表快照哈希及恢复后驾驶舱总资产 `71850.9310` 一致。CFO 模块 API SQLite 5/5、基础/备份/财务全链 16/16；隔离 PostgreSQL 16 完整迁移至 `0032` 后同 API 5/5；SQLite/PostgreSQL 大额 Decimal 读值与 SUM 零差异。首轮准确 SHA CI `cff0a94666c7b041689499af94bc28f0aef7b98b` 的 run `39096602647` 暴露生产查询使用 `.astext` 的 4 个 Copilot 测试失败，已改用跨库 `.as_string()`，隔离 PostgreSQL 上 Copilot 29/29 + eval 6/6、数据契约 26/26。准确 SHA `1311d6c093af2ca4d44dee8dcf10a23c3150b912` 的 run `39096880139` 又发现集成测试残留 `.astext`，且 data-contract job 达到 40 分钟时限；测试改用 `.as_string()` 后，隔离 PostgreSQL 定向测试和文件测试均通过。最终修复 SHA `b0e1eb787592ff84bc4c19873a1e61cad1f9f3e6` 的 run `39099573268` 全部 18/18 jobs success（包括 integration、data-contract、intake-e2e、metrics-known-answers、analysis-invariants），第 2 阶段验收完成。Ruff、mypy、文档 M1/M6、契约与路线图视图检查通过。所有数据库和文件均为一次性临时隔离目标。PostgreSQL 既有 32 个 revisions 未改动并保留为历史/测试链；SQLite 使用 `migrations_sqlite/` Alembic 链从当前 ORM 建立本地原型 schema。

**通过条件：** 全流程在隔离环境从空库完成；全部关键金额仍使用 Decimal 并与 PostgreSQL 基线零差异；来源锚点、哈希、分析值、报告与图表数值一致；备份恢复全链通过；失败记录可复现且未连接常驻库。

### 3. 单机运行结构收敛

- 移除 Redis/Celery 队列运行依赖，将已完成的分析路径明确改为同步请求及数据库记录状态；若单次操作需要耗时提示，提供本地进度状态而非空任务队列。
- 移除 MinIO/S3 依赖，所有原始资料、报告、导出和大麦发行包写入统一本地数据根目录，避免用户数据和仓库代码/测试 fixture 混放。
- 提供单一启动入口和本地服务地址；只有 Web/API 两个本机应用进程，默认绑定 localhost；开发测试所需隔离 Postgres Compose 仅在仍必要时作为测试专用配置，不进入普通用户启动路径。
- 更新设置、依赖、Docker/Make/README、运行与备份说明，清除失效环境变量和“必须启动多个基础服务”的旧指引。

**通过条件：** 停止 PostgreSQL/Redis/MinIO/Docker 后，新用户可从本地初始化命令启动并完成核心验证流程；没有残留运行时导入、环境变量或启动依赖；测试数据与应用本地数据目录分离。

### 4. 全站 A+C 视觉与真实数据完善

- **4.1（completed，2026-10-18）：页面/模块/数据覆盖矩阵。** 将参考文的 10 个模块逐项映射到现有 `/cockpit` 与 `/data` 路由、API、指标字典、事实和图表；已存在的盈利能力/杜邦及数据中心不得重复实现。单列“利润增长”能力差异，只有覆盖核查证明确有用户任务和可用数据缺口时，才提出新增独立路由。对每项记录现有页面/API、指标/公式、事实来源与数据粒度、现有图表/交互、覆盖结论（已有/需加强/缺失/数据受限）及证据路径；报告仅基于仓库和用户提供素材，不把文章 AI 摘要或演示数字当来源事实。报告含 10 个模块、数据层/粒度边界、入口拆分和跨模块缺口；验收结论和 CI 限制见[本子步验收记录](../../60_delivery/verification/2026-10-18--cfo-reference-matrix-ci-and-isolated-validation-v1.md)。准确 SHA `d8f2ae8d617914fcd05cfd21d8484154b1411a65` 的 run `39128676851` 中 data-contract 两次触及 40 分钟上限取消；隔离运行原脚本后 133+3 项测试、Ruff、mypy、摘要检查通过，M1/M6 通过。未将远端 CI 描述为全绿。
- **4.2（completed，2026-10-18）：图表需求与数据可用性。** 对 14 个页面/分析视图记录当前图表、数据字段/来源/粒度、可复用图表需求、展示缺口与不可支持项，证据见[盘点报告](../../60_delivery/verification/2026-10-18--cfo-chart-and-data-availability-v1.md)。确认大麦包有 10,752 条预算、4,800 条合成账龄事实等未进入当前 CFO 模块；公开年度事实、月度合成分配、月度模拟预算分层；记录 1,920 条经营明细订单数为小数的整数语义缺口。报告按代码/发行包静态检查，未连接数据库、未修改事实。
- **4.3（completed，2026-10-18）：组件复用与视图方案。** 完成逐视图 builder/组件映射和事实分层、URL 状态、表格/深链、移动/无障碍合同，详见[设计记录](../../60_delivery/verification/2026-10-18--cfo-chart-component-and-interaction-design-v1.md)。结论为继续复用 ECharts 6.1 和现有 builders，不增加图表依赖；已标出尚未接入的 aging/rank/heatmap/quadrant 适配器和资产负债图型语义缺口。
- **4.4（completed，2026-10-18）：视图实现。** 按 4.3 优先序接通已有 ECharts builders、补同值 DOM 数据表与明确深链，优化图表标题/期间/单位/缺失态。先核实源合同和测试，业务值不重算、不补零、不混合公开披露与 synthetic；单独账龄、预算图必须带“合成演示数据”标识。保持截图采集工作流暂停；验收见[模块图表适配与追溯验收](../../60_delivery/verification/2026-10-18--cfo-module-chart-adapter-acceptance-v1.md)。
- **4.5（completed，2026-10-18）：真实性、数值和追溯核验。** 重建大麦企业发行包，使 31 个发行文件与当前源 fixture 一致；verify 现在检查源 manifest 指纹及 business 下五类目录的逐文件字节一致性。经营实际 1,920 行中订单数、件量全部整数语义。公开年度事实与 synthetic allocation 保持原有分层，不插值或伪装为月度披露；无来源支持的预算、原因、阈值、预测和行业分位仍不生成。验收见[发行包血缘与整数数量验收](../../60_delivery/verification/2026-10-18--cfo-enterprise-package-lineage-and-integer-counts-v1.md)。
- **4.6（active，2026-10-18）：指标展示与交互补全。** 逐项核验关键指标的绝对值、单位、合理的小数位、同期/环比变化；来源和公式版本常显或一键可达。
- **4.7（4.6 验收后启动）：浏览器验收和结案。** 图表、表格、KPI、Finding、Action、指标定义、财报来源行之间建立可操作的导航/钻取；保证 URL 状态、返回路径、键盘和手机触控。视觉只使用真实数据图层；可用受来源允许的企业标识/报告缩略图辅助定位，不用装饰图片掩盖业务数据空缺。

当前公开事实只有年度粒度的项目，不得在页面上插值或分摊后冒充月度披露。Synthetic allocation 只能明确标识为演示分配数据并与披露事实分层展示；不产生未经来源支持的预算、原因、阈值、预测和行业分位。
- 第 4 阶段逐步完成时，确保营业收入、营业利润、毛利率、经营现金流和行动项在 CFO 首页首屏可见；杜邦拆解和各财务主题图表按页面契约完整呈现。

**通过条件：** 参考 10 模块覆盖映射完整并与现有路由核对（不得重复建设已有盈利能力和数据中心）；每项计划中的图表关联指标定义、所需数据粒度、来源与明确状态；所有已实现图表的数据/公式与 API、指标目录一致，每图含单位、期间、事实类别和来源状态；下钻与筛选可达；浏览器 1440/1024/390 视口和加载、错误、空、部分、完整状态检查通过且无溢出。截图采集仍暂停，本阶段不以新截图为验收条件。

#### README 视觉叙事同步（本轮先行交付）

- 仅使用仓库已有概念板和实测/公开财报截图，重新编排 README 首屏与图像导览，形成概念方向、真实产品页面、公开财报可视化三类清楚的视觉层次。
- 概念板明确标成静态概念稿和示意数据；真实截图注明采集日期、代码基线、演示或公开来源及其验收边界。
- 校准 README 的当前阶段、路线和能力陈述，链接回唯一 CURRENT_ROADMAP；不以 README 改写产品目标或架构决策。
- 不运行或恢复暂停的 README 截图采集工作流，不生成或改造产品截图，不重命名/移动/删除素材。

**通过条件：** README 在 GitHub Markdown 中有清晰的概念/实景/数据视觉叙事；所用素材全部已存在且来源可追溯；图像替代文本、文内锚点与相对链接通过现有文档门禁；进度和边界与当前路线图一致。

### 5. 集成、独立复核与结案

- 全量隔离测试覆盖空库启动、导入/种子、客观数据、指标/快照、页面查询、图表交互、证据/报告读取、导出和备份恢复。
- 验证财务精度、数据源分型、历史不可变性、原件哈希与审计链；不连接/重置常驻数据库。
- 浏览器逐路由与桌面/手机视口断言；截图采集工作流暂停期间不生成或保存新截图。记录真实运行 SHA、SQLite fixture/发行包 manifest SHA 与输出证据。
- 契约、API/Web 测试、lint、typecheck、生产构建、文档 M1/M6、完整 GitHub CI 全绿；每个实现提交后立刻 push，并核对准确 SHA CI。
- 由独立上下文只按 diff、验收标准和项目约定复核，修复影响正确性/需求的 P1/P2 后再运行最终门禁。
- 同步 PROJECT_STATE、CURRENT_ROADMAP、HANDOFF、README、安装与运行/备份文档；全任务 commit+push 后将本 work item 标记 completed，并把 K2 恢复为队列下一项。

## 明确不做

- 本阶段不建设多租户、多角色、组织权限、局域网多人使用、生产 HA、容器编排或在线发布。
- 不把 Excel 当关系型权威数据库；不重写现有指标公式或重复造图表组件。
- 不捏造菜鸟逐月/逐笔数据、趋势、经营原因、对标分位或责任人；不以 AI/图片制造看似真实的数值图表。
- 不删除历史 PostgreSQL 迁移、用户未提交文件或既存业务数据；备份/恢复与初始化职责分离。
- 不修改 CI/CD 配置、全局依赖或现有常驻数据库数据；若发现必要更改，先按项目红线处理。

## 计划与设计

- [正式设计规格](../../superpowers/specs/2026-10-18-single-machine-visual-prototype-design.md)
- [决策 D055](../../10_governance/decisions/D055--单机单用户验证原型.md)
- 当前队列唯一入口：[CURRENT_ROADMAP](../CURRENT_ROADMAP.md)
