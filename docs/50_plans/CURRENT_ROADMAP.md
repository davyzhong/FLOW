---
doc_id: FLOW-PLAN-CURRENT
title: 当前路线图（唯一）
doc_type: plan
status: active
version: 17.29
created_at: 2026-09-12
updated_at: 2026-10-27
owner: FLOW
depends_on: [FLOW-SPEC-V1-DESIGN-001]
acceptance_refs: [roadmap-unique-invariant]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: planning
supersedes: [FLOW-PLAN-UNIFIED-000, FLOW-PLAN-OPS-000]
superseded_by: null
---

# 当前路线图（唯一主线）

> **状态速览（2026-10-27）：** 唯一队首 = K 轨 K3 全量逐条语义路由，第 143 批已完成，下一单一动作是**第 144 批**（从第 143 批末尾 `SRC-LOCAL-v1-2ed70ed7efd2f046d3dd` 之后首个未审 source_id 开始）。队列 16 项：完成 10 / 队首执行中 1 / 排队 3 / 暂停 1 / 外部条件受限 1。K3 进度：coverage 9,673 条 = routed 910 / filtered 496 / pending_review 8,267；accepted snapshot `obsidianwiki-20261026T005516+0800-d601b4d5`（manifest SHA `593715c8…`，可写句柄 0）；五个 locator-only 例外保持待审；ObsidianWiki 严格只读，`CURRENT_RELEASE` 不变。**环境已收敛（用户指令）：全部活动分支合并进 main，远端仅剩 `main`；main 基线 `b70de445`（含视觉语言统一 PR #5、K3 批次 129–133、路线图规整 v17.17、指标资料 PR #6 与 publishing-golden 字体断言平台化修复 `775f283a`）；本地保留 2 个含未提交内容的 worktree 与 1 个未合并 wip 分支（`codex/frontend-consistency-remediation`），其余已清理。本版（v17.19）补充环境收敛记录；v17.17 规整结构不变。**

## 战略目标（唯一目标清单，当前有效四项）

| # | 目标 | 状态 | 口径 |
|---|---|---|---|
| G1 | 单机单用户验证原型（D055） | ✅ 已交付 | 可启动/可装载重置演示业务/图表下钻追溯/分析导出报告/备份恢复/离线浏览，全部按验收结案（7a.1–7a.8 + 视觉语言统一）；原型使用 synthetic 演示数据 |
| G2 | 第二代知识刷新与战略重基线（K0–K6） | ▶ 进行中（唯一活跃工程线） | K0–K2 完成；K3 全量路由第 133 批；K5 候选封存与 K6 用户裁决未到，`CURRENT_RELEASE` 保持 `flow-knowledge-2026-09-12.1` |
| G3 | 公开财报 C 级出口 | ⏸ No-Go 维持（长期） | 条件 2（完整独立 oracle 0/14）、条件 4（泛化留出全败）未满足；用户裁决不扩大盲评；证据工作归长期队列 |
| G4 | 企业内部月度工作台 + 四级真实验证 | 🔒 gated | 依赖 G3 通过 + 真实企业数据 + 连续 3 个真实月度周期、人工基准、盲评与工时门槛 |

已终结的历史目标不单列：早期「D052–D054 公开模块先行」路径已被 2026-10-18 D055 转向与 2026-10-24 原型结案吸收；完整演进见文末时间线与折叠历史。D055 结案边界明确：账龄独立切片、公开 C 级、知识刷新、真实企业试点与行业扩张**不在原型完成范围**，不得为美化原型重开。

## 唯一执行队列（16 项，严格串行；编号保持历史可追溯）

