---
doc_id: FLOW-REV-DAMAI-DATA-20260924
title: FLOW 项目完成度与大麦物流全量演示数据就绪度审查
doc_type: review
status: open
version: 1.0
created_at: 2026-09-24
updated_at: 2026-09-24
last_reviewed_at: 2026-09-24
owner: FLOW
subject_ref: main@63f99b2
findings: [strategic-completion-50-60, no-one-click-demo-loader, internal-workbench-25-35, c-level-exit-missing-holdout-eval, four-level-validation-not-started, strategic-completion-partial, public-exit-pending, internal-workbench-incomplete, ci-doc-metadata-failing, current-state-stale, demo-data-not-loaded, demo-data-scope-insufficient]
applies_to: repository
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053, D054]
supersedes: []
superseded_by: null
source_refs:
  - docs/00_start_here/PROJECT_STATE.md
  - docs/50_plans/CURRENT_ROADMAP.md
  - docs/20_product/PRODUCT_SCOPE.md
  - docs/20_product/PRODUCT_PRINCIPLES.md
evidence_refs:
  - "https://github.com/davyzhong/FLOW/actions/runs/35864060350"
confidentiality: project-internal
---

# FLOW 项目完成度与“大麦物流”全量演示数据就绪度审查

> 审查基线：`main@63f99b2`，2026-09-24。本文是一次事实审查，不替代
> [PROJECT_STATE](../00_start_here/PROJECT_STATE.md) 与
> [CURRENT_ROADMAP](../50_plans/CURRENT_ROADMAP.md) 的权威关系。后续数据设计获批后，
> 应另建正式规格与实施计划。

## 1. 结论

FLOW 不是“功能尚未开发”，而是“共享底座和公开财报模块已较成熟，最终目标产品尚未闭环”。
按 2026-09-13 战略目标审视：

- 共享工程底座约处于 **80%–90%** 成熟度；
- 公开财报模块约处于 **75%–85%**，功能链已具备，C 级出口仍缺独立盲评与留出验收；
- 企业内部月度财务经营分析工作台仅约 **25%–35%**，已有数据接入、指标、调查、发布和
  企业/周期底层对象，但目标工作流、双 AI 报告链和企业配置/记忆尚未形成完整产品；
- 四级真实企业验证尚未启动，可视为 **0%–10%**；
- 综合战略完成度只能估为 **50%–60%**。这个区间是阶段证据判断，不是代码行数统计。

“很多页面看不到内容”的直接原因不只是缺数据，而是以下四项叠加：

1. 当前 Docker 服务未运行，数据库链路不可用；
2. 仓库已有演示数据，但没有在普通启动流程中自动装载；
3. 内部经营、公开财报、分析 Finding、冻结发布分别依赖不同对象，没有统一的一键演示装载器；
4. 既有内部演示包规模仅约 2,630 万元年收入，且只含 15 个运行指标所需窄事实，无法代表
   菜鸟级物流企业，也无法覆盖完整四表、预算预测、现金与全部指标库条目。

因此，正确改造对象不是“一份 Excel”，而是一个可重复生成、可一键灌入、可验收的
**跨域演示数据发行版**。

## 2. 目标与现状对照

| 目标阶段 | 当前事实 | 判断 | 未完成项 |
|---|---|---|---|
| U8 生产就绪 | HTTPS、对象存储、发布、恢复与结构化日志已有验收证据 | 已完成 | 保持回归门禁 |
| S01 战略边界与安全 | Facts V2 领域模型、enterprise/cycle、RBAC、审计、模块边界已落地 | 已完成基础门禁 | 状态文档仍停在旧迁移头，需刷新 |
| 公开模块 C 级出口 | 财报抽取、事实、溯源、四表、经营概览、问数 v1、冻结导出已具备 | 部分完成 | 10 条抽取候选复核、独立盲评、holdout、正式 Go/No-Go |
| 数据扩张 | 14 份报告、5 家公司；10× 性能基线已有 | 进行中 | 更多公开财报与真实来源跳转闭环 |
| 内部月度工作台 | 旧物流窄切片可完成接入→指标→Finding→冻结；有企业/周期底层表 | 仅基础资产 | 持续企业空间、月度周期 UI/API、BP 受限入口、V2 事实持久化、企业配置、记忆 |
| AI 报告生产链 | Copilot 与确定性 Finding 已有 | 未达到目标 | 分析型 AI 专业版、CFO 角色 AI 管理版、两版差异、冲突队列、一次终审 |
| 四级验证 | 有工程测试与公开样本基准 | 未启动目标验收 | 连续 3 个企业月度周期、人工基准、双盲评审、20% 工时门槛 |

