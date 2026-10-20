---
doc_id: FLOW-WI-SINGLE-MACHINE-VISUAL-20261018-001
title: 单机原型架构简化与全视图视觉升级
doc_type: work-item
status: active
version: 3.2
created_at: 2026-10-18
updated_at: 2026-10-20
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

> **当前状态：阶段 5门禁治理、阶段 6视觉实现、阶段 6.5数据契约分片、阶段 7单机验收和本轮门禁分片均已通过；7a 继续收敛概念图视觉差距并完成文档复核。** 最新准确 SHA `368a01902124351401d73dc9329800d7f00f3953` 对应 run `39349190031`，28/28 jobs success。阶段 7隔离 SQLite 冷启动、演示包 19/19、离线 HTML 和截图证据见[阶段 7验收记录](../../60_delivery/verification/2026-10-20--single-machine-visual-static-acceptance-v1.md)。SQLite + 本地文件目录备份恢复已在阶段 2验证。GitHub 截图工作流仍暂停。唯一状态/顺序见 [CURRENT_ROADMAP](../CURRENT_ROADMAP.md)。

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
- README/GitHub 自动截图工作流此前暂停；本次新增要求仅授权建立本机启动、验证和截图能力，不据此擅自重启 GitHub Actions 截图工作流。

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
- **4.6（completed，2026-10-18）：指标展示与交互补全。** 关键指标绝对值、单位、合理精度、期间变化和来源/公式可达性已核验；未知指标不猜测映射，倍率指标按字典单位显示。验收见[指标展示与追溯验收](../../60_delivery/verification/2026-10-18--cfo-metric-display-and-traceability-v1.md)，独立审查无 P1/P2。
- **4.7（本地验收完成，2026-10-18；最终关闭待准确 SHA CI）：浏览器验收和结案。** 隔离真实大麦双财年数据下 9 个 CFO/数据页面、165 项浏览器回归通过，验证图表与 API 一致、来源/Action交互、响应式和触控；截图/trace 关闭。证据见[浏览器验收记录](../../60_delivery/verification/2026-10-18--cfo-browser-acceptance-v1.md)。

当前公开事实只有年度粒度的项目，不得在页面上插值或分摊后冒充月度披露。Synthetic allocation 只能明确标识为演示分配数据并与披露事实分层展示；不产生未经来源支持的预算、原因、阈值、预测和行业分位。
- 第 4 阶段逐步完成时，确保营业收入、营业利润、毛利率、经营现金流和行动项在 CFO 首页首屏可见；杜邦拆解和各财务主题图表按页面契约完整呈现。

**通过条件：** 参考 10 模块覆盖映射完整并与现有路由核对（不得重复建设已有盈利能力和数据中心）；每项计划中的图表关联指标定义、所需数据粒度、来源与明确状态；所有已实现图表的数据/公式与 API、指标目录一致，每图含单位、期间、事实类别和来源状态；下钻与筛选可达；浏览器 1440/1024/390 视口和加载、错误、空、部分、完整状态检查通过且无溢出。截图采集仍暂停，本阶段不以新截图为验收条件。

#### README 视觉叙事同步（本轮先行交付）

- 仅使用仓库已有概念板和实测/公开财报截图，重新编排 README 首屏与图像导览，形成概念方向、真实产品页面、公开财报可视化三类清楚的视觉层次。
- 概念板明确标成静态概念稿和示意数据；真实截图注明采集日期、代码基线、演示或公开来源及其验收边界。
- 校准 README 的当前阶段、路线和能力陈述，链接回唯一 CURRENT_ROADMAP；不以 README 改写产品目标或架构决策。
- 不运行或恢复暂停的 README 截图采集工作流，不生成或改造产品截图，不重命名/移动/删除素材。

**通过条件：** README 在 GitHub Markdown 中有清晰的概念/实景/数据视觉叙事；所用素材全部已存在且来源可追溯；图像替代文本、文内锚点与相对链接通过现有文档门禁；进度和边界与当前路线图一致。

### 5. CI 与门禁解除（新队首，严格优先）

