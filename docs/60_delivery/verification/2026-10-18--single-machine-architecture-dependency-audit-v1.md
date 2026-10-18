---
doc_id: FLOW-VERIFY-SINGLE-MACHINE-AUDIT-20261018-001
title: 单机原型架构依赖与页面现状审计
doc_type: verification
status: verified
version: 1.0
created_at: 2026-10-18
updated_at: 2026-10-18
owner: FLOW
commit_refs: "0924024d"
evidence_refs: "[roadmap, single-machine-work-item, cockpit-visual-browser-baseline, current-source-audit]"
applies_to: architecture
---

# 单机原型架构依赖与页面现状审计

## 结论

当前代码仍按 PostgreSQL + Redis + MinIO + Celery + Web/API + Nginx 的开发栈组织。单机目标可以收敛为 Web 与 API 两个本机进程、SQLite 单文件和本地内容目录，但数据库工作不是直接替换连接字符串：32 个 PostgreSQL revisions 尚未形成 SQLite 初始化/升级路径；8 个 ORM 模块直接使用 PostgreSQL JSONB/UUID 方言，另有 `gen_random_uuid()`、`NULLS NOT DISTINCT` 等方言语义。金额字段使用 `Numeric(24,4)`，SQLite 不提供同等的定点数存储/计算保证，需要在实现阶段采用可精确往返的定标整数表示并验证聚合零差异。

已存在的页面和图表可作为视觉回归基线，不必重做所有产品页面。19 个交互路由中，9 个驾驶舱/数据视图已在既有记录中完成浏览器实测，共 25 个 ECharts 画布；其余路由仍需保留为单机核心工作流回归面。Redis/Celery 目前只有 `JobService`/基础设施适配器，没有业务路由调用 `enqueue_once`；当前 worker 只承担健康检查用途。S3/MinIO 则承载财报源文件、导入原件、发布/运营报告内容与演示账套文件，必须以统一的本地 SHA-256 内容寻址目录替代，并保留现有不可变与字节校验契约。

## 审计范围与证据基线

- 计划/范围：[单机原型工作包](../../50_plans/work_items/FLOW--single-machine-visual-prototype.md)、[D055](../../10_governance/decisions/D055--单机单用户验证原型.md)、[正式设计](../../superpowers/specs/2026-10-18-single-machine-visual-prototype-design.md)。
- 仓库与分支：`FLOW`，`codex/cockpit-visual-completion`；审计基准为 `0924024d`，其父提交 `a331f03075c95f3b371b5a0ebd0fd91cac9dfeae` 对应 GitHub Actions run `39090417203`，18/18 job success。当前审计为只读盘点，未连接任何数据库或执行会改写持久数据的命令。
- 页面视觉基线：[51 图覆盖映射](2026-10-16--cockpit-51-chart-coverage-mapping-v1.md)与[九页浏览器核验](2026-10-17--cockpit-all-views-visual-browser-verification-v1.md)。后者记录 1440px/390px 两种视口、9 页、25 个 ECharts 画布以及图表/API/数值表逐项核对；此为已存档验收记录，不代表本轮重新运行浏览器。
- 基础设施证据：`infra/compose.yaml`、`services/api/pyproject.toml`、`services/api/src/flow_api/infrastructure/`、API routes、`services/api/src/flow_api/infrastructure/models/`、`services/api/migrations/versions/` 与 `.github/workflows/ci.yml`。
- 主 checkout 的四处未提交更改已只读登记（见下表），不在本分支工作区内，也未暂存、覆盖或合并。

## 路由、数据入口与交互覆盖矩阵

以下清单从 `apps/web/app/**/page.tsx` 生成，共 19 个页面路由。数据入口按页面组件与 `apps/web/lib/api/client.ts` 的调用点归类；“视觉基线”列仅表示既有浏览器报告明确覆盖的路由。

