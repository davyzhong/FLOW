---
doc_id: FLOW-HANDOFF-STRATEGY-20260912
title: FLOW 项目尽调、优化与单 Agent 执行总交接
doc_type: navigation
status: current
version: 3.1
created_at: 2026-09-12
updated_at: 2026-09-15
owner: FLOW
applies_to: repository
---

# FLOW 项目尽调、优化与单 Agent 执行总交接｜2026-09-15

> 本页是下一位单一 Agent 的工作入口，整合了多 Agent 执行审计、R1 修复复核、竞品与方法论研究、工程收口计划和后续产品优化建议。它负责说明“现在在哪里、还要查什么、先改什么、怎样证明完成”；项目状态仍以 [PROJECT_STATE](docs/00_start_here/PROJECT_STATE.md) 为唯一事实源，任务顺序仍以 [CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md) 为唯一执行入口。

## 0. 执行摘要

### 0.1 当前可信结论

- 当前审查基准为 `main@c93c896`；最近已确认的绿色恢复基线是 `640cfb8`，对应 FLOW CI run `34907918485`，17/17 jobs 全绿。
- U8 已完成并建立可恢复冻结基线；S01 Task 1–5 已完成。
- 多 Agent 并行已经终止，后续采用**单一 Agent、逐 Gate、串行执行**。历史 Sol/Kimi/GLM 名称只表示审计来源和问题域，不再表示新的并行派工。
- R0 和 R1 已完成：持久审计、action×resource 授权、严格身份 JSON、legacy cutoff 收窄、66 条路由 `require_action` 接线、correlation 中间件及迁移 `0027_security_contract_fix` 已进入主线。
- 当前没有发现产品战略方向跑偏。FLOW 的核心仍是“经分专员使用的财务经营分析工作台”，系统尽量自主完成数据、证据、分析和报告草稿，经分专员统一终审发布；公开财报分析是独立先行模块，不是最终产品替代品。
- **S01 尚未完成，Task 6 不能关闭。**必须依次完成 R2、R3、R4，并在同一最终 SHA 上通过全部门禁，才能进入公开模块 C 级出口。

### 0.2 当前最重要的偏差与缺口

| 类型 | 当前判断 | 处理方式 |
|---|---|---|
| 多 Agent 流程跑偏 | 已停止继续扩大；历史上发生过共用检出竞争、绕过合并序列、跨门禁推进、范围污染和不可归因提交 | 后续只允许单 Agent 串行，历史候选分支不得整包重放 |
| 安全核心缺口 | R1 已修复并有 CI 证据 | 不重复返工；R2 只补治理写、发布/运行接线及死代码处置 |
| 模块边界验证 | 仍不充分 | R3 重建全树 AST + path-glob ownership 门禁 |
| 全链恢复验证 | 仍不充分 | R4 使用动态隔离、真实 CA、唯一 sentinel 和双证明重做 |
| 权威文档漂移 | `PROJECT_STATE` 已更新；`CURRENT_ROADMAP`、S01 工作包、`READING_ORDER` 和根 README 仍含旧 SHA、旧迁移头或旧并行叙述 | 先登记为文档校正包，最终关闭 S01 时统一同步 |
| 数据正确性 | 覆盖矩阵能说明“能否计算”，尚不能量化“是否算对”；已发现个别同比基数错配 | 在公开模块 C 级出口前建立数字级答案集与盲评基准 |
| 工程卫生 | 运行日志入库、ownership owner 名称仍是 Agent 名、dashboard 存在 404 数据态 | R2/R3 中按白名单处理，不夹带产品功能 |
| 合规/供应链/容量 | 尚无完整基线 | 分别在 R4、数据扩张和内部工作台启动前完成专项尽调 |

## 1. 权威关系与阅读顺序

下一位 Agent 开始工作时按以下顺序读取，禁止从历史聊天或旧三 Agent 计划直接领任务：