- 复核当前准确 SHA 的 GitHub Actions：区分真实测试失败、文档门禁错误、作业时限、旧 SHA 重复运行和 runner 排队；记录每个 run 的 SHA、job、起止与结论。
- 先收敛已知重复负载：过期 SHA 的整套运行不再与最新 SHA 竞争；旧 run `39179389944`（SHA `e27ad1c0`）已取消。失败提交 `b12289a0` 的 M6 元数据错误作为已修复历史问题；以最新 SHA 的作业结果为准。
- 修复 M1 暴露的计划状态门禁缺陷：状态表与详细执行队列重复引用工作包时，只认路线图状态表作为状态真相；支持合法 `queued` 状态并生成独立排队视图。补充回归测试，确保叙述链接不被误识别为重复状态记录。
- 准备 GitHub Actions 并发策略，使同一分支只保留最新 push 的全量 run，PR 与不同分支互不误取消；保留所有现存检查，不跳过测试、不降低覆盖、不把本地通过冒充远端通过。
- 已授权的具体最小 diff：在 workflow 顶层加入 `concurrency.group: ${{ github.workflow }}-${{ github.event.pull_request.head.repo.full_name || github.repository }}-${{ github.head_ref || github.ref_name }}` 与 `cancel-in-progress: true`。push 与 PR 对同一来源仓库/分支共用组，不同分支和 fork 不相互取消；只取消该组过期运行，不变更任何 job、触发器或测试命令。用户于 2026-10-19 明确选择允许修改。
- 长作业脚本审计发现明确重复：`integration` 已跑全量 `tests/integration`，而 `data-contract` 再跑 `test_data_contract_persistence.py` 与 `test_excel_database_round_trip.py`；`data-contract` 和 `intake-e2e` 均跑 `tests/data_contract`、`tests/fixtures`；`metrics-known-answers` 与 `analysis-invariants` 都重跑 `tests/integration/test_intake_e2e.py`，后者还重复指标测试；四个脚本重复 Ruff/mypy，三个脚本重复迁移校验，intake 脚本还重复合约检查及 web lint/typecheck（各有专门门禁）。
- 按唯一归属划分：全量集成测试归 `integration`；`tests/data_contract` 与 fixtures 归 `data-contract`；指标已知答案归 `metrics-known-answers`；分析测试归 `analysis-invariants`；intake 专项归 `intake-e2e`；静态、迁移、合约和 web 检查分别归对应门禁。对每一旧脚本的独立本地运行仍保留完整验证；GitHub Actions 环境仅运行该脚本独占范围。增加回归核对，证明原测试集合仍由全量 workflow 覆盖，且没有测试被移除。
- 对 `data-contract`、`intake-e2e`、`integration` 记录准确 SHA 的单次耗时与子步骤；保留稳定汇总检查名和完整测试集合。缓存或并行切片只有在测试隔离和确定性得到证据后再考虑。
- **授权边界与结案：** 顶层并发 diff 已于 2026-10-19 获用户明确授权并实施；不再改动 workflow 的触发器、job 超时或测试命令。最新远端 `data-contract` 达到现有 40 分钟上限后取消；同一 SHA 的隔离替代验收已完成，结论和限制见阶段 5 验收记录。

**结案条件与结果：** M1 队列状态门禁通过；新 SHA 推送后，同分支旧 run 自动取消；准确 SHA `dfc67283751a357d43ae23296e561cd286fea1dc` 的其余 17 项门禁成功；`data-contract` 的 CI 测试主体在同 SHA 全新隔离 Compose 项目上 133/133 通过，契约摘要通过。远端 `data-contract` 仍因 40 分钟 job 上限取消，完整限制见[阶段 5 验收记录](../../60_delivery/verification/2026-10-19--ci-concurrency-and-data-contract-isolated-acceptance-v1.md)。阶段 5并发治理与契约分片已结案；后续 CI 执行结构仍可能按本工作包第 9 节的覆盖证明继续优化，当前用户已明确授权实施门禁简化。

### 6. 按概念板完成视觉高保真（本机首轮完成；差距复核后重开，2026-10-20）

**首轮本机实现已交付，但此前“高保真结案”结论过早。** 组合图使用同一趋势响应中的收入/营业利润数据；现金流瀑布、杜邦因子、费用结构复用现有模块 API 和 ECharts builders。事实期间、单位、类别及来源入口已呈现，缺数态保留说明。2026-10-20 对照概念图发现页面仍受旧蓝色设计 token 与后台式布局控制，因此视觉验收重新打开；阶段 9重新按概念图逐项核对，不推翻已有的数据真实性和交互验收。