## 3. 当前工程健康度

### 3.1 已验证通过

- Web 单元测试：24 个测试文件、86 项测试全通过；
- Web TypeScript 类型检查通过；
- Python Ruff 与严格 MyPy 通过（189 个源文件）；
- 最新 GitHub Actions 中，data-contract、smoke、integration、migrations、unit、dashboard、
  investigations、publishing、contracts、module-boundaries 等业务作业均通过。

### 3.2 当前不能称为绿色基线的原因

- `main@63f99b2` 的 FLOW CI 总结为失败；失败点是文档元数据门禁：
  `CODE_OF_CONDUCT.md`、`CONTRIBUTING.md`、`SECURITY.md` 缺 frontmatter；
- `PROJECT_STATE.md` 更新于 2026-09-15，仍写迁移头 `0028`，实际 Alembic head 已是
  `0029_statement_provenance`；
- `docs/README.md` 仍显示迁移头 `0024`；
- `HANDOFF.md` 的基线和“下一步”停在 2026-09-19，落后于当前主线；
- 工作区存在其他 Agent 留下的未跟踪文件
  `services/api/tests/security/test_route_policy_registry.py`，本审查不纳入、不修改。

## 4. 页面为何为空：数据依赖矩阵

| 页面 | 主要数据依赖 | 现有恢复方式 | “大麦物流”发行版需要补什么 |
|---|---|---|---|
| `/` 驾驶舱 | canonical 经营/财务/预算/应收事实 + 12 个月指标快照 | `seed_dashboard_demo.py` | 大麦 24 个月事实、预算、快照、异常 |
| `/data` 数据工作台 | 工作簿、画像、映射、质量、对账、发布版本 | 手工上传 fixture | 可下载的大麦标准包与非标准包；一键导入 |
| `/investigations` | AnalysisRun、Finding、Evidence、Conclusion | dashboard seed 只生成窄样例 | 覆盖收入、成本、利润、预算、AR、现金、效率的 Findings |
| `/reports` | 已批准 Finding 的冻结快照、经营快照、发布尝试和对象存储 | 分散脚本/人工动作 | 预生成候选、已审核样例、冻结快照与可下载产物 |
| `/statements` | StatementReport + 四表行项目 + 溯源 | `seed_p5_statements.sh` | 大麦物流完整合成四表与比较期 |
| `/analysis` | 公开财报事实与四问工作台 | 依赖 StatementReport | 大麦报告的指标、主题、风险与证据 |
| `/operations` | 内部 dashboard + 公开经营披露/财报经营概览 | 两条不同链路 | 统一可选的大麦内部经营周期与大麦财报经营概览 |
| `/metric-library` | 静态治理字典 + 财报覆盖矩阵 | YAML 静态可见 | 大麦覆盖矩阵与“可算/缺失”证据，不伪造不可算指标 |

## 5. 既有演示数据的能力与缺口

仓库当前 canonical fixture 已经有 24 个月：2024-09 至 2026-08，其中后 12 个月为分析期、
前 12 个月为同比期。数据量为：

- 3 个组织节点、2 个客户群、16 个客户、8 个物流产品、4 个区域；
- 3,072 条经营事实、432 条财务实际、120 条预算、1,920 条应收回款；
- 15 个物流运行指标可以计算；
- 12 个月指标快照与一个分析运行可以通过 `seed_dashboard_demo.py` 生成。

但它不足以承担新的全页面演示：

- 公司名仍是“FLOW 供应链集团”；
- 分析期收入合计约 2,630 万元，远低于菜鸟参考量级；
- 仅 9 个管理科目，不能生成完整利润表、资产负债表和现金流量表；
- 预算只有 5 类指标，没有 forecast；
- 应收数据没有发票号，现金只有经营现金流，没有现金余额和完整现金桥；
- 没有统一生成 StatementReport、财报覆盖矩阵、报告冻结、发布尝试的入口；
- 指标知识库约 65 个条目不等于每个企业数据包都可计算，必须明确区分“指标已定义”和
  “大麦数据可算”。