| 路由 | 页面/组件 | 当前主要数据或动作 | 图形/可追溯现状 |
|---|---|---|---|
| `/` | `DashboardApp` | `/api/v1/dashboard/overview` | 主仪表盘；趋势/指标和 Finding 深链 |
| `/cockpit` | `CockpitOverviewApp` | `/api/v1/cockpit/overview`、`/api/v1/cockpit/action-items` | 4 个画布、行动项和来源/指标入口；视觉基线已测 |
| `/cockpit/profitability` | 盈利能力页 | `/api/v1/cockpit/profitability` | 杜邦、比较图和源行入口；基线已测 |
| `/cockpit/expenses` | `CockpitModulePage(expenses)` | `/api/v1/cockpit/modules/expenses` | ECharts 与数值表；基线已测 |
| `/cockpit/balance-sheet` | `CockpitModulePage(balance-sheet)` | `/api/v1/cockpit/modules/balance-sheet` | ECharts、指标及源行链接；基线已测 |
| `/cockpit/working-capital` | `CockpitModulePage(working-capital)` | `/api/v1/cockpit/modules/working-capital` | ECharts、DSO/DIO/DPO/CCC；基线已测 |
| `/cockpit/cashflow` | `CockpitModulePage(cashflow)` | `/api/v1/cockpit/modules/cashflow` | 现金桥/现金流比较；基线已测 |
| `/cockpit/risk` | `CockpitModulePage(risk)` | `/api/v1/cockpit/modules/risk` | 偿债比率图与 unavailable 状态；基线已测 |
| `/cockpit/consolidation` | `CockpitModulePage(consolidation)` | `/api/v1/cockpit/modules/consolidation` | 分部数据图，合并抵销不足时降级说明；基线已测 |
| `/data` | `DataWorkbench` | `/api/v1/intake/*` 导入批次、模板、映射、验证和发布 | 批次/导入状态可追踪，2 个画布；基线已测 |
| `/analysis` | 分析工作台 | `/api/v1/analysis/workbench/{reportId}` | 财报事实与分析运行关联；需纳入单机端到端回归 |
| `/statements` | `StatementsApp` | `/api/v1/statements`、详情、修正、发布 | 财报行/校验和发布动作；需纳入单机端到端回归 |
| `/reports` | `ReportsCenter` | `/api/v1/publishing/*`、冻结候选、尝试记录 | 发布快照及 HTML；需验证本地文件读取/导出 |
| `/operations` | `OperationsOverviewApp` | `/api/v1/operations/*`、公开期间 | 经营分析快照，可冻结并导出 HTML/PDF/XLSX/PPTX |
| `/metric-library` | `MetricLibraryApp` | `/api/v1/metric-library`、coverage、events、entries | 指标定义/治理变更与指标快照可追溯 |
| `/investigations` | `InvestigationApp` | `/api/v1/investigations` | Finding 列表和分析入口 |
| `/investigations/[findingId]` | Investigation detail | investigation、source-records、evidence decision、conclusion、transition、copilot | Finding→证据→源记录/结论链路 |
| `/internal` | 内部模块入口 | 页面导航，无独立数据 API | 模块入口与能力状态；不纳入 9 页截图基线 |
| `/public` | 公开模块入口 | 页面导航，无独立数据 API | 公开报告入口；不纳入 9 页截图基线 |
| `/login` | 登录页 | 登录会话接口 | 唯一不包裹 `AppShell` 的页面 |

已存视觉报告里 9 页、25 个画布的逐项数据、期间、单位、来源和交互信息继续作为相同页面迁移后的回归标准。其它页面的本次审计是代码入口盘点，不表示其当前状态、完整性或浏览器体验已重新验收。

## 数据与指标来源链路基线

- 经营/财务驾驶舱：`dashboard/overview`、`cockpit/overview`、`cockpit/modules/{module}` 与盈利能力端点，消费冻结指标/事实；模块数据包括 KPI、图表 series、瀑布/公式卡、unavailable 原因和财报源行信息。
- 客观来源：`statements`、`intake`、`operations`、`publishing` APIs。公开财报与经营披露被装载成 Statement/Canonical/MetricSnapshot/ReportSnapshot 等关系；原件经对象存储适配器读取。
- 分析与追溯：`analysis/workbench`、`analytics/metric-snapshots`、`analytics/analysis-runs`、`investigations` 与 copilot。页面链路应保持“图表或指标 → 定义/期间 → 冻结快照 → 财报源行/原件”的可复算证据链。
- 指标字典：`metric-library` 的定义、coverage 和 governance events；杜邦等派生值必须继续遵循冻结快照、定义版本和来源指纹，不在 UI 自行重新计算。
- 数据事实分型与既有演示数据边界见大麦来源登记、浏览器验收报告及正式财务事实合同；月度/组织分配是 synthetic，不得在迁移中被展示成菜鸟逐月披露事实。

