---
doc_id: FLOW-DOC-ARCH-001
title: FLOW 静态知识库与项目文档体系总体设计
doc_type: design
status: approved
version: 1.1
created_at: 2026-09-12
updated_at: 2026-09-12
last_reviewed_at: 2026-09-12
owner: FLOW
applies_to: repository-documentation
knowledge_release: flow-knowledge-2026-09-12.1
target_knowledge_release: flow-knowledge-2026-09-12.1
decision_refs:
  - D049
  - D051
supersedes: []
superseded_by: null
source_refs:
  - docs/knowledge-base/02_research/synthesis/2026-09-12-obsidian-internal-kb-assessment.md
related_code: []
confidentiality: project-internal
---

# FLOW 静态知识库与项目文档体系总体设计

## 0. 文档性质与实施边界

本文定义 FLOW 后续采用的静态业务知识库和项目文档目标架构。用户已确认采用“分层静态化”：完整沉淀知识结论，关键材料选择性归档，其余材料保留固定来源证据。

本轮只批准目标设计，不批准移动、重命名、删除、清洗或批量改写现有文档，也不批准产品代码改造。实际迁移须另行形成实施计划，逐批评审、验证、提交和推送。`docs/knowledge-base/01_conversations/raw/`、`02_research/original/`、原始图片及批准快照继续作为不可变档案，实施时不得移动或重写。

### 0.1 V1.1 修订记录（2026-09-12）

V1.1 为向后兼容的 minor 修订，依据同日评审意见（对照 ATLAS 知识库治理实战经验）：

1. §10.1 验收从写死的篇数改为基线清单哈希对账；
2. 新增 §4.9 存储与体积分级，补齐二进制资产治理；
3. §6.3 校验三件套收敛为单一检查脚本 `scripts/check_docs.py`，JSON Schema 后置；
4. §4.6 新增单人 + AI 会话的角色映射表；
5. §10.3 接续测试从十题降为五题，rubric 附于验证记录；
6. §4.8 / §9 补 `knowledge_release` 批量切换机制；
7. §5.2 补仓库顶层文件的归宿规则。

## 1. 背景与问题

FLOW 经历了财务驾驶舱、财务分析工作台、客观财报分析、财务/经营双轨和内部数据试点等多次方向调整。仓库已积累大量规格、计划、验收、研究、对话、素材和生成文件，但其组织方式仍按形成过程堆叠，造成以下问题：

1. 动态 Obsidian 曾同时承担素材源、研究源和事实参照，项目设计对外部可变目录存在隐性依赖；
2. 素材、知识结论、产品决定和实施任务之间缺少强制的逐层转换关系；
3. Phase、WS、M、P、U、O 多代文档并存，虽然当前已指定 U 为唯一入口，目录仍容易让读者误判；
4. 当前说明、历史证据、正式规格和研究候选分散在 `docs/`、`docs/superpowers/` 与 `docs/knowledge-base/`；
5. `documentation-status.md` 等登记文档会随工程进展迅速过时，缺少可执行的生命周期；
6. 文档标题、日期、版本和状态表达不统一；
7. 新 Agent 需要读取过多历史材料，才能判断哪些内容仍然有效。

截至设计时，`docs/` 下约有 2075 份知识库文件、49 份实施文件、20 份计划和 8 份规格；知识库中又包含约 1558 份已移交微信材料与 425 份研究文件。数量不是问题本身，缺少稳定分层、唯一入口和状态边界才是问题。

## 2. 目标与非目标

### 2.1 目标

- 把已读取的行业知识、财务知识和经营分析知识转化为 FLOW 自有的静态知识资产；
- 让产品定义、设计报告、规格和计划只依赖已发布的静态知识版本；
- 为每份素材建立可追溯的处理结论，避免重复读取或遗漏；
- 为项目文档建立唯一入口、唯一当前状态、唯一当前路线图和清晰的历史区；
- 使业务知识、产品设计、技术规格、实施证据和运行手册各自只有一种职责；
- 保持原始档案可复核、机器引用稳定、Git 历史可追踪；
- 使没有历史会话上下文的新 Agent 能准确接续项目。

### 2.2 非目标

- 不把 3035 篇正文逐篇复制进 FLOW 仓库；
- 不把行业文章中的公式、阈值、内部值或建议自动升级为正式规格；
- 不借文档整理重写产品方向、会计口径或事实合同；
- 不在本设计阶段清理 Git 分支、stash、审计日志或产品代码；
- 不要求所有历史文件采用新名称；不可变档案和机器引用路径优先保持稳定。

## 3. 总体原则

### 3.1 三层资产模型

FLOW 将文档资产分成三个平面：

| 平面 | 回答的问题 | 主要内容 | 是否直接约束实现 |
|---|---|---|---|
| 证据与知识平面 | 我们知道什么，依据是什么 | 来源、知识卡、领域手册、方法模板 | 不能单独约束实现 |
| 产品与合同平面 | FLOW 决定做什么，必须满足什么 | 产品定义、决策、架构、规格 | 是 |
| 执行与证明平面 | 何时做、做了什么、是否通过 | 路线图、工作包、实施、验证、运维 | 按上游合同执行 |

依赖只能单向流动：

```text
来源证据
  → 静态知识
  → 产品定义
  → 正式决策
  → 架构与规格
  → 当前计划
  → 实施记录
  → 验证与发布
```

