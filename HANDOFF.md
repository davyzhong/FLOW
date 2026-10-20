---
doc_id: FLOW-HANDOFF-STRATEGY-20260912
title: FLOW 项目交接文档
doc_type: navigation
status: current
version: 8.5
created_at: 2026-09-12
updated_at: 2026-10-20
owner: FLOW
applies_to: repository
---

# FLOW 项目交接文档

> 本文档是下一位 Agent 接手的唯一入口。项目唯一权威状态以 [CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md) 为准；本文档提供接手上下文、踩坑记录和下一步操作指引。

### 2026-10-20 接手核验（当前快照）

- 当前工作区为 `.worktrees/execution-convergence`，分支 `main`，起始 HEAD `5ed61af91ea4c1c2a2078fd654accf671ba805ba`，与 `origin/main` 一致且干净；开工前已执行 `git pull --ff-only`。
- 最新 HEAD 对应 GitHub CI run `39119888132`，SHA 与 HEAD 完全一致，`success`，18/18 jobs。该结果不代表后续提交。
- 唯一 To-do 以 [CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md) 为准：14 项，已完成 7、实际执行中 0、队首待开始 1、排队 4（含 K2）、暂停 1、外部材料受限 1。唯一队首是 D055 单机原型架构简化与全视图视觉升级。
- 状态已收敛：路线图说明“第 3 阶段启动准备完成、运行时实现待启动”，与唯一队列和工作包状态一致；工作包第 2 阶段标题已更正为“已完成，准确 SHA CI 验收通过”。当前可核实的是第 1、2 阶段完成、依赖路径盘点已交付，第 3 阶段运行时实现尚未开始。
- 主 checkout `/Users/qiming/workspace/FLOW` 是独立工作区：分支 `flow/u04-closeout-20261016`，落后 `origin/main` 63 个提交；有 4 个已修改文件和 1 个未跟踪 YAML。本轮未触碰，后续不得覆盖、暂存、清理或擅自合并。
- 本轮更新了 HANDOFF、CURRENT_ROADMAP、单机工作包及自动生成的计划视图；未访问常驻数据库、未触发暂停的截图采集工作流、未修改 CI/CD 配置。

---

## 一、当前任务

**当前任务：单机原型架构简化与全视图视觉升级（D055）**。目标决策与范围不变：单机单用户、SQLite 单文件 + 本地文件目录、退出 Redis/Celery/MinIO、A「高管编辑部」+ C「财务报告画布」。第 1 阶段审计、第 2 阶段 SQLite/本地内容存储隔离实现与准确 SHA CI 验收均已完成；第 2 阶段 SHA `b0e1eb787592ff84bc4c19873a1e61cad1f9f3e6` 的 run `39099573268` 为 18/18 jobs success。依赖路径盘点和调用点矩阵已交付；第 3 阶段运行时实现尚未开始。审计覆盖 19 个页面路由、32 个 PostgreSQL revisions、SQLite 方言/金额精度风险及 S3/Redis/Celery 调用点。README 视觉编排已完成，使用已有 A+C 概念板和实景素材，并标明示意、演示与公开数据边界；M6、readme-craft（81.1/100）及 71 项相对链接/图像引用检查通过。详见[架构审计报告](docs/60_delivery/verification/2026-10-18--single-machine-architecture-dependency-audit-v1.md)。截图采集工作流仍按用户要求暂停，不得触发。完整范围见[唯一工作包](docs/50_plans/work_items/FLOW--single-machine-visual-prototype.md)、[设计规格](docs/superpowers/specs/2026-10-18-single-machine-visual-prototype-design.md)和[当前路线图](docs/50_plans/CURRENT_ROADMAP.md)。

此前全视图驾驶舱工作包作为回归基线归档：九页 25 个 ECharts 画布、桌面/手机 18 组视口验收、API/页面数据对账、来源深链与缺数态等本地证据保留。真实 CI 状态：`39042517573`（SHA `e6b68c8a`）和 `39041228479`（SHA `0b9b12f3`）均 cancelled；`39040652008`（SHA `b2ee0373`）和 `39038535194`（SHA `df5c338b`）均 failure；不能说旧全视图任务准确 SHA CI 已通过。阶段 2 准确 SHA `09ba5722ec3e8075a3483223df4c81fe5cdaa9fa` 的 run `39035163288` 为 18/18 成功。相关[旧工作包](docs/50_plans/work_items/COCKPIT--all-views-data-and-visual-completion.md)已 archived 且禁止继续执行；[浏览器验证报告](docs/60_delivery/verification/2026-10-17--cockpit-all-views-visual-browser-verification-v1.md)仅作为回归基线。

