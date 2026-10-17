---
doc_id: FLOW-HANDOFF-STRATEGY-20260912
title: FLOW 项目交接文档
doc_type: navigation
status: current
version: 7.7
created_at: 2026-09-12
updated_at: 2026-10-17
owner: FLOW
applies_to: repository
---

# FLOW 项目交接文档

> 本文档是下一位 Agent 接手的唯一入口。项目唯一权威状态以 [CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md) 为准；本文档提供接手上下文、踩坑记录和下一步操作指引。

---

## 一、当前任务

**当前任务：收尾 CFO 驾驶舱全视图数据与图表完整性改造**。阶段 1–4 已完成。阶段 5 的本地隔离浏览器验收、截图报告、全视图 API/页面逐项核对、独立复核、M1/M6/契约/相关测试均已完成；九页共 25 个 ECharts 画布，桌面/手机 18 组路由视口通过。六个模块的全部图表 series、waterfall steps、formula_card 的 DSO/DIO/DPO/CCC，以及盈利能力页全部期间指标均逐值对 API；总览四项 CFO 指标与行动项可见，来源行深链、键盘来源披露、行动项审计和 403 拒绝态均有验收。独立复核无剩余 P1/P2。演示账套 `flow_cockpit_visual_20261017a`，manifest SHA-256 `6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed`；月度/组织分配标记 synthetic allocation，未连接常驻业务库。

代码提交 `b2ee037375ff0949a1dec442bd3ac4feb6bb078d` 已推送；报告状态修正提交 `0b9b12f3e0138898ff719d2f1db378cd793b9d5f` 已推送。最新准确 SHA CI run `39041228479`（https://github.com/davyzhong/FLOW/actions/runs/39041228479）仍在执行，最后核验时仅 `integration`、`intake-e2e`、`data-contract` 运行中，其余完成 job 全绿；因此工作包仍为 active、浏览器验收报告仍为 draft，不能宣称最终通过。旧代码 SHA run `39040652008` 的 `static-python` 曾因该报告 frontmatter 写 `status: active` 被 M6 拒绝；已改为 `draft`，最新 run 的 `static-python` 已通过。阶段 2 准确 SHA `09ba5722ec3e8075a3483223df4c81fe5cdaa9fa` CI run `39035163288` 为 18/18 成功。知识刷新 K2 顺延至本工作包关单后。[计划工作包](docs/50_plans/work_items/COCKPIT--all-views-data-and-visual-completion.md)、[浏览器验证报告](docs/60_delivery/verification/2026-10-17--cockpit-all-views-visual-browser-verification-v1.md)。

**CFO 驾驶舱盈利分析与图表缺口补全已完成**。本分支新增盈利能力页面 `/cockpit/profitability`、只读 API 与冻结时杜邦指标载荷；提供净利率、ROE、总资产周转率、权益乘数、两期比较、勾稽提示、指标/报告/来源财报行深链。图表复用 ECharts；旧快照或缺少期初数据时明确显示 unavailable。前端 36 个测试文件/184 项通过、typecheck/build 通过；lint 零错误，有一条既有 TanStack Table 警告；后端隔离定向测试 12 项、Ruff、mypy 通过；隔离账套核验 19/19、可见性矩阵 162 项无失败、浏览器全旅程 16/16 通过，真实页面截图见[浏览器验收记录](docs/60_delivery/verification/2026-10-17--cockpit-profitability-browser-verification-v1.md)。CI 首轮发现重复 seed 会新增两份 Objective 快照；修复归一化行 UUID 不稳定性后，回归测试 10 项通过，准确 SHA `08aa4cd02247f995bc990d92c8f34f5a1829afa1` 的 GitHub CI run `38996089002` 为 18/18 job success。contracts、plan views、links 与 M1 通过。代码与修复提交分别为 `5817efcf`、`08aa4cd0`，均已推送。工作包/设计/计划见 [工作包](docs/50_plans/work_items/COCKPIT--visual-analysis-expansion.md)、[设计规格](docs/superpowers/specs/2026-10-17-cfo-cockpit-visual-analysis-expansion-design.md)、[实施计划](docs/superpowers/plans/2026-10-17-cockpit-visual-analysis-expansion.md)。独立审查发现的单位误标和来源行下钻缺口均已修复。

**当前唯一队列：14 项，已完成 7、实际执行中 1（驾驶舱全视图）、队首待启动 0、排队 4（含顺延的 K2）、暂停 1、外部材料受限 1。当前唯一执行项为驾驶舱全视图；K2 待本工作包完成后先只读核验 ObsidianWiki 状态并执行门禁。K0 已在 Davybase 分支 `codex/knowledge-run-manifest-k0` 推送实现 `172a099`、证据 `94fc05d`、交接 `eb8c3d0`；严格复算 1,265 输入、1,239 成功、2 待复核、24 过滤，32 篇/512 图样本对账通过，872 项测试与 Ruff 通过。ObsidianWiki `main` `e04d6833` 有 1,365 条既存变化且范围指纹为 `0a42346d…c7f7`，继续只读保护；`CURRENT_RELEASE` 保持 `flow-knowledge-2026-09-12.1`。K1 扫描器实现 `a0c2e6762c2c212baa23f4ea4855dde5399c37a6`、证据 `a914830`；扫描 1,601 篇，566 篇人工 triage、0 可执行候选。K2 冻结器实现提交 `699e5c6`（13 项专项/892 项全量测试通过；独立复核发现的发布校验绕过已修复）；README 截图工作流 run `38953998448` 成功，自动截图更新 `b051c35` 已同步。截图工作流不替代 GitHub CI。详情见[知识刷新工作包](docs/50_plans/work_items/KNOWLEDGE--refresh-v2.md)。