### 3.2 双库职责

- FLOW 静态知识库是项目可重复使用的业务知识、方法和来源证据库；
- FLOW 项目文档库是产品、架构、规格、计划、实施和运维的正式记录；
- Obsidian/Davybase 继续作为个人动态采集与研究环境，但不再是日常项目执行依赖；
- 迁移前项目引用固定来源基线 `obsidian-2026-09-12T15:46+08:00`；M2 完成后切换到首个静态发布 `flow-knowledge-2026-09-12.1`。只有用户明确发起知识维护时才读取增量并发布新版本。

### 3.3 唯一事实源

| 信息 | 唯一当前来源 |
|---|---|
| 当前工程状态 | `PROJECT_STATE.md` |
| 当前任务顺序 | `docs/50_plans/CURRENT_ROADMAP.md` |
| 产品定位与范围 | `PRODUCT_VISION.md`、`PRODUCT_SCOPE.md` |
| 正式决策 | `DECISION_INDEX.md` 及单项决策文件 |
| 领域对象和行为 | 对应规格文件 |
| 业务知识 | 指定知识发布中的 canonical 知识卡与领域手册 |
| 已完成证据 | 实施、验证、迁移和发布记录 |

README 只导航，不重复维护状态、规格或计划正文。

### 3.4 术语与编号命名空间

| 命名空间 | 含义 | 当前规范入口 | 生命周期 |
|---|---|---|---|
| K1–K8 | 既有财经知识主题分类 | `docs/knowledge-base/02_research/2026-09-11-finance-knowledge-map.md`；M2 后由知识 taxonomy 接替 | 分类可扩展，不代表产品批准 |
| L1–L4 | 数据可得性：公开披露、过程事实、事件事实、行动事实 | `docs/superpowers/specs/2026-09-09-operations-track-methodology.md`；M3 后进入数据层规格 | 随正式规格版本化 |
| D | 正式决策编号 | 当前 `DECISION_LOG.md`；M1 后为 `DECISION_INDEX.md` | 追加、修订或取代，不复用编号 |
| U | 统一财务轨任务编号 | 当前统一 U 计划；M4 后仅由 `docs/50_plans/CURRENT_ROADMAP.md` 解释 | 计划状态，不进入长期知识 |
| O | 经营轨任务编号 | 当前 O 计划；M4 后并入同一路线图 | 计划状态，不进入长期知识 |
| Phase/WS/M/P | 历史计划命名空间 | 路径映射与历史计划 | 只读历史，不领取新任务 |

具体任务状态、阻塞和依赖不得写入本长期架构文档，只能写入唯一 `CURRENT_ROADMAP.md`。

## 4. 静态素材与业务知识库设计

### 4.1 目标目录

知识库保留稳定根路径 `docs/knowledge-base/`，目标结构如下：

```text
docs/knowledge-base/
├── README.md
├── 00_governance/
├── 10_sources/
│   ├── SOURCE_REGISTER.md
│   ├── snapshots/
│   ├── public_originals/
│   ├── authorized_internal/
│   ├── source_notes/
│   └── rejected_and_background/
├── 20_knowledge_cards/
│   ├── finance/
│   ├── operations/
│   ├── methods/
│   ├── governance/
│   └── technology/
├── 30_domain_handbooks/
│   ├── finance_statements/
│   ├── financial_analysis/
│   ├── revenue_and_growth/
│   ├── cost_and_expense/
│   ├── profitability/
│   ├── cash_and_working_capital/
│   ├── budget_and_forecast/
│   ├── operational_efficiency/
│   ├── logistics_and_supply_chain/
│   ├── management_reporting/
│   └── finance_ai_governance/
├── 40_methods_and_patterns/
├── 50_product_mappings/
├── 90_history/
├── 99_manifest/
├── 01_conversations/raw/        # legacy immutable root，永久原位共存
├── 02_research/original/         # legacy immutable root，永久原位共存
├── 03_assets/logistics_daily/    # legacy immutable image root
├── 03_assets/external_reference/ # legacy immutable image root
└── 05_design/approved/           # approved snapshot root
```

上图最后五项是 legacy immutable roots，不参与编号重排，永久与新结构共存。目标结构通过来源登记引用这些原路径，不以搬迁换取表面整齐。

不可变路径基线必须由 M0 生成 `00_governance/IMMUTABLE_PATHS.md` 和机器可读 `00_governance/immutable-paths.lock.tsv`：

| 路径 | 属性 | 允许操作 | 禁止操作 |
|---|---|---|---|
| `docs/knowledge-base/01_conversations/raw/` | 原始会话 | 读取、校验哈希、新增独立批次 | 移动、覆盖、清洗旧文件 |
| `docs/knowledge-base/02_research/original/` | 原始研究及其图片 | 读取、校验哈希、新增独立批次 | 移动、覆盖、改写旧批次 |
| `docs/knowledge-base/03_assets/logistics_daily/` | 用户原始图片 | 读取、引用、校验哈希 | 移动、压缩覆盖、重命名 |
| `docs/knowledge-base/03_assets/external_reference/` | 外部参考原图 | 读取、引用、校验哈希 | 移动、覆盖、重命名 |
| `docs/knowledge-base/05_design/approved/` | 批准时设计快照 | 读取、引用、校验哈希 | 原位修订、移动、替换 |

