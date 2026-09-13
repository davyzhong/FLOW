---
doc_id: FLOW-HANDOFF-STRATEGY-20260912
title: FLOW 三智能体并行重构总交接
doc_type: navigation
status: current
version: 2.1
created_at: 2026-09-12
updated_at: 2026-09-13
owner: FLOW
applies_to: repository
---

# FLOW 三智能体并行重构总交接｜2026-09-13

> 本页是 GPT-5.6 Sol、Kimi K3、GLM 5.3 和主协调者的统一交接入口。下面“历史战略交接”保留原有 D052–D054 背景，当前执行以本页前半部分和链接的正式计划为准。

## 0. 当前结论

U8 已冻结并可恢复；S01 Task 1–5 已形成代码提交。下一阶段不再由一个智能体串行承担全部 Task 6–10，而采用三执行者独立 worktree、主协调者串行集成。

**执行更新（2026-09-13）**：用户已明确批准安全规格并下令开始执行。integration 基线 `b8a3edd` 已建立；Kimi 候选 `0841ff9` 与 GLM 候选 `07d82f2` 已推送。两者当前只进入审查队列：Kimi 分支早于 Sol Bootstrap，不得直接合并；GLM 前端在 Task 7 合同完成后通过新集成分支移植。当前由主协调者完成安全规格 V1.1 独立审查与 Sol Bootstrap。

设计本交接时的仓库基线：

- `main` / `origin/main`: `4ec50bc`；
- U8 严格冻结：`914a473`，标签 `flow-u8-freeze-20260913`；
- Task 5 企业周期实现：`15c57c6`，迁移目标 `0025_enterprise_cycle`；
- `4ec50bc` 的 FLOW CI run `34755147722` 已 success；执行 Gate 0 时仍以最新 main 和最新绿色 run 为准；
- 本页是计划，不代表 Task 6 已经开工。

接手时必须重新 `git fetch` 并以最新绿色 main 为准，不得机械使用这里的旧 SHA 创建执行分支。

## 1. 必读文档

1. [三智能体并行编排设计](docs/superpowers/specs/2026-09-13-flow-three-agent-parallel-orchestration-design.md)——为什么这样分工、合同、所有权、失败边界；
2. [三智能体并行实施计划](docs/superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md)——Task 0–7、精确文件和测试；
3. [三智能体执行使用手册](docs/70_operations/three-agent-parallel-execution-runbook.md)——派发提示词、交付格式、合并方法；
4. [原 S01 详细计划](docs/superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md)——Task 6–10 的功能范围；
5. [S01 工作包](docs/50_plans/work_items/S01--post-u8-boundary-contract-security.md)与[唯一当前路线图](docs/50_plans/CURRENT_ROADMAP.md)——唯一状态真相。

新计划是原 S01 计划的执行编排层，不是第二份路线图，不扩大产品范围。

## 2. 三个智能体的固定职责

| 智能体 | 主要工作 | 不得修改 |
|---|---|---|
| GPT-5.6 Sol | 安全 ABI、授权纯函数、身份解析、0026、审计持久化、publication/object-store 事务边界、负向安全验证 | 除串行 publishing/operations 外的业务 route、前端、路线图、HANDOFF |
| Kimi K3 | 全挂载路由盘点、route policy、七组敏感入口接线、旧工作包/证据继承 review 备忘 | publishing/operations 两条 Sol 路由、Principal/authorize 第二实现、迁移、前端、权威状态与 backlog 修改 |
| GLM 5.3 | 两模块前端、模块 registry/ownership/AST、API 契约生成、受控 E2E runner、Task 9 全链验证 | 安全迁移、产品状态裁决、HANDOFF |
| 主协调者 | 规格冻结、共同基线、分支派发、diff 审查、合并、CI 门禁、交付记录、权威状态和最终关闭 | 不把未经验证的执行者总结直接当完成证据 |

初始分配依据：Sol 是当前环境中的可靠代理型工程模型；Kimi K3 官方资料强调 1M 上下文和长程 coding/知识工作；GLM 5.3 官方仓库强调复杂 coding 与长程工程增强。厂商描述不是验收证据，Wave 1 后按 FLOW 的 CI、越界文件、冲突和返工数据调整。

## 3. 启动顺序

### Gate 0：主协调者串行完成