主 checkout `/Users/qiming/workspace/FLOW` 当前状态：分支 `flow/u04-closeout-20261016`，落后 `origin/main` 63 个提交；四个已修改文件为 `apps/web/components/cockpit/cockpit.css`、`apps/web/components/cockpit/kpi-card.tsx`、`apps/web/components/cockpit/module-page.tsx`、`services/api/src/flow_api/cockpit/modules.py`，另有未跟踪文件 `docs/knowledge-base/00_governance/migration/source-inputs-2026-10-19.yaml`。本轮未触碰。后续先核实归属、与最新 main 的关系和文件用途；未经授权不得覆盖、暂存、清理或自动合并。

**CFO 驾驶舱盈利分析与图表缺口补全已完成**。本分支新增盈利能力页面 `/cockpit/profitability`、只读 API 与冻结时杜邦指标载荷；提供净利率、ROE、总资产周转率、权益乘数、两期比较、勾稽提示、指标/报告/来源财报行深链。图表复用 ECharts；旧快照或缺少期初数据时明确显示 unavailable。前端 36 个测试文件/184 项通过、typecheck/build 通过；lint 零错误，有一条既有 TanStack Table 警告；后端隔离定向测试 12 项、Ruff、mypy 通过；隔离账套核验 19/19、可见性矩阵 162 项无失败、浏览器全旅程 16/16 通过，真实页面截图见[浏览器验收记录](docs/60_delivery/verification/2026-10-17--cockpit-profitability-browser-verification-v1.md)。CI 首轮发现重复 seed 会新增两份 Objective 快照；修复归一化行 UUID 不稳定性后，回归测试 10 项通过，准确 SHA `08aa4cd02247f995bc990d92c8f34f5a1829afa1` 的 GitHub CI run `38996089002` 为 18/18 job success。contracts、plan views、links 与 M1 通过。代码与修复提交分别为 `5817efcf`、`08aa4cd0`，均已推送。工作包/设计/计划见 [工作包](docs/50_plans/work_items/COCKPIT--visual-analysis-expansion.md)、[设计规格](docs/superpowers/specs/2026-10-17-cfo-cockpit-visual-analysis-expansion-design.md)、[实施计划](docs/superpowers/plans/2026-10-17-cockpit-visual-analysis-expansion.md)。独立审查发现的单位误标和来源行下钻缺口均已修复。

**当前唯一队列：14 项，已完成 7、实际执行中 0、队首待开始 1、排队 4（含顺延的 K2）、暂停 1、外部材料受限 1。** D055 完成后恢复知识刷新 K2；执行前只读核验 ObsidianWiki 状态。K0/K1/K2 的证据、dirty vault 保护与来源说明见[知识刷新工作包](docs/50_plans/work_items/KNOWLEDGE--refresh-v2.md)。

用户四项裁决（2026-10-16）：
1. **L0 挂 CI（选项 C）**：非阻断 `l0-baseline` job（continue-on-error: true），失败仅作信号灯。
2. **盲评复评范围（选项 A）**：仅旧三样本（顺丰/腾讯/中通）。
3. **C 级维持 6 条件不变（选项 A）**：诚实标准，做不到如实 No-Go。
4. **ZTO 立即恢复（选项 C）**：`wip/zto-integration-20260929` 已解封合并。

---

## 二、已完成的内容

### 前序驾驶舱交付清单（2026-10-17，历史基线）