- 以 `docs/assets/cockpit-visual-direction-2026-10-18.png` 为验收基准，将概念板拆为可核对的视觉清单：纸白/暖白报告画布、墨蓝工作流导航、克制金色重点、编辑部标题与留白、首屏四项 CFO KPI、收入/利润趋势、经营现金流瀑布、杜邦驱动分解、成本结构、关键洞察/行动项、口径与来源说明。
- 先重构 `/cockpit` 总览，保证 1440px 首屏版式与概念图同构；随后按现有数据和能力覆盖扩展至 8 个 CFO 主题页及 `/data`，不重复创建已有功能，不为凑图表虚构事实。
- 复用 ECharts、现有指标/数据表和深链。所有图均展示期间、单位、数据类别、来源状态；图表有同值表格/可访问文本和可达的详情追溯。年度披露不伪装成月度真实趋势，合成数据需显著标注。
- 使用真实大麦发行包或公开财报数据验证。概念板内虚构的指标数值不得用作事实；无法被当前来源支持的视觉模块显示明确缺数/待配置状态。
- 本机验收启用截图：固定 `1440×900` 与 `390×844` 视口，保存总览及主题页面截图、数据批次与代码 SHA；截图为实际浏览器输出，不对图像摆拍或后期改数。

**本机验收结果：** 概念板对应的暖纸白画布、墨蓝导航、金色重点、四项核心 KPI、收入/营业利润趋势、经营现金流瀑布、杜邦拆解、费用排名、来源说明和行动项已落地。9 个 CFO/数据路由在桌面与手机共 18 个组合验证真实图表和无横向溢出；总览 KPI 与趋势明细逐项核对 API；桌面总览、手机总览和盈利能力页面截图已保存。详见[阶段 6 本机验收记录](../../60_delivery/verification/2026-10-19--cfo-cockpit-visual-phase6-local-acceptance-v1.md)。准确 SHA `dc705fec087c0b4d41e3a5a85baa38d9811269d8` 的 GitHub Actions run `39265415539` 为 17/18 成功，唯一取消项 `data-contract` 达到 40 分钟上限且无失败报告；同一 SHA 的隔离 Compose 执行 `GITHUB_ACTIONS=true bash scripts/test_data_contract.sh`，133/133 通过、契约摘要检查通过。阶段六按[验收记录](../../60_delivery/verification/2026-10-19--cfo-cockpit-visual-phase6-local-acceptance-v1.md)结案；阶段 7 已排至唯一队首。

### 6.5 收敛 data-contract 单个长作业（completed，2026-10-20；保留全量测试）

**现状证据：** 阶段 6 准确 SHA `dc705fec087c0b4d41e3a5a85baa38d9811269d8` 的 GitHub Actions run `39265415539` 为 17/18 jobs success，唯一取消项 `data-contract` 达到 40 分钟上限且没有测试失败报告。相同 SHA 的新隔离 Compose 环境执行 `GITHUB_ACTIONS=true bash scripts/test_data_contract.sh`，133 项通过（1066.42 秒），数据摘要 `operating=3072 financial=432 budget=120 ar=1920` 一致。说明当前反馈障碍来自单 job 时长，不是测试失败或前一 SHA 占队列。

**本阶段执行方案与本机结果：** 已将 `tests/data_contract` 与 `tests/fixtures` 的 133 项全量测试按文件分配到五个独立 CI shard，每个 shard 使用 runner 自带的隔离服务/数据库，避免共享可变数据库造成并行竞争；五个 shard 全成功后，由稳定名称 `data-contract` 的汇总 job 执行摘要校验并作为唯一汇总检查。固定分组为：

1. 契约/workbook 测试（`tests/data_contract/`，26 项）；
2. 菜鸟 canonical 与 statements（35 项）；
3. generator 与 source registry（30 项）；
4. profile、已知答案、workflow loader 与 analytics loader（26 项）；
5. atomicity、通用 generator/loader 与 metric grain（16 项）。

每个文件只归入一个 shard；固定 `pytest` 路径映射，不使用基于运行时顺序的随机拆分。每个 shard 保留 `uv sync`、`make infra-up`、相同 Python 版本和现有 40 分钟上限；不改变 workflow 触发器、测试内容、覆盖范围或 timeout。汇总 job 必须在任一 shard 失败/取消时失败，不能以 skipped/neutral 掩盖失败；全部 shard 成功后运行 `scripts/summarize_data_contract.py`，保持稳定 `data-contract` 检查名。

**本机验证：** `scripts/data_contract_shards.py --verify` 通过；五组分别 collect 为 26+35+30+26+16=133 项；新增映射/CI 结构测试 3/3、门禁清单测试 6/6，workflow job 验证 26/26。服务端 Ruff、mypy 与脚本测试已运行；`make contracts-check`、M1/M6 和 Markdown 链接检查通过（链接检查使用 `python3 scripts/documentation/links.py --check`）。完整准确 SHA GitHub CI 尚待本次提交后确认。