| 原编号 | 事项 | 状态 | 下一步 / 结案证据 |
|---|---|---|---|
| 12 | 可复用视觉语言提炼与 FLOW 全项目视觉统一 | completed（2026-10-26） | 全部验收结案并合入 main（PR #5 → merge `5d2b77f6`）；唯一遗留：原生浏览器 200% 缩放待设备解锁补验（外部条件受限结案） |
| 13 | 清理已合入 main 的历史远端分支 | completed（2026-10-25；10-27 增补） | 10-25 删 15 个旧分支；10-27 二轮：合并 PR #5/#6 后删除全部活动分支（含 ZTO），远端仅剩 `main`；本地删 17 分支 + 6 worktree，保留 2 个含未提交内容的 worktree 与 1 个未合并 wip 分支 |
| 0 | CFO 盈利分析与图表补全 | completed | `08aa4cd0` 准确 SHA CI 18/18；后续验收由 7a 承接 |
| 0a | 驾驶舱数值格式治理 | completed | `1a71e33f` 准确 SHA CI 通过 |
| 7a | 单机原型与全视图视觉升级 | completed（2026-10-24） | PR #3 merge `b2a1bf22`，run 40092106547 为 28/28 success |
| 1 | 组织与经营账套初始化包 | completed | 历史 full/business 验证；SQLite 操作由 7a.6 复验 |
| 2 | 大麦数据后体验收口 | completed | `0144bad4` 准确 SHA CI 通过 |
| 3 | 公开财报样本/证据审计 | completed（No-Go 审计） | 证据不足裁定已交付；C 级门禁本身未通过，归 G3 |
| 4 | U04 解析与盲评复评 | completed（限定样本） | 旧三样本 199/199；不等于全部报告 oracle 完成 |
| 5 | C 级质量基准与 Go/No-Go | completed（裁定 No-Go） | 维持 No-Go；解锁路径归 G3 长期 |
| 6 | P3 真实数据/来源与行业扩张 | 暂停 | ZTO 已于 2026-10-16 恢复合并；其余扩张等真实财报到料或用户指令 |
| **7（原 K）** | **第二代静态知识刷新** | **队首执行中：K3** | **下一动作 = 第 144 批**（143 批完成：24 条审阅、12 routed / 12 filtered，coverage routed 910 / filtered 496 / pending 8,267）；之后 coverage 闭合 → 知识综合 → 独立 reader → K5 seal → K6 用户裁决（Agent 不可代签） |
| 8 | rnd_exp 官方依据核验 | 外部条件受限 | 原文不可得结案；穷尽搜索记录与重启条件已登记，不得伪造核验 |
| 9 | U09/O05 真实内部试点 | 排队（blocked） | 需真实企业数据与质量门槛；技术原型不冒充真实试点 |
| 10 | U10 V1.1 证据决策 | 排队（blocked） | 依实际证据逐项 go/hold，不作为原型无限开发项 |
| 11 | 内部月度工作台与真实周期验收 | 排队（gated） | 真实连续 3 周期 + 人工基准 + 盲评 + 工时比较；模拟数据不能替代 |

## 工作包登记表（治理登记，每包一行；状态以包 frontmatter 为准，禁止从历史段落领取）

| 工作包 | 状态 | 一句话口径 |
|---|---|---|
| [CFO 驾驶舱产品化](work_items/COCKPIT--cfo-dashboard-implementation.md) | **completed** | 批次 A–D + FINMETRIC F1–F4 + 51 图映射全交付 |
| [盈利分析与图表补全](work_items/COCKPIT--visual-analysis-expansion.md) | **completed** | `/cockpit/profitability` 杜邦树与来源深链 |
| [视觉补全与数值格式](work_items/COCKPIT--visual-completion-and-number-format.md) | **completed** | 整数订单/两位小数/单位统一 |
| [CFO 全视图数据与图表改造（旧）](work_items/COCKPIT--all-views-data-and-visual-completion.md) | **archived** | 九页/25 图为回归基线；禁止独立执行 |
| [财务指标目录](work_items/FINMETRIC--financial-metric-catalog.md) | **completed** | 指标引擎类型扩展 + 字典对齐 + F3/F4 |
| [单机原型与全视图视觉升级](work_items/FLOW--single-machine-visual-prototype.md) | **completed** | 7a.1–7a.8 结案；工作包 `do_not_execute` |
| [可复用视觉语言与全项目统一](work_items/FLOW--portable-visual-language-and-full-project-restyle.md) | **completed** | 视觉包 + 全页面统一；PR #5 |
| [历史分支清理](work_items/FLOW--merged-branch-cleanup.md) | **completed** | 15 个已合入分支删除 |
| [U08 生产就绪](work_items/U08--production-readiness.md) | **completed** | u8-final-baseline 冻结 |
| [U04 独立 oracle](work_items/U04--independent-oracle.md) | **completed** | 盲评复评 199/199 |
| [S01 边界、事实合同与安全门禁](work_items/S01--post-u8-boundary-contract-security.md) | **completed** | 安全规格 V1.1 → V1.1.1 |
| [大麦完整财年演示数据](work_items/DAMAI--full-year-demo.md) | **active** | FY2022/FY2023 披露事实层固化；仅随产品需求增量维护，不与 K3 并行 |
| [UX 剩余体验收口](work_items/UX--post-damai-experience-closeout.md) | **completed** | Gate1/Gate5 关闭 |
| [组织账套初始化包](work_items/ORG-LEDGER--enterprise-initialization-package.md) | **completed** | ORG-LEDGER v2 重版 |
| [知识刷新 K0–K6](work_items/KNOWLEDGE--refresh-v2.md) | **active** | 队首：K3 第 144 批 |
| [公开财报 C 级出口](work_items/PUBLIC--c-level-exit-protocol.md) | **active** | No-Go 维持；条件 2/4 归长期 |
| [溯源/重述/只读 MCP](work_items/PUBLIC--provenance-restatement-mcp.md) | **completed** | 溯源页锚 + supersedes 链 + 只读 MCP |
| [数据扩张与行业基准](work_items/PUBLIC--data-expansion-benchmarks.md) | **active** | 10× 性能基线已交付；扩张等真实财报 |
| [AI 问数 v1](work_items/PUBLIC--ai-qa-v1.md) | **completed** | 94 问评测 100% 命中、拒答零误答 |
| [U09/O05 授权内部试点](work_items/U09-O05--authorized-internal-pilot.md) | **blocked** | 等 C 级 Go + 真实企业数据 |
| [U10 V1.1 证据决策](work_items/U10--v1-1-evidence-decision.md) | **blocked** | 等证据门槛；轮到即整理 go/hold |