| 交付 | 提交 | 验证/状态 | 要点 |
|---|---|---|---|
| CFO 全视图页面、来源联动和完整浏览器验收 | `b2ee037375ff0949a1dec442bd3ac4feb6bb078d` | 本地通过；CI run `39040652008` 的 M6 因报告状态 `active` 失败，已在下一提交修正 | 九视图 25 个 canvas；桌面/手机 18 组通过；18 张截图；所有模块 series/waterfall/formula-card 与盈利明细逐项核对 API；截图报告见下方索引 |
| 验收报告状态修正 | `0b9b12f3e0138898ff719d2f1db378cd793b9d5f` | 已推送；CI run `39041228479` cancelled | verification 状态改为 `draft` 以满足 M6；本包被新工作包接替，准确 SHA 全 CI 未通过 |
| 独立复核 | — | 已完成，无 P1/P2 | 复核覆盖所有 module chart、waterfall steps、公式卡 DSO/DIO/DPO/CCC、盈利能力所有明细行 |

本地验收：`pnpm -r lint && pnpm -r typecheck` 通过（3 条既有 warning）；`pnpm --filter @flow/web build` 通过；相关 Vitest 10/10；目标 Playwright 18/18 路由×视口通过（在现有隔离服务上设置 `PLAYWRIGHT_BASE_URL=http://127.0.0.1:3461`）；`make contracts-check`、文档 M1/M6、`git diff --check` 通过。浏览器报告及全部截图：[全视图浏览器核验报告](docs/60_delivery/verification/2026-10-17--cockpit-all-views-visual-browser-verification-v1.md)。

### 前序批次（2026-10-13 ~ 10-16）交付清单

| 交付 | 分支 | main 合并 | CI | 要点 |
|---|---|---|---|---|
| **Codex 分支合并** | codex/damai-logistics-data-audit | `3b5c82b8` | ✅ | 28+ 提交（驾驶舱批次 A + ECharts + F1/F2 + 来源审计 + 驾驶舱批次 A 门禁），60 文件 +5552 行 |
| **来源事实登记** | flow/source-registry-20261013 | `d9a99ece` | ✅ | 325 条 disclosed_fact + 页锚机械核验 + 7 项假设处置；13 项 pytest |
| **运营披露层重建** | 同上 | `e5d8d2c6` | ✅ | 分部序列/件量改用菜鸟披露值（FY2023 国际 1,519 百万件）；废弃收入推导件量 |
| **时间线迁移** | flow/timeline-migration-20261013 | `c824f55f` | 17/17 ✅ | FY2022/FY2023 真实财年；明细↔披露年度聚合零差异；IFRS 三表过发布门禁；ORG-LEDGER v2 |
| **F3** | flow/finmetric-f3-20261014 | `4951fcfb` | ✅ | capex 符号修复（FCF −37.3 亿）；18 项缺口族裁决测试 |
| **F4** | 同上 | `732d1dcd` | ✅ | 环比 prior_month 窗口 + MetricCard.mom 契约 |
| **批次 B** | 同上 | `5421f01a` | 17/17 ✅ | 安全规格 V1.1.1 + cfo 角色 + 行动项闭环 + 独立审查 |
| **C-2** | flow/cockpit-c2-20261014 | `07a07b7c` | 17/17 ✅ | 资产负债/营运资金模块页 |
| **C-3/C-4/C-5** | flow/cockpit-c3-20261014 | `95427ae4` | 17/17 ✅ | 费用/现金流/风险/合并四模块 |
| **批次 D** | flow/cockpit-d-20261015 | `14016297` | 17/17 ✅ | 问数入口嵌入 |
| **51 图验收** | flow/cockpit-acceptance-20261016 | `df6073a8` | 17/17 ✅ | 10 模块×51 图覆盖映射文档 + 全链门禁绿 |
| **U04 盲评复评** | flow/u04-blind-review-20261016 | `707733dd` | 17/17 ✅ | **199/199 全绿**（顺丰 137 + 腾讯 32 + 中通 30）；C 级条件 5 通过 |
| **ZTO 解封** | 同上 | `ad255d3d` | ✅ | 合并 `wip/zto-integration-20260929`（+18506 行） |
| **L0 挂 CI** | 同上 | `b5c58c59` | ✅ | `l0-baseline` CI job（非阻断）+ `l0_baseline_check.py` |
| **路线图 v5.52** | 同上 | `08dfdfae` | ✅ | U04 → completed；队列 12 项：完成 6 / 执行中 0 / 排队 4 / 暂停 1 / 外部受限 1 |

### 更早交付（已在 main，本轮验证不回退）