M0 必须记录当时既有路径集合、逐文件 SHA-256 和 `baseline_hash`。后续合法新增批次使用独立 append-only delta 清单与 `delta_hash`，再生成不替代历史基线的汇总索引；验收要求基线路径集合及其逐文件哈希不变，不要求汇总索引永远保持同一哈希。若发现其他用户原始图片目录，先加入新的锁定 delta 再继续迁移。

### 4.2 来源与证据层

来源层只回答“这条知识从哪里来、是否允许使用”，不承担产品结论。`SOURCE_REGISTER.md` 必须覆盖本轮财经/经营预设范围内的全部来源，并为每项记录：

- `source_id`、标题、作者、来源路径或 URL；
- 固定截面、获取日期、文件哈希；
- 来源类型、权威等级、敏感等级；
- 是否允许归档全文、引用、改写或仅保留路径；
- K1–K8 知识域和产品相关范围；
- 处置：采用、部分采用、重复、背景、拒绝或待核；
- 派生知识卡 ID 和核验说明。

“全部整理”的完成标准不是复制全部文章，而是所有来源均有处置记录，所有正式知识均能反查来源。

### 4.3 原子知识卡

一张知识卡只表达一个可独立引用和版本化的知识单元。建议 ID 体系：

| 前缀 | 范围 | 示例 |
|---|---|---|
| `FIN` | 财务事实、指标与报表 | `FIN-METRIC-001` |
| `OPS` | 经营、供应链与物流 | `OPS-PROFIT-003` |
| `METHOD` | 分析、报告与会议方法 | `METHOD-REPORT-002` |
| `GOV` | 权限、审计与知识治理 | `GOV-AUTH-001` |
| `TECH` | AI、检索和可解释性方法 | `TECH-COPILOT-004` |

统一元数据：

```yaml
---
doc_id: FIN-COMPARE-004
doc_type: knowledge-card
knowledge_id: FIN-COMPARE-004
title: 预算版本与实际比较
domain: budget_and_forecast
status: canonical
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
last_reviewed_at: 2026-09-12
owner: FLOW
applies_to: finance-analysis
knowledge_release: flow-knowledge-2026-09-12.1
authority_level: B
sensitivity: project-internal
source_refs:
  - SRC-EXAMPLE-001
applicable_scope: []
effective_from: 2026-09-12
supersedes: []
superseded_by: null
related_knowledge: []
related_code: []
---
```

正文固定包含：定义、业务目的、输入、规则、适用条件、不适用条件、常见误用、来源与核验、FLOW 影响。`canonical` 知识卡必须至少有一个有效 `source_ref`；综合结论可以引用其他 canonical 知识卡，但必须同时保留核验记录，不能形成无源闭环。

知识卡不保存 `related_specs`。规格对知识的消费关系由发布外的生成索引维护，防止新增规格反向修改已经发布并锁定的知识内容。

知识状态只允许：

- `candidate`：已登记，未完成正式核验；
- `verified`：来源和含义已核验，尚未成为项目默认；
- `canonical`：已进入当前静态知识发布；
- `deprecated`：被新版本替代。

访问限制不是内容状态，而是独立 `sensitivity` 属性。授权、降敏或撤回必须创建新知识版本和新发布，不能原位改变旧发布。

### 4.4 领域手册

领域手册把多个知识卡组织成完整业务认知。每个领域 `README.md` 至少包含：

1. 领域定义与边界；
2. 核心对象和术语；
3. 指标与口径；
4. 分析维度；
5. 比较、分解和下钻逻辑；
6. 数据要求与可得性 L1–L4；
7. 典型分析路径；
8. 风险、误用与权限边界；
9. 对应知识卡、来源和产品映射。

知识卡解决“单条知识是否可信”，领域手册解决“一个主题如何被系统性理解”。

领域手册复用同一核心元数据，`doc_type: domain-handbook`，使用稳定 `doc_id`（例如 `HANDBOOK-BUDGET-001`），并增加 `knowledge_refs`。candidate/verified 阶段的 `knowledge_release` 可以为 `null`；一旦 canonical，必须指向包含该确切版本和哈希的 release lock。

### 4.5 方法与模板层

`40_methods_and_patterns/` 保存可复用的抽象方法，包括财务分析方法、经营分析 SOP、差异分析、报告章节、驾驶舱信息架构、分析包、一报一会、指标卡/预警卡/问题卡、Copilot 回答约束及独立复核方法。

这里不得复制受版权或权限限制的原文，不保存具体项目排期，也不能用文章示例值替代 FLOW 默认值。

### 4.6 产品知识映射

`50_product_mappings/` 是知识进入产品的唯一转换入口。每项映射至少包括：

| 字段 | 含义 |
|---|---|
| 业务知识 | 领域手册或知识卡 ID |
| FLOW 对象 | 事实、指标、比较、分析、报告或行动对象 |
| 当前能力 | 已实现、部分实现或未实现 |
| 数据层 | L1–L4 |
| 采用状态 | 采用、试点、后置、拒绝、待核 |
| 缺口与风险 | 数据、权限、口径、技术或评测缺口 |
| 目标规格/任务 | D/U/O/规格编号 |

产品规格不得从来源文章直接产生；必须先经过知识卡或领域手册，再通过映射记录进入正式决策和规格。

逐层转换门禁如下：