1. 等最新 main CI 全绿；
2. 修正当前文档漂移：PROJECT_STATE 的迁移头/Task 3、CURRENT_ROADMAP 的三规格状态、READING_ORDER 的“V2 待设计”、S01 工作包的 Task 4/5 状态；
3. 将安全规格从 approved 降回 review，完成修订和独立审查，取得用户对最终字节的明确批准后才恢复 approved；
4. 冻结安全 ABI、审计事务语义、旧 Bearer 截止和模块描述合同；
5. 运行 approved-spec + docs-check；该脚本只校验状态和索引，不能替代第 3 步的用户批准；
6. 创建并推送 `codex/s01-parallel-integration`，公布 Gate 0 `base_sha`；后续每个 checkpoint 重新公布其 CI 绿色 SHA。

当前安全规格虽为 approved，但仍有必须先关闭的空白：旧 Bearer 截止日期、审计访问/保留/脱敏阈值、public/legacy 无企业身份时的授权语义。默认提案写在编排设计 §5；必须经过 `review → 独立审查 → 用户明确批准 → approved`，未完成前不得启动 Task 6。

### Bootstrap：Sol 先建立可依赖 ABI

Sol 在 `codex/s01-security-abi` 交付 Principal/Role/Action/Resource/Decision、纯 authorize 和 audit writer Protocol。主协调者先合并并等 CI 绿，再让三条 lane 从新的共同 SHA 并行。

### Wave 1：三路并行

| Lane | 分支 | 交付 |
|---|---|---|
| Sol | `codex/s01-security-audit` | 身份、审计 ORM/writer、0026、trigger、startup fail-fast、publication/object-store 调用方事务与 intent/outcome |
| Kimi | `codex/s01-route-policy` | 全挂载 route inventory；intake、investigations、metric library、objective reports、statements、copilot、orchestration 权限接线；publishing/operations 标为 Sol 待串行接线；API/扫描测试 |
| GLM | `codex/s01-module-ui` | `/public`、`/internal`、导航语义、Vitest/Playwright 与可供 CI 调用的受控 E2E runner |

主协调者先合并 Sol，再合并 Kimi；随后从两者合并 SHA 派发 Sol 串行发布路由分支，接入 publishing/operations 的最终 route policy 和持久 intent 调用序列，完整复验后关闭 Task 6。GLM 前端分支暂存，不提前宣称 Task 8 完成。

### Wave 2：模块边界和前端集成

Task 6 CI 绿后，GLM 从新基线创建 `codex/s01-module-boundaries` 完成 Task 7。Kimi 只读复核 ownership/route inventory，Sol 只读复核安全副作用。主协调者先合并 Task 7 并重生契约，再从 Task 7 SHA 新建 `codex/s01-module-ui-integration`，cherry-pick 已审 UI commit 后合并 Task 8；不 rebase 已推送分支。

### Wave 3：验证与预关闭

- GLM：`codex/s01-full-verification`，执行 Task 9 全链、U8/0024 恢复→0026 升级→再验证；
- Kimi：`codex/s01-work-item-disposition-review`，只创建 Task 10 旧工作包裁决 review 备忘，不修改权威状态、CAPABILITY_MAP 或 backlog；
- Sol：独立安全复核，P1/P2 不清零不得关闭。

主协调者按 Task 9 → Task 10 review 备忘合并；由主协调者应用裁决、创建或修改 backlog，最后独占更新 PROJECT_STATE、CURRENT_ROADMAP、S01 work-item、CAPABILITY_MAP、计划视图和交付记录。

## 4. 派发使用说明