| 内容 | 要点 |
|---|---|
| 来源事实登记 `config/damai/source_facts_v1.yaml` | 325 条、四分型、页锚对 PDF 机械核验 |
| 来源基线审计 | `docs/60_delivery/verification/2026-10-12--damai-source-baseline-audit-v1.md` |
| 驾驶舱批次 A（总览页） | `ae56e96f`/`b7dc4983`，CI 17/17 |
| ECharts 6.1.0 + 10 类构建器 | `d563b8dc` |
| FINMETRIC F1/F2 | 指标引擎类型扩展 + 字典对齐 |

---

## 三、待处理事项与限制

| 问题 | 影响 | 当前处置 |
|---|---|---|
| **旧驾驶舱全视图 CI 未通过** | `39042517573`、`39041228479` cancelled；`39040652008`、`39038535194` failure | 旧包已归档；不反复重跑旧 SHA。新范围最终以本工作包的准确 SHA 做完整 CI 验收 |
| **主 checkout 有 4 个修改文件和 1 个未跟踪 YAML，且落后 63 个提交** | 内容可能与当前主线有交集，来源/归属尚未核实 | 保持原位，不覆盖、不暂存、不清理；先只读检查差异与用途，再确定安全集成方式；不要在该旧分支直接实施当前队首 |
| **仓库指令引用 `RTK.md` 但当前工作区未找到该文件** | 无法确认该引用是否缺失或过期 | 后续只读核实文件是否应在仓库/被忽略；不猜测其内容，也不擅自修改全局规则 |
| **README 截图采集工作流暂停** | 不得自动重新生成或采集产品截图 | 遵守暂停状态；验收只用现有素材或获准的本地方法，不触发该工作流 |
| **历史 CI 曾受长测时限取消** | README SHA `d51af7ad` run `39087270646` cancelled；文档更新 SHA `a331f030…` run `39090417203` success | 超时未复现；不增超时、不减覆盖、不改 CI 配置。后续每次实现提交都核验准确 SHA CI |
| **C 级条件 2（独立 oracle 0/14）** | 14 份报告无完整独立 oracle | 用户裁决 3A：如实 No-Go，后续迭代补 |
| **C 级条件 4（泛化留出全败）** | 小米 0/25、阿里 0/15、yunda 0/20、jdl 0/25 | 用户裁决 2A：不扩大盲评范围；适配器开发列后续迭代 |
| **P5 capex 符号** | `cainiao_private` 段 capex 映射与 damai_syn 同型问题（披露负值应 abs:true） | 登记为公开矩阵治理事项，本轮不动 |
| **rnd_exp 官方依据** | 原文不可得 | 外部材料受限结案；穷尽搜索后重启条件已列 |

---

## 四、下一步计划

### 当前下一步：实施单机运行结构

第 1、2 阶段及第 2 阶段准确 SHA CI 已完成。证据见[架构审计报告](docs/60_delivery/verification/2026-10-18--single-machine-architecture-dependency-audit-v1.md)。第 3 阶段依赖路径盘点已完成，但运行时改造未开始。按下列顺序串行推进；路线图状态变化先落盘、校验、提交推送，再执行代码：

1. 阅读已交付的[架构审计报告](docs/60_delivery/verification/2026-10-18--single-machine-architecture-dependency-audit-v1.md)，按调用点矩阵开始第 3 阶段；首个切片聚焦同步任务与本地内容存储接线，先写定向测试并明确单一验收边界。
2. 按工作包接入同步任务和本地文件存储，移除普通运行路径中的 Redis/Celery/MinIO；统一设置与本机启动入口。测试一律使用一次性隔离目标，PostgreSQL 32 个历史 revisions 保持不动。
3. 每个可验证切片先更新工作包/路线图，再测试、独立复核、提交并立即 push；检查实际运行时导入、环境变量、启动依赖均无 Redis/Celery/MinIO 残留。
4. 在停止 PostgreSQL/Redis/MinIO/Docker 的条件下，从空目录初始化并完成核心财务分析、报告与本地备份恢复；验证数据根目录与仓库/测试 fixture 分离。
5. 按工作包完成全站 A+C 视觉与真实数据完善、桌面/手机逐路由验收、完整测试与独立复核；核对最终提交对应的 GitHub CI SHA。同步 PROJECT_STATE、路线图、README、运行文档和 HANDOFF。
6. D055 工作包完成并经准确 SHA CI 验收后，才从唯一队列恢复 K2；K2 操作前只读核验 ObsidianWiki 状态。