**验收结果：** 本机 shard 路径互斥且并集精确覆盖 133 项；新增映射测试 3/3、CI 清单测试 6/6、workflow job 验证 26/26；准确 SHA `3ac44738c75f710156724a8584bda1144624235d` / run `39276126532` 的五个 shard 和 `data-contract` 汇总全部 success。各 shard 用时：`contracts` 1分14秒、`canonical-statements` 1分16秒、`generator-source` 1分14秒、`profile-known-workflow` 21分26秒、`loader-atomicity-edges` 11分18秒；稳定汇总检查约 49 秒。全量 133 项未删减，均低于 40 分钟。workflow 其他已完成门禁均成功；`integration` 在记录时仍处于 GitHub `in_progress`，所以整条 workflow 尚无全绿结论。阶段 6.5 的指定验收目标已满足，阶段 7 进入唯一队首。

### 7. 单机静态运行、验收与截图闭环（新阶段）

- 从当前实现重新盘点进程、外部服务、运行依赖、数据路径和安装步骤；明确区分构建依赖与日常运行依赖。
- 保持 SQLite 单文件与本地文件目录为事实源。对可只读展示的财报视图，评估并优先产出冻结 JSON/HTML 与 ECharts 静态页面；数据变更后由显式本地命令重建，静态发布物记录来源批次、公式/指标版本和内容 SHA。
- 提供最少命令闭环：初始化/构建、启动、验收、数据校验、浏览器截图；新建临时数据目录即可运行，不要求 Postgres、Redis、MinIO、云账号或容器编排。关键交互需要后端时，采用现有 SQLite/API 本地路径，不强迫全站动态化。
- 从空的隔离目录执行完整流程并保留日志/manifest；验收 UI 关键金额与指标 API 一致、业务源包 hash 一致、静态文件可离线打开、SQLite/本地对象存储备份恢复可用。
- 更新 README、安装/运行/备份文档和 HANDOFF，明确最低环境要求、实际命令、截图位置、常见故障恢复；截图仍不自动上传。

**通过条件：** 在无 Docker/无服务容器且无外部网络的本机环境，从新数据目录可一次完成 build/init、启动、关键路径验证与截图；静态图表可离线浏览且数据有来源/版本追溯；常驻用户数据不被测试重置；性能/容量边界与仍保留的动态路径如实记录。

**阶段 7 本机验收结果（2026-10-20；准确 SHA CI 已闭环）：** 在 `/tmp/flow-stage7-20261020` 空隔离目录执行 `make flow-bootstrap`、`make flow-init`、`make flow`，生产 Web 构建完成，SQLite migrations `sqlite0001`–`sqlite0004` 执行，API 与 Web 绑定 `127.0.0.1` 并返回 HTTP 200；普通启动未使用 Docker、PostgreSQL、Redis 或 MinIO。加载大麦合成演示批次后，`scripts/verify_damai_demo.py --check-storage` 报告 `ok=true`、19/19、failed=[]；发行包 manifest SHA `6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed`、批次 `01a154ea-455d-79fb-8521-072795629bec`。真实总览包含四项核心 KPI、趋势、经营现金流桥、杜邦、费用和行动项；新增 stale 数据提示回归测试。桌面总览、手机总览、盈利分析和自包含 HTML 均截图。离线 HTML 打开检查：8 KPI、内嵌 API JSON、来源/代码版本均存在，外部网络请求 0、页面错误 0；移动视口无横向溢出。截图索引：[screenshots README](../../assets/screenshots/README.md)，原图位于 `docs/assets/screenshots/cockpit-single-machine/`。SQLite + 内容目录备份恢复至新目录、逐文件校验及驾驶舱结果一致的既有验证见[阶段 2验收记录](../../60_delivery/verification/2026-10-18--single-machine-runtime-convergence-v1.md)。阶段 7准确 SHA `431cf62bec94bd009cce8b205962eeb8bff68120` 的 GitHub Actions run `39343622288` 为 23/23 jobs success；其中 `integration` 用时 36分51秒，是后续门禁拆分的实测基线。

### 8. 集成、独立复核与结案

- 全量隔离测试覆盖空库启动、导入/种子、客观数据、指标/快照、页面查询、图表交互、证据/报告读取、导出和备份恢复。
- 验证财务精度、数据源分型、历史不可变性、原件哈希与审计链；不连接/重置常驻数据库。
- 浏览器逐路由与桌面/手机视口断言；按用户本轮授权在本机生成可复验截图，记录真实运行 SHA、SQLite fixture/发行包 manifest SHA 与输出证据。
- 契约、API/Web 测试、lint、typecheck、生产构建、文档 M1/M6、完整 GitHub CI 全绿；每个实现提交后立刻 push，并核对准确 SHA CI。
- 由独立上下文只按 diff、验收标准和项目约定复核，修复影响正确性/需求的 P1/P2 后再运行最终门禁。
- 同步 PROJECT_STATE、CURRENT_ROADMAP、HANDOFF、README、安装与运行/备份文档；全任务 commit+push 后将本 work item 标记 completed，再恢复 K3 来源审核队列。