1. [PROJECT_STATE](docs/00_start_here/PROJECT_STATE.md)：唯一 current state；
2. [CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md)：唯一可领取路线图；
3. [S01 工作包](docs/50_plans/work_items/S01--post-u8-boundary-contract-security.md)：当前工作包边界与退出条件；
4. [战略重构设计 V1.1](docs/superpowers/specs/2026-09-13-flow-strategic-reset-design.md)、[PRODUCT_SCOPE](docs/20_product/PRODUCT_SCOPE.md)、[PRODUCT_PRINCIPLES](docs/20_product/PRODUCT_PRINCIPLES.md)：产品目标、固定原则和冲突裁决；
5. [单 Agent 修正接管说明](docs/70_operations/2026-09-14-s01-single-agent-repair-handoff.md)与[协调台账 §6](docs/70_operations/2026-09-14-coordination-ledger-glm.md)：R0/R1 已完成证据及 R2–R4 边界；
6. [整合尽调总汇](docs/80_reviews/2026-09-15-integrated-due-diligence.md)、[修复后项目 Review](docs/80_reviews/2026-09-15-project-review-post-repair.md)和[整合优化方案](docs/80_reviews/2026-09-15-integrated-optimization-program.md)：审计结论与候选优化项；
7. [竞品优化清单](docs/competitive/optimization-checklist.md)和[知识库 O-01～O-17](docs/knowledge-base/09_competitive/2026-09-14-optimization-backlog.md)：只作候选需求证据，不自动转成任务。

冲突裁决顺序：用户最新明确指令 → 已接受决策 D052–D054 → approved 规格 → PROJECT_STATE → CURRENT_ROADMAP / 当前工作包 → 本交接 → review / research → 历史计划和聊天记录。

## 2. 已整合的尽调结论

### 2.1 已经闭环，不应重复做

- U8-A～D 与冻结恢复锚已经完成；重构后复用 U8 验收工具，不重建另一套基线。
- R0 已完成：审计材料入库、worktree 收敛、历史候选冻结、交付过度宣称纠正。
- R1 已完成：安全合同核心缺口修复，迁移头升至 `0027_security_contract_fix`，路由保护和审计主链已上线。
- CI required inventory 已包含 `module-boundaries-e2e`；文档元数据门禁在 `640cfb8` 恢复。
- 三层两模块、AI 不得自行发布、缺失不补造、确定性内核与证据链优先等原则已经正式决策，不重新讨论默认方向。
- 竞品/方法论研究已形成较完整资产：商业与开源 AI 财分、国内外 BI、FP&A、咨询方法、AI 问数、MCP、行业基准和物流行业深挖均已入库。

### 2.2 仍需闭环的工程问题

1. R2：七类治理写入口的治理模式、publishing/operations 四阶段事务接线、pipeline 死代码处置；
2. R3：ownership manifest 从单文件登记升级为 path-glob，按全树 source/target owner 做 AST 禁止互导检查；
3. R4：从 U8 冻结数据恢复到 0027 的独立部署验收，禁止 `curl -k`、固定端口/卷、残留数据库或只比较“存在”；
4. `var/metric_library_audit.jsonl` 是运行产物却被 Git 跟踪；
5. `config/modules/ownership_v1.yaml` 使用 `sol/kimi/glm-coordinator` 作为 owner，单 Agent 时代应改成 `security/api/web/docs` 等职责域；
6. dashboard 的 404 not-ready 是 0027 后快照未重发的数据态，不是安全回归，但影响演示；
7. CI 只强制文档 m1，m6 的链接、兼容与读者测试未进入远端门禁。

### 2.3 仍需补做的产品与数据尽调

- 建立反向解析数字级准确率基准，覆盖行项目映射、同比/环比基数、单位、期间、符号和重述；
- 建立 10× 数据量的查询、覆盖矩阵、报告渲染和对象存储容量/性能基线；
- 建立 Python/npm 依赖漏洞、许可证和制品来源清单；
- 内部工作台开始前完成企业数据授权、脱敏、模型数据保护、留存和信创适配边界审查；
- U4 独立 oracle 到料后再执行，不能由参与抽取实现的同一上下文代替；
- U9/O5 继续等待真实企业数据授权，U10 按新路线图重新裁决，不按旧依赖链自动恢复。

## 3. 完整尽调计划

尽调不是一次性“看代码”，而是九个有出口的审计包。每个包都必须记录审查 SHA、证据路径、发现等级、责任工作包和复核结果；尽调发现与修复提交分离。