| 转换 | 必备输入 | 输出与状态门 | 责任角色 | 失败处置 |
|---|---|---|---|---|
| 来源→知识卡 | 已登记来源、权限和截面 | `candidate` 卡片 | 知识整理者 | 重复/背景/拒绝写回来源处置 |
| candidate→verified | 来源可追、含义明确、冲突已处理 | `verified` 卡片 | 领域复核者 | 保持 candidate，或提高 sensitivity 限制访问 |
| verified→canonical | 进入发布范围、引用完整、通过 schema/哈希 | 版本化 immutable 卡片 | 知识发布维护者 | 不纳入本次发布 |
| 知识→产品映射 | canonical/verified 知识、数据层和风险 | 采用/试点/后置/拒绝 | 产品负责人 | 记录理由，不产生规格 |
| 映射→决策 | 改变产品边界、合同或优先级 | accepted decision | 用户或明确授权的决策者 | 保持候选或后置 |
| 决策→规格 | accepted decision、知识发布锁 | approved spec | 规格负责人 | 不得进入计划 |
| 规格→计划 | approved spec、依赖和验收明确 | active work item | 计划负责人 | blocked/proposed |
| 计划→实施/验证 | 明确实施授权 | 交付与独立验证证据 | 实施者/复核者 | 失败不标完成，形成缺陷或回滚 |

仅当映射改变产品范围、合同、不变量、授权边界或任务优先级时必须产生正式决策；纯展示参考、已批准规格内的非语义实现细节可以进入工作包，但必须同时引用产品映射和一个现存的 approved spec，且不得新增或改变输入、输出、不变量、权限、失败态或验收语义。超出任一条件必须退回决策/规格门。

### 4.6.1 单人 + AI 会话的角色映射

上表的责任角色在单人项目中按以下方式落地。门禁分两类：**AI 可自验**（脚本、哈希、链接、schema、来源核验）失败即阻断该步；**必须用户签**（决策 accepted、release 切换、范围/授权变更、删除类操作）AI 只能准备变更并停下等确认，不得代签。

| 设计角色 | 实际执行 | 门禁性质 |
|---|---|---|
| 知识整理者 | AI 会话 | AI 可自验（登记、处置、来源追溯） |
| 领域复核者 | AI 会话（换会话复核） | AI 可自验（来源补核、冲突裁决） |
| 知识发布维护者 | AI 会话执行；release 切换须用户批准 | 混合：构建/校验 AI 自验，`CURRENT_RELEASE` 切换必须用户签 |
| 产品负责人 / 决策者 | 用户本人 | 必须用户签 |
| 实施者 / 复核者 | AI 会话；复核由无历史上下文的独立会话完成 | AI 可自验；测试证据落 `60_delivery/` |

### 4.7 权威与敏感等级

建议权威等级：

| 等级 | 来源 | 可支持的结论 |
|---|---|---|
| A | 法律、准则、监管和官方原文 | 正式口径和强约束 |
| B | 经审计披露、权威行业标准 | 事实定义和行业口径 |
| C | 专业机构、教材、成熟产品文档 | 方法与候选设计 |
| D | 企业实践、内部材料、行业文章 | 字段和试点候选 |
| E | AI 摘要、二次整理、无源观点 | 检索线索，不得单独定稿 |

敏感等级统一为 `public`、`project-internal`、`authorized-internal`、`restricted`。低权威来源不能覆盖高权威来源；内部值和文件必须经过对应内部数据试点的明确授权、脱敏和审计。冲突按“适用会计制度/司法辖区→生效日期和版本→来源权威→对当前主体的具体性”依次裁决；同级且仍不能裁决时并列保留为 candidate，不合并成虚假统一口径。

### 4.8 静态发布与更新

目标第一版发布固定为 `flow-knowledge-2026-09-12.1`，引用 `obsidian-2026-09-12T15:46+08:00`。该发布只有在 M2 验收通过后才存在；在此之前，文档使用 `flow-knowledge-2026-09-12.1`。M2 之后每份产品设计、规格和计划必须声明一个可由 release lock 解析的 `knowledge_release`。

知识发布采用可回放的物理结构：

```text
docs/knowledge-base/00_governance/releases/
├── release-lock.schema.json
├── CURRENT_RELEASE
└── flow-knowledge-2026-09-12.1/
    ├── release.yaml
    ├── release-lock.yaml
    ├── coverage.tsv
    └── sha256sums.txt
```

`release-lock.schema.json` 是所有发布锁的机器合同。`CURRENT_RELEASE` 只保存当前 release ID。`release.yaml` 固定来源截面、覆盖范围、排除规则和批准记录；`release-lock.yaml` 枚举该发布的全部权威资产，而不只知识卡：knowledge-card、domain-handbook、taxonomy、product-mapping、source-register 和 coverage。每项必须有稳定 asset ID、类型、版本、路径、SHA-256 和上游关系。

已发布知识卡和领域手册使用带版本文件名，例如 `FIN-COMPARE-004--v1.0.md`，发布后不可原位修改；任何语义或文字修订都创建新版本文件。旧发布目录永久保留，历史产品文档通过 `knowledge_release` → `release-lock.yaml` → 版本化路径恢复其当时内容。`CURRENT_RELEASE` 只能在新发布全部校验通过后以独立提交切换。