## 待验证清单（收缩后仅 4 项活跃）

| 验证项 | 归属 | 状态 |
|---|---|---|
| K3 全量语义路由（pending_review 8,506 条）+ coverage 终态闭合 | G2 | 随批次推进，第 134 批起 |
| K3 知识综合 + 独立 reader 复核 | G2 | 路由闭合后执行 |
| K5 candidate seal → K6 原子激活 | G2 | 须用户正式裁决，Agent 不可代签 |
| 原生浏览器 200% 缩放补验 | G1 唯一遗留 | 外部条件受限：待设备解锁且有可控缩放工具；390/360 CSS px 不替代 |

**已关闭的验证（不再挂账，证据见 docs/60_delivery/verification/）**：C 级六条件（已裁决 No-Go，条件 2/4 归 G3 长期）；视觉矩阵（20 路由×3 视口 60/60、Axe 桌面 20 路由零违规、可见性 164/164、Playwright 17/17）；7a 单机验收（SQLite 旅程、离线零外呼、备份恢复、verify 19/19）；大麦来源勾稽（IFRS 12 恒等式 + 明细↔披露年度聚合零差异）；U04 旧三样本盲评 199/199。

## 演进时间线（压缩版）

| 日期 | 事件 |
|---|---|
| 2026-09-13 | D052–D054 战略定调：公开财报模块先行 → 内部工作台 → 四级验证 |
| 2026-09-29 | C 级证据审计 No-Go；U04 盲评复评提队首 |
| 2026-09-30 ~ 10-16 | CFO 驾驶舱产品化批次 A–D + FINMETRIC F1–F4 + 大麦来源登记/时间线迁移 + U04 盲评 199/199 + L0 挂 CI |
| 2026-10-18 | D055 转向：单机单用户验证原型（SQLite + 本地目录，移除 Redis/Celery/MinIO，A+C 视觉） |
| 2026-10-24 | 7a.1–7a.8 结案合 main（PR #3，CI 28/28） |
| 2026-10-25/26 | 视觉语言统一结案（PR #5）；K2 即时快照 accepted；K3 语义路由启动 |
| 2026-10-27 | K3 路由至第 133 批；路线图结构性规整（本版 v17.17） |

知识库增量扫描、指标库行业包、竞对五维矩阵及 O-01/O-02 地基均为已完成证据或设计输入，不再作为待办；Davybase 新增图片批次及非微信覆盖属于第 6 项的未完成工作，不能据早期扫描记录判为完成。

<details>
<summary>历史状态段落全文（2026-10-12 ~ 2026-10-27 过程记录；只读归档，不作为当前状态）</summary>

> **2026-10-27 最新状态：** D055 单机原型 7a.1–7a.8 已合入 main；视觉语言包及全项目页面、图表、报告/离线输出和 README 视觉统一已完成。路线图仍为 16 项：完成 10、实际执行中 0、队首待启动 1（K 轨 K3）、排队 3、暂停 1、外部条件受限 1。视觉覆盖验收：隔离 synthetic manifest `6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed` 下验证器 19/19、可见性矩阵 164/164（154 HTTP 200、10 预期拒绝、0 失败）、Playwright 17/17；20 路由×3 视口 60/60 与 Axe 桌面 20 路由零违规仍对应应用 SHA `01e8e25dd426ed43ad6a2cad76544bbbe623eb99`。最新 E2E 断言修复已提交于 `d01daa11`，独立复核无 P1/P2，`git diff --check` 通过。原生浏览器 200% 缩放因 Mac 锁屏且当前工具不能操作 Edge 工具栏，未直接验收；390/360 CSS px 证据不替代。按外部条件受限替代结案，待设备解锁且可控工具可用时补验。当前分支 `codex/flow-visual-language` / PR #5；工作包结案文档随后提交并以准确 SHA 查询 GitHub CI。视觉包证据见[覆盖验收](../60_delivery/verification/2026-10-24--flow-visual-language-coverage-v1.md)。下一唯一事项 K 轨当前子步为 K3 全量逐条语义路由：当前 accepted snapshot `obsidianwiki-20261026T005516+0800-d601b4d5`（manifest SHA `593715c832a538d9ba83df4e077b8dd9bace24f40d3c0d5262fc3779b20f0e77`）候选/复验一致、内容 SHA `c84efd671e2b90e4f69152c3dd04a570d9c378d08fb7a3cb97b86e322f123df0`、可写句柄 0。新 snapshot 与之前 K3 基线内容指纹一致；registry/baseline/delta 已绑定最新 snapshot 并重复构建一致。K3 处于会话间队首待启动状态；全量路由已完成至第133批，coverage 为 routed 755、filtered 412、pending_review 8,506；下一动作是第134批。当前有五个 locator-only / pending-review 例外（新增 `SRC-LOCAL-v1-0de553da4d8d857b90d3`；其他包括 `SRC-LOCAL-v1-00625bae4e08042539d1`、`SRC-LOCAL-v1-0428a240b0361157ffa1`、`SRC-LOCAL-v1-057cabfb9baca9f47c44` 和 `SRC-LOCAL-v1-0bd79ce2c2d600301852`），均未使用范围外内容或链接标题推断。HIGH 全读及 MED/LOW 双审已完成。旧 10-19 baseline/diff 保留为历史结果。ObsidianWiki 和 `CURRENT_RELEASE` 保持不变。

