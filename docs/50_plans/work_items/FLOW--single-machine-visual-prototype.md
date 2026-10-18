---
doc_id: FLOW-WI-SINGLE-MACHINE-VISUAL-20261018-001
title: 单机原型架构简化与全视图视觉升级
doc_type: work-item
status: active
version: 1.3
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

> **当前状态：第 1 阶段审计与第 2 阶段隔离验证的实现及本地检查已完成，待本轮准确 SHA 的 CI 验收后进入第 3 阶段。** 架构盘点与调用点矩阵见[审计报告](../../60_delivery/verification/2026-10-18--single-machine-architecture-dependency-audit-v1.md)。起始 CI 基线：准确 SHA `a331f03075c95f3b371b5a0ebd0fd91cac9dfeae` 的 run `39090417203` 全部 job success。唯一状态/顺序见 [CURRENT_ROADMAP](../CURRENT_ROADMAP.md)。本工作包替代旧全视图驾驶舱任务的剩余队列；既有 9 页、25 个画布、18 组路由/视口浏览器验收作为回归基线保留，不沿用取消/失败的 CI 运行作成功证据。

## 目标

将 FLOW 当前产品阶段收敛为单机单用户财务分析验证原型：减少运行服务和安装步骤，保住公开事实、客观计算、证据追溯和分析报告主链路；同时以用户已确认的 A+C 方向，让驾驶舱和报告视图达到高密度、精致、可读、可追溯的视觉完成度。

## 已批准选择

- 单机、单用户；多用户、组织/岗位/角色权限验证暂缓。
- SQLite 单文件为结构化数据权威源，应用本地文件目录保存原始文件和报告。
- 移除 Redis、Celery、MinIO；Excel 作为交换与备份形式，不作为业务关系和追溯的数据库。
- 视觉使用 A「高管编辑部」+ C「财务报告画布」；复用现有 ECharts，默认同时保证桌面与手机竖屏。

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

**本地执行证据（2026-10-18）：** 新增 SQLite 通用模型注册、JSON/UUID 方言适配、定标整数 Decimal（SQLite）/原生 NUMERIC（PostgreSQL）、SQLite 外键连接钩子、文件内容寻址存储、自校验备份恢复，以及复用现有 Alembic 的 SQLite 专用基线链。SQLite 空库迁移创建 61 张模型表，重复 `upgrade head` 不重复执行基线；CFO 角色约束与 `0032` 迁移对齐。两期大麦财报导入、归一化、指标快照、客观冻结后备份恢复到新目录，来源字节/哈希、FactTrace、报表快照哈希及恢复后驾驶舱总资产 `71850.9310` 一致。CFO 模块 API SQLite 5/5、基础/备份/财务全链 16/16；隔离 PostgreSQL 16 完整迁移至 `0032` 后同 API 5/5；SQLite/PostgreSQL 大额 Decimal 读值与 SUM 零差异。首轮准确 SHA CI `cff0a94666c7b041689499af94bc28f0aef7b98b` 的 run `39096602647` 暴露跨库 JSON 包装后仍使用 `.astext` 的 4 个 Copilot 测试失败，生产查询已改用通用 `.as_string()` 并在隔离 PostgreSQL 上复验 Copilot 29/29 + eval 6/6、数据契约 26/26。随后准确 SHA `1311d6c093af2ca4d44dee8dcf10a23c3150b912` 的 run `39096880139` 有 13/18 jobs 成功、4 项失败、data-contract 在 40 分钟 job 上限被取消；剩余失败全部因 `tests/integration/test_intake_e2e.py` 中一个 PostgreSQL 专用 `.astext` 测试表达式。改为 `.as_string()` 后，在新建临时 PostgreSQL 16 数据库上定向用例 1/1、该测试文件全量 1/1、Ruff 通过。data-contract 超时已有仓库历史记录，本轮复现；CI 配置未获授权修改，当前维持原覆盖与时限。该修复提交准确 SHA CI 待验证。所有数据库和文件均为一次性临时隔离目标。PostgreSQL 既有 32 个 revisions 未改动并保留为历史/测试链；SQLite 使用 `migrations_sqlite/` Alembic 链从当前 ORM 建立本地原型 schema。**修复提交的准确 SHA CI 通过后关闭本阶段。**