## 6. 外部规模锚点

建议使用公开数据作“量级与结构锚”，不复制真实公司明细：

- 菜鸟 FY2025 收入为人民币 1,012.72 亿元，调整后 EBITA 为 3.02 亿元；FY2024 收入
  990.20 亿元。来源：阿里巴巴 FY2025 年报/业绩披露；
- 菜鸟 FY2023 招股材料披露业务收入结构约为国际物流 47.4%、中国物流 46.2%、科技及
  其他 6.4%，以及国际包裹、中国履约订单、仓网等经营量级；
- 京东物流 FY2025 收入为人民币 2,171.47 亿元、毛利 197.68 亿元，收入同比增长 18.8%；
  外部一体化供应链客户收入 359 亿元、客户 91,161 家、仓库超过 1,600 个。

正式造数时，大麦物流应以菜鸟约千亿元收入规模和业务结构为主，以京东物流的毛利率、
客户与仓网效率关系作为合理性护栏。所有大麦数据必须标记为 synthetic，不能伪装成上述
公司的真实披露。

## 7. 三种实施深度

### A. 现有 fixture 改名与放大

改名为大麦物流、按比例放大金额、保留现有 24 个月和 15 个指标。

- 优点：最快；
- 缺点：`/statements`、完整报表、指标覆盖、双版本报告仍不完整；
- 结论：不满足“所有页面和功能都能验证”。

### B. 跨域全量演示数据发行版（推荐）

建立 `damai-logistics-demo-v1`：24 个月内部事实 + 预算/预测 + 应收/回款/现金 + 完整合成
四表 + 多主题异常 + Finding/Evidence + 快照/报告/发布样例，并提供幂等的一键 seed 与
覆盖验收矩阵。默认年度收入约 1,050–1,150 亿元，业务结构以菜鸟为主，保留可解释的季节性、
同比、预算差异、客户集中、跨境波动、成本冲击和应收风险。

- 优点：不改数据库 schema 即可最大化覆盖当前产品；页面可见性和数据合理性可自动验收；
- 缺点：需要同时维护内部事实与财报事实两套投影，并明确哪些指标只是定义、尚不可算；
- 结论：最符合当前诉求。

### C. 36 个月日级/票级数字孪生

增加日级订单、运单、仓库、线路、发票、现金流水与预测版本，必要时扩 schema。

- 优点：可支持更深的运营诊断和压力测试；
- 缺点：范围大、可能触发 schema 迁移红线，且当前页面大多消费月度事实；
- 结论：应作为 B 完成后的第二阶段，不应阻塞当前全页面演示。

## 8. 推荐裁决

采用方案 B，时间范围固定为 24 个月：12 个月当前分析期 + 12 个月上年同期；当前分析期
同时生成月度预算和滚动预测。最近 12 个月保留月度明细即可满足现有页面；如后续验证日级
功能，再在不改变基线口径的前提下扩充日级附加包。

设计获批后再进入正式规格、独立规格审查、实施计划、测试先行和代码实现。实现不得通过
“所有指标强行填值”制造假覆盖；不具备输入的数据必须保持结构化 unavailable，并在覆盖矩阵中
说明缺失项。

## 9. 证据来源

- 仓库内：`PROJECT_STATE.md`、`CURRENT_ROADMAP.md`、`PRODUCT_SCOPE.md`、
  `PRODUCT_PRINCIPLES.md`、战略重构设计 V1.1、Alembic heads、页面/API/fixture 源码、
  GitHub Actions run `35864060350`；
- [阿里巴巴 FY2025 年报（HKEX）](https://www.hkexnews.hk/listedco/listconews/sehk/2025/0515/2025051500869.pdf)；
- [菜鸟招股申请版本（HKEX）](https://www1.hkexnews.hk/listedco/listconews/sehk/2023/1222/sehk23120700201.pdf)；
- [京东物流 FY2025 年度业绩公告（HKEX）](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0305/2026030500918.pdf)。