| ID | 尽调包 | 核心问题 | 方法与证据 | 交付/退出条件 |
|---|---|---|---|---|
| DD0 | 基线冻结与证据盘点 | 审查对象是否唯一、可恢复、与 CI 同 SHA | fetch 后记录 HEAD/origin、CI job 清单、迁移头、tag、dump/hash、工作区状态 | 一页基线记录；不存在“审查旧快照却评价新 HEAD” |
| DD1 | 权威文档与决策链 | 状态、路线图、工作包、README 是否互相矛盾 | 对照 D052–D054、PROJECT_STATE、CURRENT_ROADMAP、S01、READING_ORDER、README、HANDOFF；跑 m1/m6 | 漂移清单逐项有 owner；无第二路线图；链接和元数据全绿 |
| DD2 | 产品范围与用户价值 | 是否仍围绕经分专员、月度工作流、人工终审；公开/内部模块是否混线 | 用产品原则逐项映射页面、API、计划和竞品建议 | 每项能力标记 public/internal/shared/governance；范围外项不进入当前 Gate |
| DD3 | 数据、会计与指标 | 数字是否正确、可复算、可追源、可处理重述 | 冻结答案集、company holdout、期间/单位/符号/基数测试、来源页抽核、指标版本核对 | 数字级准确率报告；正式数字 100% 有来源和复算路径；零严重事实错误 |
| DD4 | 安全、权限与审计 | 跨企业、角色、自批、AI 发布、身份伪造、审计失败是否 fail-closed | route inventory 双向扫描；401/403/allow 持久审计；action×resource、loader、actor 冲突和故障注入 | 零 P1/P2；实际路由与清单一致；AI 无发布权 |
| DD5 | 架构、模块与契约 | 两模块是否越权互导，API/契约/所有权是否一致 | 全树 AST、path-glob ownership、OpenAPI 重生差异、死代码与循环依赖检查 | 每个纳管路径恰好一个职责域；public/internal 禁止互导；生成契约无手改 |
| DD6 | 运行、存储与恢复 | 干净环境能否从 U8 基线恢复并升级，真实 TLS/对象存储是否成立 | 唯一 compose project/卷/动态端口；真实 CA；dump hash、SQL marker、HTTPS marker 三方对账；U8-A/U8-D | 无 skip；hash 相等且 marker HTTPS=SQL；升级/回退和失败态证据完整 |
| DD7 | 测试、CI 与供应链 | 门禁是否真实覆盖，依赖是否安全可追踪 | required job 与 workflow 双向比对；测试隔离/flake 检查；pip/npm 漏洞与许可证扫描；SBOM 候选 | 同一 SHA 全 jobs 绿、无隐藏 skip；P1/P2 供应链问题清零或有批准豁免 |
| DD8 | UX、报告与竞品适配 | 是否减少人工加工，证据/配置是否可见，竞品建议是否适配本产品 | 以经分专员月度任务做走查；报告数字抽核；对照代码矩阵与竞品清单 | 人工只做必要提交、例外处理和终审；建议分为采纳/候选/拒绝并说明理由 |
| DD9 | 综合裁决 | 能否进入下一阶段 | 汇总 P0–P3、依赖、证据和残余风险；独立规格/代码复核 | P0/P1=0；P2 有明确退出条件；更新状态与路线图后才 Go |

### 尽调触发频率

- 每次会话/任务开始：执行 DD0 的轻量版（状态、HEAD、CI、工作区）。
- 每个 Gate 合并前：执行与该 Gate 对应的专项包和 DD7。
- 每个大版本：执行 DD0–DD9 全量复核并新建带日期的 review，旧报告通过 supersedes 链保留。
- 数据扩张前：执行 DD3 + 性能容量基线。
- 内部工作台前：执行 DD2 + DD3 + DD4 + 合规专项。
- 竞品矩阵季度刷新（下次 2026-12），定价/功能/融资等易变事实半年刷新（下次 2027-03）。

## 4. 优化改进建议方案

### A. 当前必做：S01 工程可信度收口

| 顺序 | 改进 | 验收 |
|---|---|---|
| A1 | R2 route-policy-v3：治理写策略化、publishing/operations 四阶段接线、pipeline 死代码删除 | 治理写按角色返回预期 403/成功；intent/outcome 审计完整；全 CI 绿 |
| A2 | R2 卫生包：运行日志移出版本控制并加入 ignore；dashboard 重发快照；文档 m6 纳入 CI（若扩大本 Gate 则单独工作包） | 仓库无运行产物；演示数据可读；远端能拦截链接/兼容漂移 |
| A3 | R3 module-boundaries-v2 + ownership 角色域化 | 全树 AST 无越权导入；manifest 全覆盖且恰好一次；模块 API/契约一致 |
| A4 | R4 full-verification-v2 | U8 dump→0027→HTTPS/API/SQL/hash 双证明，全链无 skip |
| A5 | 状态收口 | PROJECT_STATE、CURRENT_ROADMAP、S01、READING_ORDER、README、HANDOFF、CAPABILITY_MAP 同步到最终绿色 SHA |