## PostgreSQL/SQLite 兼容性风险清单

| 发现 | 代码证据 | 风险 | 实施验证要求 |
|---|---|---|---|
| 32 个 Alembic revisions（`0001`–`0032`）针对 PostgreSQL 编写 | `services/api/migrations/versions/` | revisions 中有 PostgreSQL 专用类型/默认值/索引语义；直接在 SQLite 执行不能视为受支持升级 | 定义一个 SQLite 新库初始化和单一 schema 版本升级路径；保留旧 revisions 作为历史，不并行维护两套运行 schema |
| 8 个 ORM 文件引用 PostgreSQL `JSONB` 或 UUID 方言 | analytics、canonical、copilot、enterprise_directory、intake、metric_library、publishing、statement | import/DDL 可能在 SQLite 直接失败，JSON 比较/索引行为不同 | 以 SQLAlchemy 通用 `Uuid`/`JSON` 或经验证的适配类型替代；建表、序列化、查询、索引回归 |
| PostgreSQL 服务端默认及约束 | cockpit 的 `gen_random_uuid()`；models 里 3 处 `postgresql_nulls_not_distinct` | 默认函数和 NULL 唯一语义不兼容；SQLite 需由应用稳定生成 UUID 并验证等价约束 | 创建/重复导入/NULL 维度唯一性/升级后写入专项断言 |
| 财务金额 `Numeric(24,4)` | analytics、canonical 等多表列定义 | SQLite NUMERIC 亲和类型可能转成浮点，精度与算术并不等同 PostgreSQL | 使用定标整数（精度标度由财务事实合同决定）及明确转换边界；验证读写、求和、公式、快照和导出与 PostgreSQL 基线 Decimal 零差异 |
| 关系约束和删除行为 | 外键、CASCADE/RESTRICT/SET NULL 定义分布在各模型 | SQLite 外键需显式开启；部分约束检查与 Postgres 不同 | 每个连接启用并断言 `PRAGMA foreign_keys=ON`；验证孤儿拒绝、级联和事务回滚 |
| 本地单用户并发模型 | 当前 Postgres 支持行锁与并发事务 | SQLite 写锁粒度不同；同步导入/冻结不能假设可并行写 | 明确单写路径、事务边界、busy timeout/短事务；覆盖双击/重复请求和失败回滚 |

金额精度风险是本阶段最重要的技术门槛。不能仅用 ORM `Numeric` 返回 Python `Decimal` 证明 SQLite 的底层值完全精确。

## Redis、Celery、MinIO、Compose 与启动调用点