**通过条件：** 全流程在隔离环境从空库完成；全部关键金额仍使用 Decimal 并与 PostgreSQL 基线零差异；来源锚点、哈希、分析值、报告与图表数值一致；备份恢复全链通过；失败记录可复现且未连接常驻库。

### 3. 单机运行结构收敛

- 移除 Redis/Celery 队列运行依赖，将已完成的分析路径明确改为同步请求及数据库记录状态；若单次操作需要耗时提示，提供本地进度状态而非空任务队列。
- 移除 MinIO/S3 依赖，所有原始资料、报告、导出和大麦发行包写入统一本地数据根目录，避免用户数据和仓库代码/测试 fixture 混放。
- 提供单一启动入口和本地服务地址；只有 Web/API 两个本机应用进程，默认绑定 localhost；开发测试所需隔离 Postgres Compose 仅在仍必要时作为测试专用配置，不进入普通用户启动路径。
- 更新设置、依赖、Docker/Make/README、运行与备份说明，清除失效环境变量和“必须启动多个基础服务”的旧指引。

**通过条件：** 停止 PostgreSQL/Redis/MinIO/Docker 后，新用户可从本地初始化命令启动并完成核心验证流程；没有残留运行时导入、环境变量或启动依赖；测试数据与应用本地数据目录分离。

### 4. 全站 A+C 视觉与真实数据完善

- 按规格的页面分析契约覆盖 CFO 总览、盈利/杜邦、费用、资产负债、营运资金、现金流、风险、集团合并、数据、分析、报表和指标库现有页面。
- 每页从现有真实或明确分型的数据中选出有分析意义的趋势、同期/预算对比、构成、瀑布/驱动拆解、排名或矩阵；有足够数据才画，不足时说明缺口及形成完整图所需数据。
- 关键指标提供绝对值、单位、合理的小数位、同期/环比变化；来源和公式版本常显或一键可达。
- 营业收入、营业利润、毛利率、经营现金流和行动项在 CFO 首页首屏可见；杜邦拆解和各财务主题图表按页面契约完整呈现。
- 图表、表格、KPI、Finding、Action、指标定义、财报来源行之间建立可操作的导航/钻取；保证 URL 状态、返回路径、键盘和手机触控。
- 视觉只使用真实数据图层；可用受来源允许的企业标识/报告缩略图辅助定位，不用装饰图片掩盖业务数据空缺。

**通过条件：** 所有页面的实测图表/数据矩阵与 API/指标目录一致；每图含单位、期间、事实类别和来源状态；全站链接可达；桌面 1440 px 和手机 390 px 无溢出、数据可读；空、错、部分、完整等状态有明确外观；真实或演示来源清楚标记。

#### README 视觉叙事同步（本轮先行交付）

- 仅使用仓库已有概念板和实测/公开财报截图，重新编排 README 首屏与图像导览，形成概念方向、真实产品页面、公开财报可视化三类清楚的视觉层次。
- 概念板明确标成静态概念稿和示意数据；真实截图注明采集日期、代码基线、演示或公开来源及其验收边界。
- 校准 README 的当前阶段、路线和能力陈述，链接回唯一 CURRENT_ROADMAP；不以 README 改写产品目标或架构决策。
- 不运行或恢复暂停的 README 截图采集工作流，不生成或改造产品截图，不重命名/移动/删除素材。

**通过条件：** README 在 GitHub Markdown 中有清晰的概念/实景/数据视觉叙事；所用素材全部已存在且来源可追溯；图像替代文本、文内锚点与相对链接通过现有文档门禁；进度和边界与当前路线图一致。

### 5. 集成、独立复核与结案

- 全量隔离测试覆盖空库启动、导入/种子、客观数据、指标/快照、页面查询、图表交互、证据/报告读取、导出和备份恢复。
- 验证财务精度、数据源分型、历史不可变性、原件哈希与审计链；不连接/重置常驻数据库。
- 浏览器逐路由、桌面/手机截图；记录真实运行 SHA、SQLite fixture/发行包 manifest SHA 与输出证据。
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