> 当前完结目标依据 D055：交付本机单用户可启动、可加载/重置演示业务、可看丰富 CFO 图表、可下钻追溯、可分析和导出报告、可备份恢复、可离线浏览的验证原型。公开 C 级、知识刷新、真实企业三周期仍未完成，保留在长期队列，不作为本原型无限延期的理由。

> **2026-10-24 连续收尾接管授权：** 用户已要求按 `CURRENT_ROADMAP` 顺序连续执行路线图 7a.1–7a.8，完成可做事项后进入收尾。范围和跳过规则已落盘：外部长等待先诊断并尝试安全替代，仍无进展则如实记为跳过/未验证；不得绕过红线或虚报验收。

> **2026-10-21 历史状态：单机启动/本机验收、门禁拆分已完成；7a 收敛全视图视觉差距和文档治理。** 费用页 KPI 修复 SHA `87e1829d32d6281fe1dad7ee978f39e0c1b4e5f2` 的准确 SHA CI run `39451521454` 因后续提交已取消；期间费用堆叠对比提交 SHA `65d7dc61d18e0ebe2f2bc582c3f99e4bbe3e4d5d` 的 CI run `39453419044` 因后续状态提交取消，汇总 job 失败由分片取消导致、非断言失败；状态提交 SHA `a71cb28eedc6bca8019e7552fe7b2348f28f1239` 对应 run `39453752316` 已 28/28 jobs success；最新文档提交 SHA `21b650a108e7d906338454d661b7cfe178e13487` 对应 run `39457446117` 已 28/28 success。本轮修复 390px 费用页五项 KPI 栅格并新增隔离响应 fixture E2E；驾驶舱期间费用图改为已披露两年四项费用堆叠对比。前端 199/199、typecheck、生产 build 通过；lint 零错误、3 条既有警告；文档 M1/M2/M6 通过。六个主题模块 390px 实测 ready、有图表且无横向溢出。原 284 项/66 文件集成测试分片零遗漏、零重复，准确 SHA `368a01902124351401d73dc9329800d7f00f3953` / run `39349190031` 为 28/28 success。截图位于本机 `/tmp/flow-cockpit-visual-20261020/`，没有恢复截图自动化工作流。

> **2026-10-20 main 基线（历史快照）**：当时 main HEAD `5ed61af91ea4c1c2a2078fd654accf671ba805ba` 对应 GitHub Actions run `39119888132`，18/18 jobs success；唯一队列为 14 项（完成 7、执行中 0、队首待启动 1、排队 4、暂停 1、外部条件受限 1），队首为 D055 单机原型架构简化与全视图视觉升级。此快照早于本分支后续进展，不代表当前状态。

> **2026-10-19 工作包 7a 第 4 阶段关闭，K2 转为唯一队首**：4.6 指标期间、方向、单位与来源链接已修复，独立审查无 P1/P2；4.7 隔离真实数据验收覆盖 9 个 CFO/数据页面及 165 项浏览器回归。代码 SHA `65a087063ad67702172430702590083f8991a884` 的 run `39139310634` 18/18 success；最终文档 SHA `a1fe50ef4e71298767b4fe8e22ab47d780f28552` 的 run `39140563811` 18/18 success。随后 2026-10-24 7a 收尾批次（7a.1–7a.8）重开并结案，见队列第 7a 行。

> **2026-10-18 用户确认原型方向并完成队首重规划**：当前交付定位调整为单机单用户验证原型；用户选择 SQLite 单文件 + 本地文件目录、移除 Redis/Celery/MinIO，并确认 A 主风格 + C 报告叙事。旧驾驶舱全视图工作包归档，其九页/25 图与桌面/手机实测作为回归基线。旧 CI 实际结果为：`39042517573`、`39041228479` cancelled；`39040652008`、`39038535194` failure；不得描述为 CI 全绿。第 1 阶段现状/影响审计、第 2 阶段 SQLite/本地内容存储（准确代码 SHA `b0e1eb787592ff84bc4c19873a1e61cad1f9f3e6` 的 run `39099573268` 18/18 jobs success）、第 3 阶段同步处理/本地内容寻址存储/单一启动入口（最终 SHA `20a511f66e4bfe65ab02edc091c7b49e2cbcbe67` 的 run `39125304357` 18/18 success）均完成关闭。第 4 阶段 4.1–4.7 结案（4.1 覆盖矩阵、4.2 数据盘点、4.3 组件交互方案、4.4 图表适配、4.5 发行包血缘与整数件量、4.6 指标展示、4.7 浏览器验收 165 项），代码 SHA `65a08706` 与文档 SHA `a1fe50ef` CI 均 18/18 success。