### B. 下一产品门：公开模块 C 级出口

1. 执行冻结样本 + company-level holdout + 独立盲评协议；
2. 建立数字级准确率基准，优先修复同比基数、期间列和年度/季度错配；
3. 把溯源提升到数据点级（页码/坐标/原文定位），抽 20 条人工核对；
4. 建立重述/更正的 `supersedes` 链与差异报告；
5. 差异说明和 MD&A 可由 AI 起草，但数字只能来自确定性引擎并接受一致性检查；
6. 只读 MCP 可作为受治理的数据访问通道候选，先暴露 facts、指标和溯源，不开放写入或发布。

### C. 数据与分析深化

- 数据从 5 家/14 份逐步扩至至少 15 家/80 份，先覆盖物流、电商、SaaS；扩张前先有准确率与性能门禁。
- 接入或自建行业基准，优先 ROE、净利率、周转率和杠杆中位数，并记录来源、期间和样本集合。
- 指标字典 v2 增加查询编译层；勾稽规则和科目→报表行推导树成为一等可见配置。
- 增加多期趋势、跨公司对比和受控敏感性分析；多业务线杜邦在分部数据充分时再启动。

### D. AI 能力路线

- 问数按 v1 检索引用 → v2 多步受控计算 → v3 反事实建模递进；100 条基准问题达到约定命中率且每个回答引用事实。
- AI 临时计算必须经过“提议表达式→程序复算→一致性校验→入报告候选”，不能直接把模型答案当正式数字。
- 双 AI 角色可承担分析者与 CFO 复核者，但最终报告仍由经分专员人工确认发布。
- 多模型路由、历史 Finding RAG 和本地模型属于成本/合规优化，在评测与数据保护方案存在后再实施。

### E. 内部月度工作台（双门禁后）

只有公开模块 C 级出口通过且企业数据获得授权后，才启动：月度周期状态机、Finance BP 轻量提交、缺失证据请求、双 AI 例外队列、双版本报告、Excel 共生导出、ERP 连接器抽象和持续对账。拖拽式通用 BI、BSC、K8s/Helm、国际合规认证等高成本项目保持远期候选。

### F. 明确不做

- 不做通用金融终端、通用 BI、海外内容库或自训练金融大模型；
- 不用 AI 代替经分专员正式发布，不让 AI 规则自行批准；
- 不在数据基础不足时堆叠 DCF/EVA/BSC/五力等空壳框架；
- 不将产品绑定到单一云数据仓库语义层；
- 不因为竞品有某功能就绕过 D053 路线图门禁。

## 5. 接下来可直接执行的 To-do List

> 下面只有 T00–T07 属当前已授权的 S01 收口。T08 以后必须在路线图明确领取后才能执行；本表不构成第二份路线图。

| ID | 优先级 | 状态 | 任务 | 依赖 | 完成证据 |
|---|---|---|---|---|---|
| T00 | P0 | next | fetch、HEAD/origin、工作区、迁移头、最新同 SHA CI、U8 tag/dump 可读；建立新 Gate 分支 | 无 | DD0 基线记录；不得从历史 SHA 机械开工 |
| T01 | P0 | next | R2 规格差异核对并先写失败测试；确认治理写、publishing/operations、pipeline 的唯一范围 | T00 | 测试红灯与文件白名单记录 |
| T02 | P0 | todo | 实现 route-policy-v3 治理写与身份去信任；inventory 校验 method/path/action/loader | T01 | 全路由双向一致；伪造、越权、自批、AI 发布均拒绝 |
| T03 | P0 | todo | 串行完成 publishing/operations 四阶段事务和 durable intent/outcome；删除已裁决死代码 | T02 | 成功/失败/对象存储故障均有一致审计，失败态 fail-closed |
| T04 | P1 | todo | 清理 R2 工程卫生：运行日志、dashboard 数据态；评估并单独提交 m6 CI 门禁 | T03 | 工作区干净、演示入口可用、门禁无范围夹带 |
| T05 | P0 | todo | R2 独立规格符合性 + 代码质量复核；目标测试、全测试、required jobs 同 SHA 全绿 | T03–T04 | R2 checkpoint SHA + CI run；P1/P2=0 |
| T06 | P0 | todo | R3 module-boundaries-v2：path-glob ownership、职责域 owner、全树 AST、真实违规 fixture、契约重生 | T05 | public/internal 零越权；每个纳管路径恰好一次；契约检查绿 |
| T07 | P0 | todo | R4 full-verification-v2：独立环境、真实 CA、U8 dump 恢复到 0027、sentinel/hash/API/SQL 双证明、全链回归 | T06 | 无 skip；U8-A/U8-D + S01 jobs 同一最终 SHA 全绿 |
| T08 | P0 | gated | Task 10 旧工作包逐项裁决；同步权威文档并正式关闭 S01 | T07 | PROJECT_STATE/ROADMAP/S01/README/READING_ORDER/HANDOFF/CAPABILITY_MAP 一致 |
| T09 | P0 | gated | 公开模块 C 级出口协议与数字级准确率基准 | T08 | holdout、盲评、可复算/可追源、零严重事实错误 |
| T10 | P1 | gated | 数据点级溯源、重述检测、AI 差异说明、只读 MCP 候选 | T09 | 各自工作包和量化验收 |
| T11 | P1 | gated | 数据扩张与行业基准；同步做 10× 性能容量尽调 | T09 | 15 家/80 份目标按批交付；性能不低于批准阈值 |
| T12 | P1 | gated | AI 问数 v1 与评测集；再裁决 v2/v3 | T09–T11 | 100 问基准、引用/复算/拒答证据 |
| T13 | P1 | blocked | 内部月度工作台与连续三周期真实企业验证 | C 级出口 + 数据授权 | 三个完整周期；相对人工基准满足质量与工时门槛 |
| T14 | external | blocked | U4 oracle、rnd_exp 原文、U9/O5 授权、U10 外部证据决策 | 用户/外部材料 | 各工作包退出条件 |