第 2 阶段已完成的隔离验证证据（不是待做项）：

1. 一次性隔离 SQLite 库验证 schema、UUID/JSON、外键、Decimal 精度、事务回滚和单用户行为。
2. 最小样例串通财报装载、指标快照、FactTrace 查询、驾驶舱聚合、报告冻结与恢复。
3. 隔离本地内容目录验证 SHA 幂等、字节冲突、缺文件、下载与完整性错误。
4. 备份恢复到新的隔离目录并对账来源、报告和驾驶舱结果；未连接或重置常驻库。
5. SQLite 使用独立 Alembic 链；原 32 个 PostgreSQL revisions 未改动，保留为历史/测试链。

### 后续队列项：知识刷新 K0–K6

工作包：`docs/50_plans/work_items/KNOWLEDGE--refresh-v2.md`
规格：`docs/superpowers/specs/2026-09-17-static-knowledge-refresh-and-strategic-rebaseline-design.md`
实施计划（archived，取方法/命令）：`docs/superpowers/plans/2026-09-18-static-knowledge-refresh-and-strategic-rebaseline-implementation-plan.md`

**K0–K6 步骤概要**（状态以路线图和工作包为准）：
1. **K0 已完成**：Davybase 运行清单实现、微信历史批次严格验收和证据归档已推送。
2. **K1 已完成**：只读 allowlist scanner 已扫描三个非微信范围；566 篇需人工 triage，可执行候选 0，证据见工作包。
3. **K2 队首待启动**：Obsidian Git 冻结（14:30 锁定、15:00 候选、15:30 复验）
4. **K3** 用 accepted manifest 重建来源 registry/baseline/diff
5. **K4** 全量路由 + HIGH 精读
6. **K5** 构建 candidate + seal
7. **K6/战略裁决** 原子激活 release（须用户裁决，Agent 不可代签）

### D 之后（驾驶舱后续）

完成当前全视图工作包之前，不得开始下列工作。工作包关单后按唯一队列恢复 K2；暂不另开 cockpit 任务：
- 利润增长/盈利能力拆独立路由（当前复用总览 KPI）
- ECharts 视图层逐图增强（数据表为基线已成立）
- 行业参考包基准接入（v1.2 16 行业包已有，缺分位分布数据）

---

## 五、踩过的坑（重要——新会话必读）

### 多 worktree / cwd 漂移

1. **shell cwd 持久化跨命令**：上一条命令 `cd` 到了哪里，下一条命令就在哪里执行。**对策：每条 git 命令前自校验 `git branch --show-current`；多 worktree 场景用绝对路径 `git -C <path>`。**
2. **两个工作区同时操作导致文件版本错位**：worktree 里的文件和主工作区的文件是独立 checkout。曾在 worktree 里跑 `ruff check --fix` 但编辑了主工作区的文件（或反过来）。**对策：确定一个工作区作为本轮的唯一工作区，不混用。**
3. **分支误建到 worktree**：`git switch -c` 在 cwd 所在仓库执行，如果 cwd 在 worktree 里就建到 worktree 了。**对策：切分支前先 `pwd` 确认。**

### 测试与环境

4. **S3 环境变量**：`create_app()` 启动时校验 `s3_access_key`/`s3_secret_key` 等。本地跑测试必须设置：
   ```bash
   export DATABASE_URL='postgresql+psycopg://flow:flow_dev_only@localhost:5432/flow_test'
   export REDIS_URL='redis://localhost:6379/0'
   export S3_ENDPOINT_URL='http://127.0.0.1:9000'
   export S3_BUCKET='flow' S3_ACCESS_KEY='flow' S3_SECRET_KEY='flow_dev_only'
   export FLOW_DEV_ACTOR_ID='flow-dev-bp'
   ```