每条工作单必须写清：任务名、`base_sha`、分支、规格、允许和禁止文件、前置接口、红灯测试、绿色测试、提交信息、交付格式和停机条件。三种模型的完整可复制提示词见[执行使用手册 §5](docs/70_operations/three-agent-parallel-execution-runbook.md#5-三个智能体的固定工作说明)。

执行者必须返回：

```text
状态 / base_sha / branch / commit / push
逐项修改文件
红灯证据与绿色证据
范围检查
迁移或契约结果
残余风险
建议合并顺序
```

没有提交、测试结果或文件清单的工作不进入合并队列。

## 5. 文件所有权与禁止事项

- Sol 独占 security core、auth/settings/main、ORM、0026、两条串行发布 route、`publishing/publication.py`、`operations/publication.py`、`infrastructure/object_store.py` 及其安全/事务测试；
- Kimi 独占 route_policy、工作单逐项列出的七组业务 routes/schemas、全路由 inventory、路由扫描和 auth boundary 测试；可写 Task 10 review 备忘，不得写两条发布 route 或权威状态；
- GLM 独占模块 facade/registry/router/ownership/AST、两入口页面、导航、模块 E2E runner、S01 独立验收 compose 和升级验证 runner；
- 主协调者独占 `.github/workflows/ci.yml`、所有状态、计划视图、知识清单、backlog、CAPABILITY_MAP、交付记录和 integration 分支；
- 三个执行者都不得修改 `docs/knowledge-base` 的不可变档案；
- 不得 force-push、`reset --hard`、直接推 main、手改生成契约或为解决冲突删除用户文件。

发现两个 lane 需要同一文件时，两边都停止，由主协调者重新指定唯一 owner。

## 6. 合并和验收

固定顺序：

```text
安全 ABI
→ Sol 审计/0026/发布事务
→ Kimi 路由接线
→ Sol 串行接入 publishing/operations route
→ 完整安全复验并关闭 Task 6
→ GLM 模块 API/ownership
→ GLM 前端
→ Task 9 全链证据
→ Task 10 review 备忘
→ 主协调者状态关闭
```

每次合并前检查当前 checkpoint base 和文件白名单；同一波次共享 base，后续波次使用上一 checkpoint 的 CI 绿色 SHA。每个候选合并后只运行本地目标测试与交叉测试；在 Bootstrap、Task 6 security、Wave 2、最终 Wave 3 四个检查点各推送一次 integration。由于 main 当前没有 branch protection required checks，必须用仓库内 S01 job 清单核验目标 SHA 的 FLOW CI：workflow success、清单 job 全 success 且无 skip。`.github/workflows/ci.yml` 必须纳入安全纯测试/集成测试、模块 AST/API、导航 Vitest 和 `make test-module-boundaries-e2e`。最终 main 只从上述门禁全绿的 integration 前进。

Task 9 的关键恢复序列：

```text
用专属 compose project 在一次性隔离库恢复 U8/0024 基线
→ 核验关键表和 frozen payload 哈希
→ alembic upgrade 到唯一 0026 head
→ 核验 enterprise/cycle/security schema
→ 直接 SQL 验证 AuditEvent UPDATE/DELETE trigger
→ 专属 API/动态 HTTPS 读取恢复库独有载荷并与 SQL/哈希对账
→ 旧入口与新模块全链回归
```

任何 skip、哈希不一致、第二 migration head、AI 可发布、规则可自批或跨企业可访问，均令 S01 保持 active。

## 7. 卡住的问题与默认裁决

1. 基线 `4ec50bc` 的 FLOW CI 已 success；接手仍必须重新查询最新 main，不能把历史 run 当成新 checkpoint 证据；
2. 权威状态文档落后于 Git：只能由主协调者成组修正，并在原 S01 计划、CURRENT_ROADMAP、S01 work-item、计划 README 登记“原计划定义范围、新计划定义并行执行”的权威关系；
3. 安全规格有空白：默认 Bearer 截止 `2026-10-31T23:59:59+08:00`，只映射最小 service account；审计至少在线保留 365 天且 S01 不物理删除；这些仍是待审提案，必须经独立审查和用户明确批准才能成为 approved 规格；
4. 现有部分 GET 实际冻结/写入：按实际副作用保护，不能按 HTTP 方法猜；
5. publication service 内部 commit 和对象存储副作用可能破坏审计原子性：固定 `prepare_intent → route commit → execute_object → finalize success/failure → route commit`；两条发布 route 与 service 统一归 Sol，并在 Sol/Kimi 主分支合并后串行接线，不能在 route 尾部补日志冒充闭环；
6. Task 7 新 API 会改变 OpenAPI：该任务同批重生契约，Task 9 再从最终状态复验；
7. 当前 CI 没有覆盖新增安全、架构、Vitest 和 Playwright 门禁：Task 6/8 的完成条件包含由主协调者补齐 FLOW CI job 并由 S01 清单逐项核验，不能用本地证据替代。

## 8. 故障恢复

- lane 失败：不合并，保留分支修复；
- integration 合并导致失败：普通 `git revert -m 1`，不改写历史；
- 0026 失败：只在一次性验收库 downgrade；
- generated contract 冲突：从最终 FastAPI 重生；
- Task 9 恢复失败：停止 Task 10 关闭；
- main 被其他会话推进：暂停合并，fetch 后重新评估 base，不盲目 rebase 状态文档；
- 始终保留 `u8-final-baseline`、`flow-u8-freeze-20260913` 和本地 U8 备份。

## 9. 下一步

接手者只执行 Gate 0，不直接领取三条 lane。Gate 0 提交和 CI 绿色后，先派发 Sol Bootstrap；Bootstrap 授权测试已接入远端 CI 且 checkpoint 核验绿色后，才同时派发 Wave 1 三个智能体。

---

## 历史战略交接（原 2026-09-12 内容，保留供 D052–D054 追溯）

# FLOW 战略重构讨论交接｜2026-09-12

> **状态更新（2026-09-13）**：本交接所述沉淀任务已完成——D052–D054 决策已创建并更新索引与接替关系（D002/D010/D045/D046 superseded，D039/D049/D050 amended），canonical 产品文档与 PRODUCT_PRINCIPLES 已更新，README/导航/状态/路线图已同步，战略设计 V1.1 经三轮独立规格审查后转为 approved。以下 §4/§5 保留为历史记录，不再表示当前待办。

## 1. 当前任务

用户要求基于当前实现和已积累的财务/经营知识，使用苏格拉底提问法重新讨论 FLOW 的目标和计划；必要时允许大幅调整项目目标。讨论已完成目标定位、产品结构和阶段路线三部分，并逐段获得用户确认。

当前只应把已确认结论沉淀到项目文档、README、决策和固定原则中。**不要开始产品代码重构**；现有 U8 必须先完整收口。

## 2. 已确认的战略结论

### 2.1 核心产品与用户

- FLOW 的核心、不可替代价值是**财务分析工作台**。
- 核心操作者是**财务经营分析专员（经分专员）**，不是 Finance BP。
- Finance BP 是数据和业务背景提供者，首版使用受限的轻量提交入口：上传文件、补充资料、回答问题、查看退回原因，不进入完整分析工作台。
- CFO 是首要阅读者；管理层和业务负责人是最终价值承接者。三者可以只消费发布成果，不要求登录 FLOW 完成复杂编制。
- 当前产品按**单个企业内部部署**设计，服务该企业多个经分专员和 Finance BP；不是多租户 SaaS。
- 默认部署形态是公有云企业单租户。允许使用具有企业数据保护条款、禁止训练且可审计的云模型 API。

### 2.2 核心任务与成功标准

- 第一报告场景是**月度综合财务经营分析报告**。
- FLOW 从原始 Excel 和企业数据开始，覆盖识别、映射、校验、对账、分析、补证、报告、审核和发布。
- 首版以复杂 Excel 文件包为主，未来增加 ERP、财务系统、业务系统和数据仓库连接。
- 现实中每月通常可获得：
  1. 财务报表或科目余额；
  2. 当月实际与预算；
  3. 上年同期、上月数据；
  4. 应收、回款和现金数据。
- 报告采用**稳定骨架 + 动态专题**；财务和经营指标都属于固定分析对象。
- 交互式报告是权威母版，PPT/PDF/Excel 等是派生发布物。
- 系统目标是完成典型报告 80%–90% 的工作；经分专员主要核对证据、处理少量例外并一次性批准发布。
- 最终原型成功门槛：使用授权脱敏真实企业数据端到端生成报告；专业经分人员确认关键事实和 Finding 可用；报告质量不低于人工基准；人工工作量不超过传统流程的 20%。

### 2.3 分析、证据和学习原则

- 默认流程：系统完成标准扫描并推荐重点，经分专员可以接受、调整或追加调查。
- 一条核心 Finding 必须包含：**变化事实、驱动因素、财务影响、证据、风险和建议动作**。首版不强制责任人、改善目标和截止期限。
- 企业事实、内部知识和外部参考必须分层标注：企业数据证明事实；知识库提供方法；行业与外部资料辅助解释和比较，不能混成同一证据等级。
- 数据能证明的事实直接进入报告；证据不足的原因保持候选假设；重要假设主动追问 Finance BP/经分专员，取得证据后再升级为正式结论。
- 当只有人工业务说明时允许纳入，但必须标记为人工提供的业务证据。
- 企业分析空间持续存在，按月创建独立分析周期；累积企业映射、口径、偏好和历史分析。
- 字段映射、计算口径和报告偏好可以自动复用；历史业务解释只能进入候选假设池，必须寻找本期证据后才能成为正式结论。
- 正式指标和标准分解由确定性引擎计算。AI 可在调查区提出临时公式和新拆解，但必须由程序复算；反复有效后才能进入正式、版本化的规则库。

### 2.4 AI 报告生产链

默认报告生产流程已经确认：

```text
分析型 AI
→ 生成完整财务专业分析版
→ CFO 角色 AI 质疑证据、判断管理重要性、压缩细节并生成管理层版
→ 经分专员一次最终审核
→ 正式发布
```

- CFO 角色 AI 不是第二个人工审批人。
- 它可以调整重点、章节和表达，不能修改底层数字、把假设改成事实或提升证据等级。
- 真实 CFO 可以阅读最终报告，但不作为系统发布的必经操作节点。
- AI 不得绕过经分专员自行发布。

### 2.5 产品结构与可见治理

- 主交互采用**月度分析工作流为主、对话为辅**：收数 → 校验 → 自动分析 → 补证 → AI 复核 → 人工终审 → 发布。对话用于追加调查和修改，不取代可见工作流。
- 系统保留并强化指标库、公式、会计科目、映射、分析方法、证据规则、报告模板和配置中心。
- 这些专业规则必须作为外显产品功能，可以查看来源、公式、适用范围、版本和使用位置，不能藏在模型提示词或后台实现里。
- 治理分层：平台级规则只读并随版本发布；企业级规则可配置和版本化；影响正式计算的规则需审批；个人显示偏好可直接生效；历史报告绑定当时版本，不被新配置改写。

### 2.6 两个产品模块与共享底座

- **企业内部分析工作台**是最终目标产品。
- **公开财报分析模块**作为独立产品模块保留在同一仓库，拥有独立入口、规格、验收和模块 workstream/backlog 视图，不再与内部工作台混成一条用户流程；全仓仍只有一份可执行路线图。
- 两者共享财务事实、指标、计算、证据、Finding 和报告发布底座。
- 在内部工作台真实验证前，公开模块仍优先用于成熟共享底座。
- 公开模块阶段出口为 C：自动完成公开材料接入、事实计算、Finding、交互式报告、人工复核、冻结和导出，报告接近可发布。
- 公开模块可使用四级证据：财务报表/附注；完整定期报告；公司公告/业绩会/投资者材料；新闻/研报/其他网络资料。低等级材料只能作为低等级证据或线索。
- 物流供应链继续作为第一验证样板，但不是 FLOW 的长期行业边界。

### 2.7 已批准的总体顺序

采用“共享底座重整后推进”路线：

```text
完成 U8
→ 冻结一个完整、可运行、可恢复的现有版本
→ 重构共享专业底座、公开财报模块、内部工作台的边界
→ 公开财报模块达到 C 级出口
→ 建设企业内部月度分析工作台
→ 物流样板验证
→ 专业经分评审
→ 人工报告与工作量对照
→ 授权脱敏真实数据最终验证
```

- U8 是当前最高优先级：完成真实存储、发布、HTTPS、部署和运行验收。
- 新战略文档与设计可以在 U8 期间并行完成。
- U8 完成前，不进行核心数据模型、主导航和月度工作流的大规模代码改造。
- U8 完成后，不应机械沿旧路线进入 U9/U10；先用新版路线图重新裁决旧任务的保留、改写、合并或取消。

## 3. 本会话已经完成的工作

- 已完整读取 brainstorming 设计流程要求。
- 已读取知识库入口、唯一当前状态、事实合同、D049 方向、旧统一计划、产品文档、决策索引和当前代码入口。
- 已通过逐题讨论确认上述产品目标、角色、证据边界、AI 分工、产品结构、验证标准和总体顺序。
- 已向用户分三部分展示设计并分别获得确认：
  1. 新版目标定位；
  2. 产品结构与专业底座；
  3. 执行顺序、失败边界和验收体系。
- 用户随后授权把全部结论写入关键文档、README、固定准则和原则。

## 4. 历史记录：当时尚未完成 / 当前均已闭合

- **尚未创建**正式战略重构设计文档。
- **尚未新增**承载本轮决定的 D052+ 决策，也未更新旧决策的接替关系。
- **尚未更新**根 README、docs README、产品定义、当前状态、阅读顺序、规格索引和当前路线图。
- **尚未进行**独立规格审查；brainstorming 流程要求设计文档写成后最多三轮 review。
- **尚未制定**新版详细实施计划；当前任务只应先完成文档与战略沉淀。
- 当前工作区存在另一项 M6 文档验收任务的未提交内容，不能混入本任务：
  - `Makefile`
  - `docs/00_start_here/PROJECT_STATE.md`
  - `docs/10_governance/link-allowlist.tsv`
  - `docs/80_reviews/reader-test/`
  - `scripts/documentation/links.py`
  - `scripts/documentation/reader_rubric.py`
  - `scripts/tests/test_document_links.py`
- 当前 HEAD（写交接前）为 `2f48df4`。文档迁移已推进至 M5.2；工作区和 HEAD 仍可能被并行任务推进，接续时必须重新盘点。

## 5. 历史记录：当时的下一会话建议步骤

1. 先读 `AGENTS.md`、`docs/knowledge-base/README.md`、`docs/knowledge-base/00_start_here/AGENT_START_HERE.md`、`docs/00_start_here/PROJECT_STATE.md` 和本文件。
2. 检查 `git status --short` 与最新提交，等待或避开上述 M6 在途文件；不要暂存、覆盖或回退它们。
3. 创建正式设计：建议路径 `docs/superpowers/specs/2026-09-12-flow-strategic-reset-design.md`，状态先为 `review`，内容以本交接第 2 节为准。
4. 新增正式决策并更新索引。建议至少拆为：
   - D052：内部月度财务经营分析工作台成为核心产品；
   - D053：公开财报模块、内部工作台与共享专业底座的边界和顺序；
   - D054：分析型 AI → CFO 角色 AI → 经分专员终审，以及证据/计算/学习原则。
5. 对被改变的 D002、D010、D039、D045、D046、D049 使用 supersedes/amends 关系，不抹掉历史正文；更新 `test_decision_integrity.py` 的连续编号和关系测试。
6. 更新 canonical 产品文档：`PRODUCT_VISION.md`、`PRODUCT_SCOPE.md`、`USER_AND_WORKSPACES.md`、`CAPABILITY_MAP.md`、`PRODUCT_BOUNDARIES.md`、`RELEASE_SCOPE.md`，并新增 `PRODUCT_PRINCIPLES.md` 作为固定原则入口。
7. 更新根 `README.md`、`docs/README.md`、`docs/20_product/README.md`、`docs/40_specs/SPEC_INDEX.md`、`READING_ORDER.md`、`PROJECT_STATE.md` 和 `CURRENT_ROADMAP.md`。README 只摘要和导航，不复制整份战略设计。
8. 若修改 `docs/knowledge-base/README.md` 或其他知识库内容，运行 `python3 scripts/documentation/kb_manifest.py --write` 与 `--check`，并只纳入本任务造成的 manifest 变化。
9. 派发独立 spec reviewer，最多三轮修订。通过后运行文档检查、决策测试、链接检查、全量脚本测试和 `git diff --check`。
10. 只暂存本任务文件，提交并推送 `origin`。不要开始产品代码改造；下一阶段详细计划需在用户审阅正式战略规格后另行编写。

## 6. 已踩过的坑与注意事项

- 当前仓库存在并行文档迁移，HEAD 会在会话中前进；开始和提交前都要重新读取状态。
- 根 `HANDOFF.md` 在 M5 迁移后曾不存在；历史完整原件已迁到 `docs/knowledge-base/07_handoff/HANDOFF.md`。该历史原件属于受保护档案，**不要修改**。
- `docs/knowledge-base/04_decisions/DECISION_LOG.md` 已在 `8687a15` 恢复到原始字节并锁定，不能再次改成导航页；新决定只追加到 `docs/10_governance/decisions/`。
- `test_decision_integrity.py` 当前把 D001–D051 写死；新增决定必须同步更新测试，不能只加文件和索引。
- canonical 产品文档目前仍把 Finance BP、双轨财务/经营工作区和公开客观分析写成现行产品定义，与本轮结论冲突，必须成组更新，不能只改 README。
- 当前 `PROJECT_STATE.md` 仍以旧提交和旧战略描述为主，而且正被 M6 在途任务修改；处理时需合并最新内容，不能覆盖并行修复。
- “公开模块优先”不等于它是最终目标：它只是先成熟共享底座；企业内部月度分析工作台才是目标产品。
- “CFO 角色”在新流程中是 AI 审查角色，不是新增人工审批节点。
- “自动学习”不允许复用历史业务原因为当期事实：稳定规则可以复用，情境解释只能作为候选假设并寻找当期证据。
- 文档检查通过不等于 U8、公开模块 C 级出口或内部工作台已经完成；能力状态必须继续用提交和验收证据表达。
