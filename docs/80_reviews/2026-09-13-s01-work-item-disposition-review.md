---
doc_id: FLOW-REVIEW-S01-DISPOSITION-001
title: S01 后旧工作包逐项裁决备忘（U09+O05、U10）草案
doc_type: review
status: open
version: 1.0
created_at: 2026-09-13
updated_at: 2026-09-13
last_reviewed_at: 2026-09-13
owner: FLOW
subject_ref: FLOW-WI-S01
findings: []
applies_to: s01-parallel-execution
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D049, D051]
supersedes: []
superseded_by: null
source_refs:
  - docs/50_plans/work_items/U09-O05--authorized-internal-pilot.md
  - docs/50_plans/work_items/U10--v1-1-evidence-decision.md
  - docs/50_plans/work_items/S01--post-u8-boundary-contract-security.md
  - docs/superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md
related_code: []
commit_refs: []
evidence_refs: []
confidentiality: project-internal
---

# S01 后旧工作包逐项裁决备忘（草案）

> 性质：本备忘是 Task 6B 的**裁决建议草案**，供主协调者与用户裁决。
> 本备忘不修改任何工作包状态文件；U09+O05、U10 的 status 变更须由主协调者在裁决通过后另行执行。
> 对应 S01 退出条件：「旧 U9/O5、U10 已逐项裁决」。

## 一、裁决框架

S01 战略重置后，系统边界为三层两模块：**公开模块（C 级）** 与 **内部工作台**。
旧工作包的每一项能力按以下四类裁决：

| 类别 | 含义 |
|---|---|
| 保留重命名 | 能力目标不变，按新边界重新命名/归属后保留 |
| 拆入公开 C | 能力迁入公开模块（C 级）范围，按公开数据纪律执行 |
| 拆入内部工作台 | 能力迁入内部工作台范围，受 RBAC/审计门禁约束 |
| 取消 | 与战略重置冲突或无证据支撑，取消（默认 hold 语义见各节） |

## 二、U09+O05（FLOW-WI-U09O05，授权内部经营分析试点，现 status: blocked）

| 原范围项 | 裁决建议 | 理由 |
|---|---|---|
| 主数据与版本身份（OPS-MASTER-001 蓝本） | **拆入内部工作台**（保留重命名为「企业空间与月度周期身份」） | S01 Task 5（迁移 0025）已承接企业/月度周期身份；主数据合同作为内部工作台的前置数据纪律保留 |
| 多维盈利守恒 | **拆入内部工作台** | 属内部经营分析能力，依赖授权内部数据，受 GOV-AUTH-001 门禁约束 |
| 窄主题分析包（OPS-PROFIT-001） | **拆入内部工作台** | 同上；公开模块只做 C 级公开财报链，不承接内部盈利主题 |
| 一报一会记录闭环 | **保留重命名**（迁入内部工作台的会议/报告记录能力） | 与新边界的内部工作台报告链一致 |
| 经营事件簿接入 | **拆入内部工作台**，授权门禁解除前维持 blocked | 硬依赖内部业务事件数据授权（GOV-AUTH-001） |
| 「可先做」项（脱敏数据包结构、字段映射、接入清单） | **保留**，作为内部工作台的准备性 backlog | 无授权期间唯一允许推进的部分 |
| 「禁止」项（公开年度数据摊月、伪造 L2/L3、未授权数值进产品） | **保留为永久纪律**，并入内部工作台验收标准 | 纪律不因裁决失效 |

整体建议：U09+O05 不取消，**整体迁入内部工作台范围并维持 blocked**，直至 GOV-AUTH-001 授权门禁解除。

## 三、U10（FLOW-WI-U10，V1.1 证据决策 go/hold/drop，现 status: blocked）

| 原范围项 | 裁决建议 | 理由 |
|---|---|---|
| 基于 U4/U8/U9O05 证据的 V1.1 候选能力逐项 go/hold/drop | **保留重命名**为「S01 后证据决策」，推迟到 S01 退出后执行 | U9/O5 证据链因授权门禁缺失，无证据项按原门禁默认 hold；S01 已吸收部分 V1.1 候选（模块边界、Facts V2、RBAC），决策包需按新边界重写候选清单 |
| 证据决策包底稿（90_archive/plans/2026-09-07-v11-evidence-decision-pack.md） | **保留**为底稿档案，不作为当前决策依据 | 底稿基于重置前边界，需修订后重新引用 |
| 「无证据项默认 hold」门禁 | **保留为永久纪律** | 与本项目证据门禁体系一致 |

整体建议：U10 不取消，**保留并推迟**，在 S01 退出条件满足、且 U09+O05 授权状态明确后，由主协调者发起正式 D 系列决策。

## 四、派生的 gated backlog 建议（仅建议正文，不创建 backlog 文件）

### 建议 B1：公开模块 C 级完整报告链（gated）

- **建议内容**：基于公开财报（年度/季度）的 C 级完整报告链：四表一注解析 → 指标计算 → 图形化分析（趋势/结构/同业对比/杜邦树）→ 报告发布。
- **门禁（gate）**：S01 全部退出条件满足 + 公开模块入口（Task 2C 已建 `/public`）完成集成 + 发布链路（report:freeze/report:publish，owner=Sol 接线后）CI 绿。
- **不属于本 backlog**：内部企业数据、未授权数值、月度周期。

### 建议 B2：内部月度工作台功能（gated）

- **建议内容**：企业空间内的月度分析周期工作台：数据接收 → 映射确认 → 指标快照 → 调查证据链 → 内部报告；含一报一会记录闭环与经营事件簿接入准备项。
- **门禁（gate）**：GOV-AUTH-001 内部数据授权解除 + S01 退出 + RBAC/审计持久化（0026 迁移）落地。
- **准备期可做**：脱敏数据包结构、字段映射、业务事件簿接入清单（沿用 U09+O05「可先做」项）。

## 五、未决项（留主协调者）

1. U09+O05 / U10 状态文件的正式 status 变更（本备忘仅建议）；
2. B1/B2 是否登记为正式 backlog 工作包及 doc_id 分配；
3. GOV-AUTH-001 授权门禁的责任人与解除时间窗口。