5. **测试连常驻库事故已修**（`b60c51b`）：conftest 默认切 `flow_test`；但如果 Docker 不在线（`docker info` 失败），PostgreSQL 5432 拒连，需要先 `open -a Docker` + `make infra-up`。
6. **测试文件多轮字符串手术易留残留**：本次 C-3 的 `test_cockpit_modules.py` 经多轮 sed 后留下 `-> SimpleNamespace: -> SimpleNamespace:` 语法错误。**对策：复杂改动直接重写整个文件而非增量 patch。**
7. **CI ruff 与本地 ruff 版本可能不同**：本地 `uv run ruff check` 全绿但 CI 报 `E501`（行长度）。**对策：提交前在 `services/api/` 目录下跑 `uv run ruff check src tests migrations`（CI 的确切命令）。**

### 数据一致性

8. **canonical 月份常量**：`canonical.py` 曾本地复制月份常量导致批次窗口错位。已改为从 `profile.py` 唯一导入。**教训：月度合同只在 profile 定义一次，别处 import。**
9. **发行版工作簿语义指纹**：重刷发行版后 xlsx 的语义指纹会真实变化（数值变了），**不可**习惯性 `git checkout` 回退——只有 zip 容器噪音（时间戳）才该回退。
10. **毛利校准基准行**：行间相对结构按比例缩放后，尾差并入校准基准行。基准行选择错误会导致年度合计偏差——基准行必须在循环外确定（如最大毛利行），且在循环内 `continue` 跳过常规缩放。
11. **`_family_month_revenues` 尾差**：三业务族分摊后族之和可能偏差 0.0002——需在最大族吸收尾差保证月度目标精确闭合。

### 前端 / Next.js

12. **Server Component 不能传函数 prop 给 Client Component**：page.tsx（server）向 module-page.tsx（client）传 `fetcher` 函数会触发 Next.js SSR 错误。**对策：client 组件自己 import flowApi 取数，page 只传数据属性（moduleId/title）。**
13. **`const module = ...` 触发 `@next/next/no-assign-module-variable`**：ESLint 规则禁止赋值给变量名 `module`。**对策：改名为 `data` 或 `mod`。**
14. **`"use client"` 页面不能导出 `metadata`**：Next.js 要求 metadata 只在 Server Component 导出。**对策：page.tsx 保持 server component，client 逻辑放独立组件文件。**
15. **ECharts 是独立依赖**：worktree 的 node_modules 可能缺 echarts（早期 lockfile 未含）。**对策：worktree 里先 `pnpm install --frozen-lockfile`。**

### CI / 构建

16. **CI ruff 版本 / 规则集与本地可能不同**：本地全绿但 CI 报错。**对策：提交前跑 CI 的确切命令：`cd services/api && uv run ruff check src tests migrations && uv run mypy src`。**
17. **新增 CI job 必须同步 `test_ci_gate_inventory.py`**：`EXPECTED_GATES` 集合和 `test_every_ci_gate_has_an_explicit_timeout`（timeout-minutes 必填）都要更新。
18. **CI 失败时先拉日志定位根因再修**：`gh api repos/davyzhong/FLOW/actions/jobs/<jobId>/logs --allow-escape-sequences | grep -a 'error\|FAILED'`。不要凭 job 名猜测。
23. **FLOW verification 文档状态受 M6 校验**：合法状态为 `draft`、`verified`、`superseded`、`archived`；`active` 会让 M6 失败。CI 最终结案前用 `draft`，全验收通过后才改 `verified`。
24. **契约升级要同步更新强类型 fixture**：`CockpitModuleChart` 新增必填字段后，组件测试 fixture 若未同步会导致 `pnpm -r typecheck`、Next production build、依赖该构建的 smoke 全失败；本轮补上 `analysis_question`、`fact_classes`、`snapshot_id` 等字段后 static-web/smoke/module-boundaries E2E 通过。
25. **Playwright 默认地址不是当前隔离浏览器端口**：项目配置默认 `127.0.0.1:13100`；本轮现成隔离服务的 Web 在 `3461`。复跑目标全视图用例需显式 `PLAYWRIGHT_BASE_URL=http://127.0.0.1:3461`，先核实端口对应当前 worktree 和隔离账套，不能退回常驻数据库。

### Git / 文档