> **2026-10-17 用户调整队列并启动 CFO 全视图实施**：阶段 1–5 完成，阶段 2 准确 SHA `09ba5722ec3e8075a3483223df4c81fe5cdaa9fa` 的 CI run `39035163288` 18/18 job 成功；大麦演示财务数据新增 FY2022/FY2023 六类公开年度锚点及 FY2021 期末现金锚，生成 2,304 条期间×组织×科目财务明细。驾驶舱视觉补全与数值格式专项完成（代码 SHA `1a71e33fc2f779e1a848a4c3736919e98f762bdf`，run `38936413156` 全部 job 成功）；CFO 盈利分析交付（`/cockpit/profitability`，准确代码 SHA `08aa4cd02247f995bc990d92c8f34f5a1829afa1` 的 run `38996089002` 18/18 job success）。

> **2026-10-17 K0/K1 完成，K2 时间门禁已到、源状态待核验**：K0 Davybase 实现 `172a099`、证据 `94fc05d`、同步 `eb8c3d0` 已推送；历史快照严格终态为 1,265 输入、1,239 成功、2 待复核、24 过滤，清单 SHA-256 `c603baab83f7873c852681c69dfb314e7004e43b230ea832fb2a1e9043ce26bc`。K1 只读扫描器实现 `a0c2e67`、证据 `a914830` 已推送；扫描 1,601 篇 Markdown、17,450 个 embed 未解析、566 篇进入人工 triage、可执行候选为 0。K2 冻结器已推送 Davybase 提交 `699e5c6`；`release()` 推送校验绕过已修复。固定时间门禁后由 D056 和知识刷新设计 v1.2 取代。

> **2026-10-16 用户四项裁决（U04 盲评复评前置）**：① L0 挂 CI（选项 C）——非阻断 `l0-baseline` job（continue-on-error）；② 盲评复评范围（选项 A）——仅旧三样本（顺丰/腾讯/中通）；③ C 级维持 6 条件不变（选项 A）——诚实标准，做不到如实 No-Go；④ ZTO 立即恢复（选项 C）——解封 `wip/zto-integration-20260929`。

> **2026-10-13 深夜·时间线迁移交付（队首子步骤二）**：演示时间线已迁移至菜鸟真实财年——比较期 FY2022（2021-04~2022-03）、分析期 FY2023（2022-04~2023-03）。canonical 明细年度聚合精确等于来源登记披露值（FY2023 收入 77,799,675 千元、毛利 8,146,656 千元，零差异）；财务报表载荷改为申请稿 IFRS 三表逐行原值（合成权益表与利息 65%/折旧 10% 等无来源行全部移除）；新增简体 IFRS 勾稽器（12 恒等式）接入发布门禁；覆盖矩阵重建为 FY2022/FY2023 各 32/50（缺口如实缺省）；ORG-LEDGER v2 重版。实现提交 `087a72f2`（分支 `flow/timeline-migration-20261013`），已合并 main（`c824f55f`，同 SHA CI 17/17 success）。F3 已完成（2026-10-14）：capex 符号语义修复（FY2023 FCF −37.3 亿如实为负）；现金流家族勾稽 + 18 项缺口族裁决测试全绿。F4 已完成（2026-10-14）：环比经 prior_month 窗口由前月冻结快照真实供给；MetricCard.mom 进契约。批次 B 已完成（2026-10-14）：安全规格 V1.1.1（cfo 角色 + 行动项 3 Action）、独立审查闭环、ActionItem 表/迁移/路由、web 行动项面板。批次 C-2/C-3/C-4/C-5 已全部完成（2026-10-14）：资产负债/营运资金/费用/现金流/风险/合并模块端点+页面+导航登记。批次 D 已完成（2026-10-15）：问数入口嵌入驾驶舱总览页。

> **2026-10-13 队首子步骤交付（来源登记 + 运营披露层重建）**：机器可读来源事实登记 `config/damai/source_facts_v1.yaml`（325 条 disclosed_fact：FY2021–FY2023 三表逐行、FY2019–FY2025 分部序列、件量/Non-IFRS/业务线占比；原件 SHA 与页锚对 PDF 机械核验；7 项无来源假设处置登记；pytest 门禁 13 项，commit `842c8ea8`）；`fixtures/damai/operations` 重建为披露事实层——分部序列改用菜鸟披露值、件量修复数量级与语义（FY2023 国际 1,519 百万件/国内 2,311 百万单）、废弃「收入÷客单价」推导（commit `e5d8d2c6`）。