首版 `flow-knowledge-2026-09-12.1` 的 `coverage.tsv` 是 3035 篇覆盖声明的规范清单，必须记录来源 ID、截面 ID、内容指纹、纳入/排除理由、处置、知识卡关系和敏感等级；`release.yaml` 同时记录总数与 coverage 基线哈希。不能归档全文的来源至少保存稳定定位符、标题/作者、访问时间、允许保存的内容指纹、核验人和不包含受限正文的核验凭据。

后续发布不得继续断言总数 3035，而是完整继承前版记录，并追加显式 `added`、`amended` 或 `withdrawn` delta；分别校验继承基线哈希和 delta 哈希。发布外的消费者反向索引、搜索索引和生成视图不进入 release lock，可随消费者变化重建，且不得被产品文档当作权威内容。

`knowledge_release` 的批量切换：M2 验收通过后由 `scripts/set_knowledge_release.py <old> <new>` 一次更新全部引用旧 release 的文档元数据，随即运行 `scripts/check_docs.py` 全量验证，`CURRENT_RELEASE` 切换与元数据批量更新作为同一独立提交完成。切换前后的 doc 清单与逐文件 diff 保存为该提交的验证记录。

未来知识更新独立执行：建立新截面、读取增量、更新来源登记、新建知识卡版本、完成冲突与影响评审、发布新版本。动态源变化本身不触发当前项目文档或代码变更。

### 4.9 存储与体积分级

知识库与文档资产含大量二进制（原始图片、研究附件、归档快照）。为避免仓库体积失控与跨环境割裂（ATLAS 仓库曾因此做专项治理），二进制资产按以下四级分级，判定顺序 D → C → B → A：

| 级 | 判定 | 存放 | 登记字段 |
|---|---|---|---|
| D 冗余 | 与库内其他文件 SHA-256 一致，或纯中间产物 | tar 备份 30 天后删除（备份路径记录于治理文档） | `storage: redundant-deleted` + 删除依据 |
| C 冷档 | 整包快照、被替代的历史原件、>100MB 单体 | GitHub Release 原样挂载，**不重新打包** | `storage: release:<tag>/<asset>` |
| B 热档 | 当前仍在用的中大二进制原件（>2MB） | Git LFS（目录限定 pattern，防止波及代码目录） | `storage: lfs` |
| A 文本 | md、json、<2MB 小文件 | 普通 git | `storage: git` |

执行规则（来自实战验证）：

1. **docx/pptx/zip 不重压缩**：它们本身是 zip 容器，实测重压缩收益 <0.01%，且重打包破坏已登记的 SHA-256 链；归档原件永远原样。
2. **GitHub Release 会清洗 asset 文件名中的非 ASCII 字符与空格**（中文变点号），内容字节不变：上传后为每个 asset 写回 label=原始文件名，Release notes 携带「原始文件名 + SHA-256」清单作为权威对账表；仓库内引用按哈希对账，不依赖远端 asset name。
3. **冗余清除前置**：逐文件 SHA-256 核验（任一不匹配即中止）→ tar 备份 → 删除 → 登记留痕。删除、push、安装依赖、创建 Release 均须用户明确授权。
4. **git blob 内容寻址**：同内容文件多路径在对象层只存一份；去重决策按工作区实际体积计算。
5. M0 盘点时登记 `docs/` 与仓库二进制的体积分布与分级标注；迁移批次只搬运 A 类文本与元数据，B/C 类二进制的分级处理独立成批，不与文本迁移混批。

## 5. FLOW 项目文档总体设计

### 5.1 目标目录

```text
docs/
├── README.md
├── 00_start_here/
├── 10_governance/
├── 20_product/
├── 30_architecture/
├── 40_specs/
├── 50_plans/
├── 60_delivery/
├── 70_operations/
├── 80_reviews/
├── 90_archive/
└── knowledge-base/
```

### 5.2 当前入口

`00_start_here/` 只保留：

- `README.md`：入口说明；
- `PROJECT_STATE.md`：当前实现、缺口、阻塞和验证；
- `READING_ORDER.md`：按角色给出最短阅读路径；
- `DOCUMENT_MAP.md`：旧路径、新路径和接替关系。

其中 `README.md` 只链接 `docs/50_plans/CURRENT_ROADMAP.md`，不得复制路线图内容或维护第二份路线图。

新 Agent 应在读取不超过 5 份文档后，准确回答项目定位、已完成能力、下一步、不可绕过规格和静态知识版本。

仓库顶层归宿规则：顶层只保留 README、AGENTS、构建配置与工程入口文件。会话交接文档（如 `HANDOFF.md`）归 `docs/knowledge-base/07_handoff/`；一次性的全量会话归档（如 `Finance_Intelligence_OS_完整会话归档.md`）归 `docs/90_archive/`；两者均以 M5 批次迁移，原始字节不改写，仅在原位置保留指路说明。

### 5.3 治理与决策

`10_governance/` 包含文档治理、知识治理、术语、变更规则和单项决策。现有 `DECISION_LOG.md` 后续拆成 `DECISION_INDEX.md` 与 `decisions/Dxxx--topic.md`；历史原日志保留。

决策状态：`proposed`、`accepted`、`amended`、`superseded`、`rejected`、`retired`。已接受决策不直接抹改，修订通过 `amends` 或 `supersedes` 表达。

### 5.4 产品定义

`20_product/` 只回答做什么、为什么做和不做什么：