19. **`git push -q` 静默失败**：如果远端有新提交（如截图 bot），push 会 rejected 但 `-q` 吞掉输出。**对策：push 后 `git fetch && git rev-parse origin/<branch>` 确认远端 SHA 与本地一致。**
20. **docs/ 新增 .md 必须 unique doc_id**：复制文件改内容但忘改 `doc_id` 会触发 m1 重复检查。
21. **worktree 的 `node_modules` 可能过时**：worktree 共享代码但不共享 `node_modules`。在 worktree 里跑前端测试前先 `pnpm install --frozen-lockfile`。
22. **管道 `| tail -N` 会吃掉前置命令的退出码**：`cmd | tail` 永远返回 tail 的退出码（0）。**对策：需要检查退出码时不用管道，或用 `set -o pipefail`。**

---

## 六、关键命令速查

```bash
# 环境启动
open -a Docker && make infra-up

# 后端测试（必须从 repo 根或 services/api 运行）
cd services/api
export DATABASE_URL='postgresql+psycopg://flow:flow_dev_only@localhost:5432/flow_test'
export REDIS_URL='redis://localhost:6379/0'
export S3_ENDPOINT_URL='http://127.0.0.1:9000' S3_BUCKET='flow'
export S3_ACCESS_KEY='flow' S3_SECRET_KEY='flow_dev_only'
export FLOW_DEV_ACTOR_ID='flow-dev-bp'
uv run pytest -q tests/ --ignore=tests/e2e

# 静态检查（CI 确切命令）
uv run ruff check src tests migrations && uv run mypy src

# 前端
cd apps/web && pnpm typecheck && pnpm test && pnpm lint && pnpm build

# 契约再生
cd /Users/qiming/workspace/FLOW && make contracts && make contracts-check

# 文档门禁
python3 scripts/check_docs.py --phase m1

# 计划视图再生（路线图改动后必须跑）
python3 -c "
import sys; sys.path.insert(0, '.')
from scripts.documentation.plan_views import write_views, check
from pathlib import Path
write_views(Path('.'))
print(check(Path('.')) or 'OK')
"

# 发行版重建
uv run --project services/api python scripts/build_damai_demo.py --output fixtures/damai
uv run --project services/api python scripts/build_enterprise_data_package.py build
uv run --project services/api python scripts/build_enterprise_data_package.py verify

# 来源登记重建
uv run --project services/api python scripts/build_damai_source_registry.py
uv run --project services/api python scripts/build_damai_source_registry.py --check

# 盲评复跑
FLOW_HOLDOUT_RUN_ID=<run-id> uv run --project services/api python scripts/holdout_u4_run.py

# e2e
bash scripts/test_damai_demo_e2e.sh
```

---

## 七、权威文件索引

| 文件 | 作用 |
|---|---|
| `docs/50_plans/CURRENT_ROADMAP.md` | **唯一主线**（状态 + 队列） |
| `docs/00_start_here/PROJECT_STATE.md` | 唯一 current state |
| `docs/50_plans/work_items/COCKPIT--cfo-dashboard-implementation.md` | 驾驶舱工作包（completed） |
| `docs/50_plans/work_items/FINMETRIC--financial-metric-catalog.md` | 指标目录工作包（completed） |
| `docs/50_plans/work_items/U04--independent-oracle.md` | U04 工作包（completed） |
| `docs/50_plans/work_items/KNOWLEDGE--refresh-v2.md` | 知识刷新工作包（K0/K1 完成，K2 队首待启动） |
| `docs/60_delivery/verification/2026-10-16--u04-blind-review-rerun-v1.md` | 盲评复评验证文档 |
| `docs/60_delivery/verification/2026-10-16--cockpit-51-chart-coverage-mapping-v1.md` | 51 图覆盖映射 |
| `docs/60_delivery/verification/2026-10-12--damai-source-baseline-audit-v1.md` | 来源基线审计 |
| `config/damai/source_facts_v1.yaml` | 来源事实登记（325 条） |
| `config/metrics/damai_demo_metric_coverage_v1.yaml` | 指标覆盖矩阵（32/50×2） |
| `config/statements/item_alias_map_v1.yaml` | 报表行名别名映射（damai_syn 段） |
| `services/api/src/flow_api/cockpit/modules.py` | 模块构建器（8 个 build_* 函数） |
| `services/api/src/flow_api/cockpit/service.py` | 投影服务（KPI/趋势/结论/行动项） |