| 组件 | 当前调用点/职责 | 分类与替代方向 | 必须覆盖的测试 |
|---|---|---|---|
| Redis + Celery | `infrastructure/jobs.py` 创建 Redis 客户端并 `send_task`；`application/jobs.py` 提供 `enqueue_once`。仓库内没有业务路由调用 `enqueue_once`；worker 仅有 health-check ping | 当前为未接入业务的基础设施桩。先识别被装配/测试引用的接口；产品流程改为同步执行并在 SQLite 记录状态，确认没有调用方后移除包依赖 | 导入/报告/冻结的同步成功、重复请求幂等、错误恢复、页面进度态；普通启动不要求 Redis/worker |
| MinIO/S3 | `statements.py`、`publishing.py`、`operations.py`、`intake.py` 的 source store 工厂；`fixtures/damai/loader.py` 写演示工作簿；`ObjectStore` 提供 SHA 内容寻址、不可变冲突检查、读回 hash 验证 | 实际业务能力，不能直接删掉。用 `pathlib` 本地目录实现原协议：`raw/{sha前缀}/{sha}`，原子写入、若存在逐字节校验；配置根目录在仓库外 | 相同 SHA 幂等、不同字节冲突、写入中断/原子性、缺文件、坏 hash、下载与内容恢复 |
| Docker Compose / Nginx | `infra/compose.yaml` 启动 API、Web、PostgreSQL、Redis、MinIO、MinIO init、worker、Nginx；默认占用 8000/3000/5432/6379/9000/9001 等端口 | 普通用户启动路径缩为本机 API + Web；Docker/数据库服务可留作已有测试专用流程，按工作包限制不修改 CI/CD 配置 | 仅启动本机应用后核心旅程可用；杀停所有 Docker 服务后重启验证 |
| 设置与脚本 | Settings 仍含 `DATABASE_URL`、`REDIS_URL`、S3 配置；多个历史脚本默认指向 PostgreSQL/Redis | 改为单一 `FLOW_DATA_DIR` / SQLite 文件 / 本地内容根路径，避免默认回落至开发数据库；明确历史脚本边界，不一概删除 | 从空临时目录启动；断言 resolved DB path 和对象路径均在临时目录；搜索无普通运行时 Redis/S3 环境依赖 |
| CI | `.github/workflows/ci.yml` 当前服务配置 Postgres/Redis，smoke job 检查 worker | CI/CD 配置变更不属于本批准工作包，当前不修改；可能需要后续单独决策 | 代码侧验证与文档状态以本地/准确 SHA CI 区分，不把旧 PostgreSQL CI 通过当作 SQLite 兼容证据 |

### 本地对象存储替代契约

复用项目现有 `ObjectStore` / `ProtocolObjectStore` 抽象与 SHA-256 规则；存储根目录取运行配置，且位于仓库外。写文件应先在同目录临时文件写完并 `fsync`，再用原子 rename；目标已存在时对完整字节重新计算 SHA。数据库记录仍保存对象 SHA、键、大小和 MIME 类型。恢复包应将 SQLite 数据库与内容目录一起打包，并在新临时目录校验全部引用。该方案不引入新的第三方对象存储库。

## 主 checkout 未提交更改登记（只读）

基准仓库 `/Users/qiming/workspace/FLOW` 当前有 4 个用户/并发任务修改，合计 120 insertions、11 deletions；本次只记录 diff，没有触碰这些文件。

| 路径 | 内容摘要 | 后续处置 |
|---|---|---|
| `apps/web/components/cockpit/cockpit.css` | 增加 CFO 模块 KPI、图表卡、公式卡、数据表和移动端样式 | 实施视觉阶段先对照现行版本确认是否被本分支后续变化覆盖；仅移植仍缺失的行为/样式 |
| `apps/web/components/cockpit/kpi-card.tsx` | aria-label 使用共享财务格式化函数，修正可访问名称格式 | 集成前确认共享组件现状及格式化语义；不直接覆盖 |
| `apps/web/components/cockpit/module-page.tsx` | loading/error/ready 根节点统一 `module-page` 样式类 | 后续页面改造时按 diff 语义吸收或保留 |
| `services/api/src/flow_api/cockpit/modules.py` | 财务风险模块增加前期比率和偿债趋势图 | 对照新图表/来源合同验证；数据正确且页面仍需时再整合 |

## 按已批准路线执行时的最小改造顺序

1. **本阶段完成：**将以上页面/API/图表/来源矩阵，ORM/迁移风险，依赖调用点与主 checkout diff 作为 SQLite 验证的固定检查清单。
2. **SQLite + 本地内容目录隔离验证：**先迁移通用 UUID/JSON、精确金额存储、唯一约束与外键；构造全新临时 SQLite 文件及临时对象根，不接触任何常驻栈；验证导入、快照、来源回读、报表、图表和恢复包。
3. **单机运行收敛：**只在隔离验证通过后改运行装配；移除未使用 Redis/Celery、MinIO/S3 运行依赖，新增同步任务状态与本地文件实现；提供一条初始化/启动入口。
4. **全视图视觉收敛：**沿用已验收九页当回归基线，扩充到其他路由；每个页面关联指标、真实来源、图形、交互和 unavailable 状态。
5. **全链验收与独立复核：**准确代码 SHA 测试和 CI、文档门禁、备份恢复、桌面/手机及独立复核。