> **2026-10-12 接续状态**：F1 指标目录 v1 指纹兼容与验收时钟修复完成（`11129263110d296f33c48b6cb94237a6fcedfd13` CI 17/17）；F2 字典对齐完成（`0d4b554f33bd1c9cdab3242b25d26eb2209a632c` run `38188010174` 17/17）。用户 2026-10-12 重申验收基线：全部经营数据须基于阿里/菜鸟原始公开披露，财务事实不许用无来源假设填充；大麦须被明确标为基于公开数据构建的演示主体；组织用户等非公开实体数据仅作为隔离测试夹具。首轮来源审计发现 `DAMAI.SYN` 生成路径另造财务值并绕开菜鸟事实资产，件量公式存在数量级和字段语义问题。

> **2026-09-30 深夜·驾驶舱抢队首（用户裁决）**：① 交付形式为真实产品页面（Next.js 组件化 + 真实 API，不做静态原型）；② 驾驶舱抢在 U04 盲评复评之前当队首；③ 第一版用大麦物流演示数据跑通真实链路。C 级出口状态不变（仍 No-Go），驾驶舱用演示数据不构成公开财报能力证明。

> **2026-09-29 深夜·路线纠偏（用户裁决）**：C 级 No-Go 解锁路径优先于数据扩张——ZTO 接入封存，队首改为修复后盲评复评（C 级条件 5）。U04 进度：旧样本回归 199/199（顺丰 137 + 腾讯 32 + 中通 30）；CI 收尾修正（`229069ca`，经用户批准）run `36511316012` 17/17 success；小米 0/25、阿里 0/15 首跑失败归因版式泛化（无对应适配器）；yunda 0/20、jdl 0/25 显式降级；U4 按范围关单。14 份报告样本冻结与 oracle 盘点审计：完整独立 oracle 为 0/14，C 级 No-Go（证据不足）。C 级 Go/No-Go 裁决：六条件中 1/2/4/5 未满足。

> **2026-09-28 UX Gate1/Gate5 关闭**：隔离大麦验收 verify 19/19、GET 矩阵 159 项零意外、Playwright 15/15；生产 E2E 157/157、Web 143/143；提交 `0144bad4` 同 SHA CI run `36371507389` 17/17 success。

> **本页是全仓唯一主线**：既维护状态真相，也维护执行队列。2026-09-25 用户裁决（2A）后不再存在第二份「唯一」文档：EXECUTION_TODO、整合总计划、统一完整实施计划与执行收敛计划均已归档为历史/参考，状态与任务只以本页和工作包为准。

> **测试库安全状态**：共享库误清根因已修复并于 `b60c51b` 验证：测试默认使用 `flow_test`，常驻 `flow` 零污染。仍须保留该保护，不得将本地破坏性测试指向常驻库。


> **指标体系资料增量（2026-10-25 用户补充；归属既有事项 7；PR #6 合并归档）：**

## 已完成的非待办参考

知识库增量扫描、指标库行业包、竞对五维矩阵及 O-01/O-02 地基均为已完成证据或设计输入，不再作为并行/非阻塞待办；相关详情分别见[增量扫描册](../knowledge-base/02_research/synthesis/2026-09-17-obsidian-delta-scan.md)、[五维矩阵](../competitive/2026-09-17-five-dimension-matrix.md)和指标库规格索引。Davybase 新增图片批次及非微信覆盖属于上面第6项的未完成工作，不能据早期扫描记录判为完成。

## 指标体系资料增量（2026-10-25 用户补充；归属既有事项 7）

本轮已逐张核读“数研复盘狮”《经营驾驶舱分析指标库》20 张本地原图，完成与现有字典/执行定义/依赖图的查重；[研究映射](../60_delivery/verification/2026-10-25--business-metric-library-reference-review-v1.md)和[指标体系目标](../20_product/METRIC_SYSTEM_GOALS.md)已写入产品文档。本轮仅文档更新，不改运行定义、企业数据、阈值或 CURRENT_RELEASE。当前唯一执行项仍为事项 12 视觉统一；主队列维持 16 项，不因这次学习新增平行实施项或重开 7a。

后续资料评审归入既有事项 7（知识刷新/战略重基线）的来源语义复核与影响评审。下表只细化该事项的依赖和验收，不构成另一份可领取队列；轮到事项 7 后按现有 K 阶段执行。产品代码变更在影响评审后再由本路线图安排切片，不因“文章已读”自动发布新公式。