用户四项裁决（2026-10-16）：
1. **L0 挂 CI（选项 C）**：非阻断 `l0-baseline` job（continue-on-error: true），失败仅作信号灯。
2. **盲评复评范围（选项 A）**：仅旧三样本（顺丰/腾讯/中通）。
3. **C 级维持 6 条件不变（选项 A）**：诚实标准，做不到如实 No-Go。
4. **ZTO 立即恢复（选项 C）**：`wip/zto-integration-20260929` 已解封合并。

---

## 二、已完成的内容

### 本会话（2026-10-17）交付清单

| 交付 | 提交 | 验证/状态 | 要点 |
|---|---|---|---|
| CFO 全视图页面、来源联动和完整浏览器验收 | `b2ee037375ff0949a1dec442bd3ac4feb6bb078d` | 本地通过；CI run `39040652008` 的 M6 因报告状态 `active` 失败，已在下一提交修正 | 九视图 25 个 canvas；桌面/手机 18 组通过；18 张截图；所有模块 series/waterfall/formula-card 与盈利明细逐项核对 API；截图报告见下方索引 |
| 验收报告状态修正 | `0b9b12f3e0138898ff719d2f1db378cd793b9d5f` | 已推送；CI run `39041228479` 仍在执行 | verification 状态改为 `draft` 以满足 M6；CI 全绿后更新为 `verified` 并完成工作包关单 |
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

## 三、卡住的问题

| 问题 | 影响 | 当前处置 |
|---|---|---|
| **本轮准确 SHA CI 尚未收敛** | 最新 run `39041228479` 的 integration、intake-e2e、data-contract 最后核验时仍在运行 | 继续检查同一 run，不要启动重复实现；若失败先按具体 job 日志定位。全绿后更新报告为 `verified`、工作包/路线图/HANDOFF 状态，跑 M1/M6 后提交并推送；新 docs SHA CI 仍需核验 |
| **已修复的文档状态失败** | 代码 SHA `b2ee0373` 的 CI run `39040652008` 因 verification 文档不允许 `status: active` 而 M6 失败 | 最新 `0b9b12f3` 已改为 `draft`，本地 M6 与最新 CI static-python 通过；只在 CI 全绿后改为 `verified` |
| **route_policy 测试本地失败** | `test_openapi_probe_matches_tsv_two_way` 在本地 main 也失败（CI 通过） | 本地环境项（缺 S3 环境变量时 `create_app` 设置校验失败）；带完整 env 跑即绿。不阻塞 |
| **C 级条件 2（独立 oracle 0/14）** | 14 份报告无完整独立 oracle | 用户裁决 3A：如实 No-Go，后续迭代补 |
| **C 级条件 4（泛化留出全败）** | 小米 0/25、阿里 0/15、yunda 0/20、jdl 0/25 | 用户裁决 2A：不扩大盲评范围；适配器开发列后续迭代 |
| **P5 capex 符号** | `cainiao_private` 段 capex 映射与 damai_syn 同型问题（披露负值应 abs:true） | 登记为公开矩阵治理事项，本轮不动 |
| **rnd_exp 官方依据** | 原文不可得 | 外部材料受限结案；穷尽搜索后重启条件已列 |

---

## 四、下一步计划

### 当前下一步：结案驾驶舱唯一队首，再继续知识刷新 K2

1. 先查询 `gh run view 39041228479 --json status,conclusion,jobs`；继续观察该准确 SHA，不要把旧 SHA 的结果算作本轮结果。
2. 若 CI 出错，逐个读取失败 job 日志（见本节“CI / 构建”命令）并修复根因；每次 GitHub commit 后立即 push。若全部通过，记录所有 job 结论及准确 SHA。
3. 将浏览器核验报告 `status: draft` 改为 `verified`，更新 `commit_refs` 加入最终通过 SHA/run；同步更新驾驶舱工作包、唯一主线 `CURRENT_ROADMAP.md` 与本文件，准确结案队列状态，并重跑 `python3 scripts/check_docs.py --phase m1`、`--phase m6`、契约/相关测试。
4. 提交并 push 文档状态更新后，再核验该最终 HEAD SHA 对应的 GitHub CI；之后按唯一队列恢复知识刷新 K2，先只读核验 ObsidianWiki 工作树状态。

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