## 6. 单一 Agent 工作协议

1. 一个 Gate 一个 `codex/` 分支/独立 worktree；R2、R3、R4 不压成一个提交。
2. 每个 Gate 均执行：读取批准规格 → 写红灯测试 → 最小实现 → 目标测试 → 全链测试 → 独立规格审查 → 代码质量审查 → 提交推送 → 等同 SHA CI。
3. 不整包 cherry-pick 旧 Sol/Kimi/GLM 候选；需要时只把它们当作调查材料，按当前规格重做。
4. 禁止用 skip/xfail/弱化断言/删除测试/关闭认证/`curl -k` 换绿色。
5. 代码、生成契约、运行证据、文档分别如实提交，提交标题不能用 docs/chore 掩盖业务代码。
6. 修改安全、迁移、对象存储或发布事务前，先核对批准规格；规格有歧义就暂停该点，不自行创造宽松语义。
7. 只承认目标 commit 与 CI head SHA 完全一致且 required jobs 全 success、无 skip 的结果。
8. 完整任务结束后提交并推送；只暂存本任务文件，不带入其他会话的未跟踪或未提交内容。

## 7. 已踩过的坑与停机条件

- 多个 Agent 共用检出、后台 pull/push 会造成基线错乱；后续禁止。
- 旧分支局部绿色不能替代当前主线同 SHA 全绿；审查报告也必须注明快照时点。
- HTTP GET 不等于只读，冻结/发布等隐藏写必须按副作用保护。
- 数据库有表不等于审计已闭环；必须覆盖 401、403、allow、写入失败和保留策略。
- 对象存储、数据库和审计是跨边界事务，不能在 route 末尾补一条日志冒充原子性。
- 静态资料库、Statements、视觉改版和 DuPont 已随主线继承，但不是 S01 完成证据，后续各建独立工作包。
- 文档新增也会让 CI 变红；提交前必须至少跑 m1，本交接与正式关闭还要跑 m6。
- 发现第二迁移头、跨企业可访问、AI 可发布/自批、恢复 hash 不一致、测试 skip、目标 SHA 与 CI SHA 不同，立即停止关闭流程。

## 8. 下一位 Agent 的第一条动作

从当前最新 `origin/main` 做 T00，只读核对 `PROJECT_STATE → CURRENT_ROADMAP → S01 → 协调台账 §6` 与实际 Git/CI；确认没有新的外部提交后，创建 R2 专用分支，按 T01 开始。不要先做 AI 问数、行业扩张、内部工作台或 UI 大改。

完成 R2、R3、R4 前，对外状态统一表述为：~~U8 已关闭；S01 active；R1 complete；Task 6 closure-ready but not closed；下一 Gate 为 R2~~（已过时）。**2026-09-15 更新：R2/R3/R4 已交付，S01 正式关闭（Task 6 closed）；当前对外状态为「U8 closed；S01 completed；下一 Gate 为公开模块 C 级出口（T09，gated）」。**