- `PRODUCT_VISION.md`；
- `PRODUCT_SCOPE.md`；
- `USER_AND_WORKSPACES.md`；
- `CAPABILITY_MAP.md`；
- `PRODUCT_BOUNDARIES.md`；
- `RELEASE_SCOPE.md`。

这里集中解释财务/经营双轨、公开财报/内部数据两阶段、事实/拆解/推断/行动边界，以及 Dashboard、分析、报告和 Copilot 的关系。

### 5.5 架构与规格

`30_architecture/` 按系统、数据、领域、指标、分析、发布、安全和部署拆分。每份文档必须明确 `implemented`、`designed`、`external-dependency` 和 `out-of-scope`，禁止把目标架构写成现有能力。

`40_specs/` 按 platform、data-intake、financial-facts、metrics、analysis、operations、reporting、copilot 和 security 分域。规格只定义输入、输出、对象、状态、不变量、失败方式和验收条件，不维护进度或外部文章摘要。

机器和测试已引用的路径，迁移前必须完成引用影响分析；不能安全迁移时保留原路径或兼容入口。

### 5.6 计划体系

`50_plans/` 分为：

```text
50_plans/
├── README.md
├── CURRENT_ROADMAP.md
├── work_items/                 # 工作包稳定路径，不随状态移动
└── views/                      # active/blocked/completed 生成索引
```

路线图只维护任务顺序、依赖和状态；工作包文件维护范围、步骤、验收和交付物。工作包不因 active/blocked/completed 状态而移动，状态由元数据和生成视图表达。不得再出现多份“唯一总计划”。U/O 保留为当前任务编号，Phase/WS/M/P 只保留历史映射；具体当前任务状态只允许出现在路线图。

### 5.7 交付、运行和审查

`60_delivery/` 保存实施、验证、迁移、发布和机器生成结果，只记录已经发生的事实。计划任务只有得到这里的验证证据后才能标记完成。

`70_operations/` 保存部署、配置、密钥、备份、日志、故障处理、数据维护和安全运行手册。

`80_reviews/` 保存文档、架构、代码、安全和数据质量审查。问题状态统一为 `open`、`partially-resolved`、`resolved`、`accepted-risk`、`obsolete`；已关闭问题不得继续显示为当前缺陷。

### 5.8 历史区

`90_archive/` 保存被接替的项目计划、规格、方向和审查。归档文档增加：

```yaml
status: archived
archived_at: 2026-09-12
superseded_by: FLOW-PLAN-CURRENT
historical_scope: phase-1-to-phase-10
do_not_execute: true
```

不可变原始素材不移入该目录。历史区不是垃圾箱，而是保留形成过程和审计证据。

文件状态优先由元数据和索引表达，而不是通过移动表达。若可变文档确需迁移路径，必须：登记全部消费者；同批更新可变链接；对无法同步的消费者保留兼容入口；跨 macOS/Linux 验证。兼容入口只有在消费者清单为零、至少两个包含该消费者验证的正式发布周期通过、独立复核通过并获得单独批准后才能移除。不可变档案和机器硬编码但无法安全迁移的文件永久保留原路径。

### 5.9 高频文档类型路由

| 文档类型 | 唯一目标位置 | 不应出现的位置 |
|---|---|---|
| 数据字典、语义模型说明 | `40_specs/financial-facts/` 或 `40_specs/metrics/` | research、plan、README |
| 测试策略与验收矩阵 | `40_specs/platform/`；事实结果在 `60_delivery/verification/` | 产品定义、知识卡 |
| 发布变更日志 | `60_delivery/releases/` | 当前状态正文、计划正文 |
| 风险与例外登记 | `10_governance/`；运行风险可在 `70_operations/` 建链接视图 | 分散在历史 review |
| 数据库迁移说明 | `60_delivery/migrations/` | 架构目标、知识库 |
| API/事件合同 | `40_specs/` 对应领域 | implementation 复述 |
| 生成报告与矩阵 | `60_delivery/generated/` | 手工维护的规格目录 |
| 外部研究摘要 | `knowledge-base/10_sources/source_notes/` | 产品规格和当前计划 |

## 6. 命名与元数据

### 6.1 稳定当前文件

唯一当前入口和机器合同使用稳定名称，不加日期：

- `PROJECT_STATE.md`
- `CURRENT_ROADMAP.md`
- `PRODUCT_SCOPE.md`
- `FACT_CONTRACT.md`
- `DECISION_INDEX.md`

更新时间写在元数据，不通过改名表达。

### 6.2 历史与一次性交付

采用 `YYYY-MM-DD--type--topic--version.md`：

- `2026-09-12--research--obsidian-finance-baseline--v1.md`
- `2026-09-12--design--static-knowledge-architecture--v1.md`
- `2026-09-12--verification--metric-library-v1.1.md`

日期表示首次建立或事实发生日期，不随日常更新变化。

### 6.3 正式文档元数据

所有可变正式文档统一包含：

```yaml
doc_id:
title:
doc_type:
status:
version:
created_at:
updated_at:
last_reviewed_at:
owner:
applies_to:
knowledge_release:
decision_refs: []
supersedes: []
superseded_by: null
source_refs: []
related_code: []
confidentiality:
```

允许按文档类型增加字段，但不能删除核心身份、状态、版本、知识基线和接替关系。`supersedes` 始终是数组，`superseded_by` 是单个 doc ID 或 `null`。