| 处理阶段 | 范围/复用与文件定位 | 产物与通过条件 |
|---|---|---|
| 来源语义复核 | 本篇 20 图核读及指纹、现有 source baseline/coverage 工具；保留研究材料分级 | 原图页号和图哈希可定位；单篇阅读不冒充全库快照/seal；AI 摘要与直接原图核读分开记录 |
| 指标与口径映射 | `config/metrics/metric_dictionary_v1_1.yaml`、`flow_v1_metrics.yaml`、覆盖清单；本轮只读 | 每个候选判定复用/同名不同口径/待补输入/不适用；优先既有四条关系链；不复制第二套指标 YAML；不把 360/365/年度天数、管理/法定利润或不同回款分母混用 |
| 关系与建立流程评审 | `metrics/persistence.py`、`service.py`、`comparison_contract.py`、`metric-library/dependency-graph.tsx`、治理/覆盖入口 | 七类关系分型，计算边依赖闭合、单位/期间/维度可核验；诊断边不能变成因果；明确使用页面/报告和变更影响；沿用 React Flow/公式 AST/版本与执行绑定 |
| 下游产品影响与验证设计 | 产品目标、指标库和既有驾驶舱/报告；复用 `scripts/build_damai_metric_coverage.py`、现有指标/依赖图/深链测试 | 形成最小变更范围与验收案例，再由本页排入后续实施；至少覆盖增长盈利、资金周转、预算、杜邦四链的可算/不可算及来源；缺 CRM/HR/供应商/项目数据的候选不算已交付 |

文档变更验证为 M1/M6、计划视图与链接检查；本轮没有业务代码变更，不以测试数量代替指标口径审查。后续若变更运行合同，须执行 `make contracts-check`、对应指标/比较与覆盖测试及前端关系/深链测试；若涉及 schema/迁移或新阈值发布，先走既有授权/治理流程。实际可用性与历史快照不随目标文档更新而改变。

</details>

<details>
<summary>7a 单机原型收尾执行卡（2026-10-24 已全部结案，只读归档）</summary>

**执行与跳过规则（当时授权）：** 正常按 7a.1→7a.8 串行；对外部等待、服务不可用、真实数据缺失先做一次有针对性诊断和一个安全替代尝试，连续约 15 分钟无可执行进展时登记"跳过/未验证"继续；CI 排队不阻塞本地实现；关键财务计算、数据真实性、数据隔离和来源链的已证实错误必须修复；删除、密钥/环境文件、未授权 CI 配置或 schema/迁移等红线不能跳过。

| 动作 | 目的与交付 | 通过条件 | 状态 |
|---|---|---|---|
| 7a.1 统一交付基线 | 核对 main/开发分支双向差异；确定候选与批次 | 主目录文件原位保留 | 完成 |
| 7a.2 补齐演示数据 CFO 呈现 | 冻结页面—指标—数据—图表矩阵；接通预算执行、合成账龄、利润桥/产品毛利入口 | 图/表/来源同值；合成与披露分区 | 完成 |
| 7a.3 接通图表、筛选与追溯 | 点选/触屏和键盘等价表格进入指标/明细/来源 | 每种核心图型至少一条真实点选；URL 刷新恢复筛选；键盘可达 | 完成 |
| 7a.4 收敛 A+C 视觉 | 总览桌面/手机定基准，推广六主题/杜邦/数据中心 | 1440×1000 首屏四核心 KPI；九重点页 390/1440px 无溢出 | 完成 |
| 7a.5 图文报告与九页离线包 | 复用冻结快照发布 HTML/PPTX/XLSX；九页静态索引 | 导出数值与冻结快照一致；离线无外网依赖 | 完成 |
| 7a.6 单机数据操作入口 | `make flow-demo` / `flow-demo-reset` / `flow-check` / `flow-backup` / `flow-restore` | 隔离 FLOW_DATA_DIR；普通运行无需 Docker/PostgreSQL/Redis/MinIO | 完成 |
| 7a.7 最终隔离验收与独立复核 | 冻结代码候选；SQLite 全业务旅程；新上下文独立评审 | verify 19/19；准确 SHA CI success | 完成 |
| 7a.8 主线集成与交付归档 | 回流 main；PR 集成；最终说明、验收总表、恢复档案 | 正式交付指向 main 准确版本/CI | 完成 |

结案证据：PR #3 merge commit `b2a1bf22df91239eb311d1692c30c666250678bf`，run `40092106547` 28/28 success；[完结差距审查](../60_delivery/verification/2026-10-24--prototype-completion-gap-review-v1.md)。

</details>

<details>
<summary>历史队列全文（2026-10-21 及以前；冻结参考，禁止独立执行）</summary>

**当前唯一队列（15 项）**：已完成 8 项；实际执行中 1 项（7a，视觉差距收敛与文档审查）；队首待启动 0 项；排队 4 项（含 K3）；暂停 1 项；外部条件受限 1 项。准确 SHA `a71cb28e` CI 28/28 success；lint 0 error、文档 M1/M2/M6 通过。原 `integration` 基线用时 36分51秒；新结构按 4 个隔离 shard 保留全量 284 项测试，66 文件映射零遗漏、零重复，准确 SHA `368a0190` / run `39349190031` 为 28/28 success。