初始只读审计没有将迁移写成执行完成；第 2 阶段已另行完成隔离实现和本地验证，待准确 SHA CI 后关闭。其余架构实现依次按第 3–5 阶段推进；具体验收细节仍以唯一工作包和路线图为准。

## 第 2 阶段隔离验证补充（2026-10-18）

原审计没有执行 SQLite 改造。随后按工作包第 2 阶段，在临时数据源完成以下验证；本段与初始只读审计边界分开记录：

- ORM 使用 SQLAlchemy 通用 JSON/UUID 类型，并对 PostgreSQL 保留 JSONB/UUID 方言；SQLite 启用外键，金额使用 scale-aware `ExactNumeric`（SQLite 定标整数、PostgreSQL 原生 NUMERIC）。模型注册补齐 `copilot_interaction` 与 `objective_report_snapshot`，共 61 张表。
- 新增 `alembic-sqlite.ini` 与 `migrations_sqlite/` 基线链。空 SQLite 文件迁移创建全 schema，重复 `upgrade head` 保持同一 revision；原有 PostgreSQL `0001`–`0032` 未改写。
- 隔离 SQLite 中导入 FY2022/FY2023 大麦公开财报、归一化并冻结客观报告；同时保存指标快照和来源文件。SQLite 数据库与 SHA 内容目录备份恢复至新目录后，报告与快照哈希、来源文件字节、FactTrace 及驾驶舱总资产 `71850.9310` 一致。
- SQLite 本地内容存储保持项目 SHA-256 不可变契约：幂等、并发同内容写入、键冲突、缺失、坏哈希和路径穿越均有隔离测试；备份包有逐文件 SHA-256 清单，恢复拒绝覆盖已有目标。
- SQLite CFO 模块 API 5/5，SQLite 基础/迁移/财务全链测试 16/16；隔离 PostgreSQL 16 完整迁移至 `0032` 后同模块 API 5/5。金额读回与 SQL `SUM` 在 SQLite/PostgreSQL 大额 Decimal 样本零差异。Ruff、mypy 与文档 M1/M6 通过。
- 过程发现并修正 `RoleBinding` ORM 检查约束遗漏 `cfo`（PostgreSQL `0032` 已允许）以及 SQLite 企业范围 UUID 查询返回字符串导致的类型不一致。
- 首轮准确 SHA CI `cff0a94666c7b041689499af94bc28f0aef7b98b` 的 Copilot job 暴露 JSON 通用类型不再提供 PostgreSQL `.astext` 比较器；两个查询已改用跨库 `.as_string()`。修复后隔离 PostgreSQL 的 Copilot 测试/评测和数据契约测试均通过；修复提交 CI 仍待验证。
- 后续准确 SHA `1311d6c093af2ca4d44dee8dcf10a23c3150b912` 的 run `39096880139` 有 13/18 jobs 成功、4 项失败、`data-contract` 在 40 分钟时限取消。4 项失败共同来自 `tests/integration/test_intake_e2e.py` 的测试查询仍使用 `.astext`；生产查询的残留调用已先行修复。该测试表达式现也改用 `.as_string()`，并在隔离 PostgreSQL 16 全量迁移后的新数据库上完成定向用例 1/1、测试文件 1/1 和 Ruff 检查。data-contract 是长时间数据/fixture 门禁，当前没有失败断言日志且本轮确实达到 40 分钟时限；没有调整 CI 配置或削减覆盖。新修复 SHA 的 CI 尚待运行。

这些验证只使用内存库、`/tmp` 文件数据库/对象目录和一次性 PostgreSQL 16 容器，未连接常驻开发库。当前代码提交后的准确 SHA CI 尚待验证；阶段状态以 [CURRENT_ROADMAP](../../50_plans/CURRENT_ROADMAP.md) 与 [工作包](../../50_plans/work_items/FLOW--single-machine-visual-prototype.md) 为准。

## 已知限制

- 页面矩阵将路由静态代码、API 客户端与既有浏览器报告组合盘点；除 9 页基线外未在本轮实际启动页面。
- 模型方言统计依据静态扫描；SQLite 适配结论必须以后续隔离建表/行为测试为准。
- 本审计没有运行测试或连接任何本地/常驻数据库；CI 证据只引用已核实提交的运行记录。