校验工具收敛为 M1 建立的单一检查脚本 `scripts/check_docs.py`（manifest 模式），一次性覆盖全部结构校验：

1. doc / knowledge / asset ID 全仓唯一；
2. 相对链接可达（除登记的 legacy allowlist）；
3. `knowledge_release` 可解析（`pre-static-*` 基线或 release lock 中的合法 ID）；
4. canonical 知识具有有效 `source_ref`；
5. release-lock 中每个路径与 SHA-256 一致；
6. 状态转换合法（按 §7 各 doc_type 枚举）；
7. 工作包不绕过 approved spec（有 `acceptance_refs` 且上游为 approved）。

该脚本进入 CI，任何失败阻止文档/知识发布与计划状态前移。`document-metadata.schema.json` 与 `knowledge-artifact.schema.json` 降为**后置可选增强**：仅当出现检查脚本无法表达的复杂约束（跨字段条件、外部词表联动）时再引入，避免单人项目维护三套校验工具。历史文档在 M0 登记为 `legacy-exempt`，无需一次性补齐元数据；一旦被实质修订或提升为当前文档，就必须通过检查脚本。

### 6.4 版本规则

- major：改变业务语义、合同、不变量、权限边界或删除兼容行为；
- minor：向后兼容地增加字段、知识、范围或验收项；
- patch：不改变语义的订正、澄清和链接修复；
- 只复核未改内容：仅更新 `last_reviewed_at`，版本不变；
- 已发布知识内容一律新建版本文件，不能原位改写；
- 当前产品/规格文档只有在历史消费者无须恢复旧正文时才允许原位 patch；语义变化或需保留历史解释时创建新版本并填写 `supersedes`。

## 7. 文档生命周期

各文档类型使用自己的状态枚举，不能混用：

| doc_type | 必填附加字段 | 合法状态与转换 |
|---|---|---|
| design/specification | `decision_refs`、`knowledge_release` | draft → review → approved → superseded → archived |
| architecture | `decision_refs`、`applies_to` | draft → review → approved → superseded → archived |
| product | `decision_refs` | draft → review → canonical → superseded → archived |
| state/navigation/governance | `applies_to` | draft → current → superseded → archived |
| plan/work-item | `depends_on`、`acceptance_refs` | proposed → active ↔ blocked → completed/cancelled → archived |
| decision | `decided_at`、`authority` | proposed → accepted → amended/superseded/retired；或 rejected |
| knowledge-card/domain-handbook/taxonomy/product-mapping | `source_refs`、`authority_level`、`sensitivity` | candidate → verified → canonical → deprecated |
| source-evidence | `snapshot_id`、`sensitivity` | registered → verified → withdrawn |
| review | `subject_ref`、`findings` | open → partially-resolved → resolved/accepted-risk/obsolete |
| delivery/verification | `commit_refs`、`evidence_refs` | draft → verified → superseded → archived |
| operations | `applies_to`、`owner` | draft → active → superseded → archived |
| generated | `generator_ref`、`input_hash` | generated → superseded → archived |

通用规则：

1. 草稿不能作为实现授权；
2. 正式规格须完成决策和知识基线核对；
3. 实施改变合同前先修订规格或决策；
4. 当前文档直接订正过时内容，不无限叠加历史段；
5. 历史记录不改写事实，只增加接替说明；
6. 每次完整任务更新受影响索引、链接和 manifest；
7. 过期检查必须根据 `last_reviewed_at`、相关代码和接替关系执行，而非只看文件日期。

## 8. 禁止的旁路

- 外部文章或 Obsidian 笔记直接成为功能需求；
- 历史会话直接覆盖当前规格；
- 代码实现反向偷偷改变业务定义；
- 计划文档重复定义事实合同；
- README 复制产品规格或实时状态；
- AI 摘要单独决定指标公式和会计口径；
- 历史计划继续提供当前任务；
- 为追求目录整齐移动不可变档案或破坏机器引用。

### 8.1 端到端转换示例

以“预算版本与实际比较”为例：

1. 来源 `SRC-BUDGET-001` 在固定 coverage 中登记为专业方法来源，权威 C、敏感 public；
2. 形成 `FIN-COMPARE-004--v1.0.md` candidate，说明预算版本身份、期间和不可比条件；
3. 领域复核者用官方/权威来源补核后转为 verified，知识发布维护者纳入 release lock 后成为 canonical；
4. `budget_and_forecast` 手册引用该卡片，产品映射记录 FLOW 当前只有历史比较，预算比较需内部版本事实；
5. 因该能力改变 Comparison Contract，须由用户或明确授权者接受一项正式决策；
6. 规格据此定义 `actual_vs_budget` 的输入、版本身份、失败态和验收；
7. 唯一路线图在获得实施授权后创建稳定路径工作包；
8. 实施记录引用提交，验证记录证明版本错配返回不可比；
9. 生成的消费者索引把规格和实现反向关联到 `FIN-COMPARE-004`，但不修改已发布知识卡。

任何一步权限不明、来源冲突或数据不可得，都在当前门禁停止：内容可记录为 candidate，敏感性可标记为 restricted，决策可记录为 rejected，工作包可记录为 blocked；不得混用状态，也不得跳到下游。

## 9. 后续迁移设计

迁移须拆为七个独立批次。每批必须单独获得批准；前一批完成、提交或推送不自动授权下一批，更不授权产品代码实现。