0. completed CFO 驾驶舱盈利分析与图表缺口补全（工作包 COCKPIT--visual-analysis-expansion.md，登记见上方工作包登记表）：四项指标于 Objective 快照冻结并存 trace；只读 API；杜邦树与两期比较图；指标/财报/来源行深链；未具备口径时 unavailable。
0a. completed 驾驶舱视觉补全与数值格式治理（工作包 COCKPIT--visual-completion-and-number-format.md，登记见上方工作包登记表）：订单/件量整数、金额两位小数、单位格式统一、费用页错误修复、真实图表/趋势/下钻、8 页面截图及隔离浏览器验收。
7a. active（历史状态，现已结案） 单机原型架构简化与全视图视觉升级：阶段 7 冷启动 19/19、离线快照零网络请求通过。视觉尚未达到概念图报告密度和图表层级的部分已在后续视觉语言包（事项 12）闭合。
K. queued（历史状态） 第二代静态知识刷新与战略重基线：K0/K1/K2 已完成，K3 baseline/diff 已生成并复验。语义路由、HIGH 全审、MED/LOW 双审、coverage 闭合、候选与独立 reader 尚未完成；不得将自动登记冒充语义审阅。ObsidianWiki 保持只读，`CURRENT_RELEASE` 不变。

以下 1–11 是驾驶舱队首调整前的原队列事项：1、2、3、5 已完成；4 U04 与 6 P3 暂停；7、9、10、11 排队；8 外部材料受限。

1. [完成] 企业组织建制与经营账套初始化包：提交 `2c7d6eb4`，CI run `36270782272` 17/17 jobs success。31 文件发行包稳定 manifest SHA `cbc7cccf…e513`。
2. [完成] UX 可见性与全站验收关闭：Gate1/Gate5 证据与准确 SHA CI 已收口。
3. [完成—证据审计 No-Go] 公开财报 C 级样本/证据盘点与当前门禁裁定：冻结 14 份 PDF/YAML；审计证实 14 份报告没有完整独立 oracle；本阶段 C 级判为 No-Go（证据不足）。
4. [完成·盲评复评 199/199] U04 解析器适配与独立留出验证：旧三样本回归 199/199；小米 0/25、阿里 0/15、yunda 0/20、jdl 0/25 显式降级；关单提交链 `4f997020`+`a28b638d`，CI run `36525496607` 17/17 success。
5. [完成·No-Go 裁决] C 级质量基准与 Go/No-Go：§3 六条件对账裁决 No-Go（条件 1/2/4/5 未满足）；解锁路径重排为盲评复评 → L0 挂 CI → oracle 分批/泛化收敛 → 数据扩张暂停。
6. [暂停·用户裁决 2026-09-29] P3 真实数据、来源与行业扩张：ZTO 接入封存于 `wip/zto-integration-20260929`（2026-10-16 已恢复合并）；恢复条件：C 级解锁四步完成后或用户重新指令。
7. [排队] 第二代静态知识 release 与战略重基线：按已批准 K0–K6；完成用户裁决前 `CURRENT_RELEASE` 不变。
8. [外部材料受限；必须完成主动恢复/结案] `rnd_exp` 官方依据核验：穷尽后无原文则交付可复现报告与重启条件，不得宣称官方核验通过。
9. [排队—依赖验收门槛] U09/O05 内部试点：公开 C 级 Go 且真实企业数据可用时完成；不得把合成数据冒充真实试点。
10. [排队—依赖证据] U10 V1.1 证据决策：轮到后按既有标准整理证据逐项 go/hold。
11. [排队] 内部月度工作台与四级真实周期验收：依赖 C 级通过、数据可用和工作台可用。

裁决记录（2026-09-25 晚，用户四项裁决）：①分支整合归本主线串行执行；②四份「唯一」文档合并为本页唯一主线（2A）；③AI 交叉评由助手安排未参与实现的隔离 AI 审查；④holdout 候选由 AI 可复现随机抽签并归档（4A）。

战略方向（2026-09-13，D052–D054）：企业内部月度财务经营分析工作台为最终产品，公开财报模块独立并先行成熟共享底座；顺序为 U8 → 边界重构 → 公开模块 C 级出口 → 内部工作台 → 四级验证。

2026-09-24 补充：大麦合成发行版是「系统完整性验证工具」，知识刷新是「静态知识维护轨」，两者可在公开 C 级外部门禁等待期间推进；二者均不改变 D052–D054 的真实数据验收顺序。

</details>

## 纪律

- 任务领取/勾选/提交只用本页（队列 + 登记表）与工作包；模块可以维护不可领取的 workstream/backlog 视图，但不得形成第二份状态真相；每完成一阶段提交推送、CI 绿才算 done；
- 详细验收步骤在工作包与归档参考规格；旧详细计划均为历史证据，不按其空复选框恢复任务；
- 工作包文件**不随状态移动**，状态由本页与 views/ 表达；
- M/P 系列、Phase/WS 历史计划只读（见 [TERMS_AND_NAMESPACES](../10_governance/TERMS_AND_NAMESPACES.md)）；
- 测试库安全：测试默认 `flow_test`，常驻 `flow` 零污染，不得将本地破坏性测试指向常驻库。