### 9. 概念图视觉差距、门禁负载与文档治理（当前 7a 串行执行依据）

本轮对照证据：概念图为暖纸白画布、墨蓝导航、金色重点、衬线编辑部标题、明显的图表主次与叙事卡片；当前 `/cockpit` 共享 CSS 仍注释并使用旧版 `#2563eb` 蓝色主色、标准后台灰白底和紧凑标题。两边虽都有 KPI、趋势、瀑布、杜邦、成本和行动项，视觉语言与层级并未对齐。不得把“已有对应组件”当成视觉验收完成。

严格按以下单一顺序执行；状态与队列只写入 `CURRENT_ROADMAP.md`：

1. **视觉差距闭合（持续执行）：** 以概念板为视觉基准，统一总览、主题模块、`/data`、工作流侧栏的暖纸白、墨蓝、古金、衬线标题和报告式层级。沿用 ECharts 与现有数据/公式，不使用概念稿示意数；保留语义状态色和准确金额、百分比及 synthetic/reported 标签。已有桌面总览实测和九路由 1440px/390px 断言，但用户反馈实际风格、配色与概念图仍有明显距离，因此不得以配色 token 已改或路由正常作为关闭条件。下一轮须先逐屏对照概念板，核实实际渲染的容器色、导航、标题层级、卡片尺寸、图表面积/比例、标签、留白及移动阅读顺序，再针对造成差距的通用组件落地修正；验证 Web tests/typecheck/build、图表数据/深链及 1440/1024/390 视口。实测图仅用于本机验证，GitHub 截图自动化工作流保持暂停。
2. **门禁减负（已通过，2026-10-20）：** 基线 SHA `431cf62b` 的 `integration` job 为 36分51秒。固定文件映射的四个隔离 shard 覆盖原 284 项测试/66 个文件，校验脚本证明零遗漏、零重复；每个 shard 独立准备服务并迁移数据库。稳定 `integration` 汇总检查负责失败传播，10x 性能门禁独立保留。准确 SHA `368a01902124351401d73dc9329800d7f00f3953` / run `39349190031` 为 28/28 jobs success；各测试未被移除。不得降低断言、静默跳过测试或以本地通过代替远端通过。
3. **项目文档 review 精简（进行中）：** 已更新 README、文档导航、计划导航、知识库导航、PROJECT_STATE、CURRENT_ROADMAP 与 HANDOFF 的当前状态；校正日常 SQLite/本地文件运行边界与旧 CI 失败叙述。继续检查运行/备份说明、有效交接引用、状态和截图元数据。原始研究、有效历史决策与验收证据按规范保留；只改正当前入口中的过时内容。对疑似删除项做精确路径、引用扫描与保留价值审计；未获得具体路径授权前不删文件。
4. **最终复核与交接：** 本机文档 M1/M6、链接、计划视图、前后端相关验证和浏览器回归通过；远端全量 CI 对应最终提交 SHA 全绿后才能关闭 7a。同步 README、PROJECT_STATE、CURRENT_ROADMAP、HANDOFF 与截图索引；记录视觉验收图和门禁分组/耗时，核实没有触碰常驻账套。

**结案条件：** 概念板关键视觉签名实际落地且九路由统一；核心图表与数据无回归；当前最长 CI 等待有可复现的分组耗时下降且测试集合零减少；current-state 文档只保留最新状态且所有链接有效；删除项未获逐项授权前一律只登记、不执行。

## 明确不做

- 本阶段不建设多租户、多角色、组织权限、局域网多人使用、生产 HA、容器编排或在线发布。
- 不把 Excel 当关系型权威数据库；不重写现有指标公式或重复造图表组件。
- 不捏造菜鸟逐月/逐笔数据、趋势、经营原因、对标分位或责任人；不以 AI/图片制造看似真实的数值图表。
- 不删除历史 PostgreSQL 迁移、用户未提交文件或既存业务数据；备份/恢复与初始化职责分离。
- 不更改全局依赖或现有常驻数据库数据；CI/CD 配置按阶段 5 的独立授权流程执行。

## 计划与设计

- [正式设计规格](../../superpowers/specs/2026-10-18-single-machine-visual-prototype-design.md)
- [决策 D055](../../10_governance/decisions/D055--单机单用户验证原型.md)
- 当前队列唯一入口：[CURRENT_ROADMAP](../CURRENT_ROADMAP.md)