| 批次 | 目标 | 主要产物 | 不做什么 |
|---|---|---|---|
| M0 | 建立全量清单 | 文档类型、状态、权威、接替、机器引用登记；二进制体积分布与 A/B/C/D 分级标注（§4.9） | 不移动文件 |
| M1 | 建立稳定骨架 | 新 README、起点、治理规则、路径映射、`scripts/check_docs.py` 检查脚本 | 不改产品合同 |
| M2 | 发布静态知识 v1 | 来源登记、知识卡、领域手册、产品映射、release lock；`set_knowledge_release.py` 批量切换与验证记录 | 不动态追读 Obsidian |
| M3 | 统一产品与规格 | 产品定义、架构、规格唯一当前版 | 不实施代码 |
| M4 | 统一计划 | 当前路线图与 U/O 工作包 | 不重启已完成任务 |
| M5 | 整理历史 | 归档、接替关系和兼容入口 | 不改不可变原件 |
| M6 | 全面验证 | 链接、哈希、机器引用、无上下文接续测试 | 不以文档检查代替应用验收 |

任何批次发现现有代码、测试、生成器或外部工具硬编码文档路径时，应停止该文件的移动，记录兼容策略后再继续。

每批开始前建立检查点：当前提交、文件清单哈希、不可变路径哈希和消费者清单。回滚触发条件包括不可变哈希变化、规范链接断裂、机器消费者失败、唯一事实源重复或读者测试出现关键误读。回滚使用新的前向 revert 提交恢复该批变更，不重写 Git 历史；恢复后重跑链接、消费者和哈希检查。跨批次问题只回滚受影响批次及其后继，不触碰已经验证且无依赖的早期批次。

## 10. 验收标准

### 10.1 静态知识库

- 首版 `flow-knowledge-2026-09-12.1` 的 `coverage.tsv` 与 M0 冻结的来源基线清单一一对应，并通过 source ID 唯一性、截面 ID 和基线哈希检查——验收以 M0 基线清单的 SHA-256 对账为准，**不使用写死的篇数数字**；基线冻结与发布之间若出现已登记的差异，必须在 `release.yaml` 中以 `added`/`withdrawn` delta 说明。后续版本通过继承哈希与 delta 哈希检查；
- 所有 canonical 知识都能追溯来源、截面和权威等级；
- 每个领域手册有明确边界、指标、维度、分析路径和数据要求；
- 受限知识无未授权原文、数值或文件复制；
- 静态发布的 `release-lock.yaml` 中每个路径和 SHA-256 均可解析且校验通过，旧 release lock 仍可恢复旧内容；
- 在测试环境主动取消 Obsidian 路径访问后，起点、产品定义、当前规格和路线图仍能只依赖仓库内容完成读取。

### 10.2 项目文档库

- 全仓扫描恰有一个 `doc_type: state`、身份为 `PROJECT_STATE` 且 `status: current` 的文档；恰有一个规范 `docs/50_plans/CURRENT_ROADMAP.md` 和一套 canonical 产品范围；
- 每份当前规格都能关联决策、知识版本、代码和验收入口；
- 每份历史文档都有清晰状态和接替关系；
- 对除 raw/original 字节档案外的全部 Markdown 扫描相对链接；零未登记断链，历史故意保留的旧路径必须在 allowlist 中有接替说明；
- M0 机器消费者清单中的测试、脚本、生成器、配置和外部工具路径逐项通过；
- `immutable-paths.lock.tsv` 的基线路径集合与逐文件哈希完全一致；新增批次只追加独立 delta，不改变基线文件；
- 每批由文档维护者和独立复核者签署验证结果，M2 知识发布和最终 M6 还需用户确认。

### 10.3 无上下文接续测试

M6 使用固定题集（五题，从原十题中保留信息密度最高的核心题），不临时改题：

1. FLOW 当前产品定位和明确非目标是什么？
2. 当前已实现、正在执行、被阻塞的工作分别从哪里读取？是否存在第二份可执行总计划？
3. 某项财务公式、业务方法和产品功能分别以什么文档为权威？
4. Obsidian 不可访问时是否可以继续工作，允许何时刷新？哪些目录不可移动或重写？
5. 内部材料怎样才能进入试点或产品？如何判断一个任务已经完成？

独立 Agent 最多读取 `READING_ORDER.md` 指定的 5 份起点文档作答。评分 rubric（必答事实、规范来源、允许表述、关键错误条件）附于 M6 验证记录中，随记录一并提交，不设独立版本化机制；当前状态变化导致期望答案改变时，先更新验证记录再开始盲测。通过标准：五题至少四题完全满足 rubric，且第 1、2、4 题不得命中任何关键错误；同时必须正确区分研究候选、canonical 知识、正式决策、规格、计划和交付证据。题目、rubric、期望答案、实际回答和评分作为 M6 验证记录提交。

## 11. 后续输出

本目标设计已由用户确认，但设计批准不构成目录迁移、批量文档改写或产品代码实施授权。下一阶段须单独编写“FLOW 文档与静态知识库迁移实施计划”，将 M0–M6 拆成可执行任务、文件级迁移表、兼容策略、验证命令和提交边界；该计划必须另有明确用户批准记录，之后每个迁移批次仍按 §9 单独领取。未经这些门槛，不开始实际目录优化。
