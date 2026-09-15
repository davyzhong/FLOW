---
doc_id: FLOW-REVIEW-INTEGRATED-DD-20260915
title: 整合尽调总汇与后续尽调计划（2026-09-15）
doc_type: review
status: open
version: 1.0
created_at: 2026-09-15
updated_at: 2026-09-15
last_reviewed_at: 2026-09-15
owner: FLOW
subject_ref: main@c93c896
findings: [dd-security-closed-r1, dd-multi-agent-drift-closed, dd-module-boundary-partial, dd-competitive-complete, dd-project-post-repair-done, dd-gap-accuracy-benchmark, dd-gap-performance, dd-gap-supply-chain, dd-gap-compliance, dd-gap-u4-oracle]
applies_to: repository
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053, D054]
supersedes: []
superseded_by: null
source_refs:
  - docs/80_reviews/2026-09-14-s01-multi-agent-overall-review.md
  - docs/80_reviews/2026-09-15-project-review-post-repair.md
  - docs/70_operations/2026-09-14-single-agent-takeover-plan.md
  - docs/competitive/README.md
confidentiality: project-internal
---

# 整合尽调总汇与后续尽调计划（2026-09-15）

> 目的：把多 Agent 时期与本日各会话产出的全部尽调/审查/调研合并为一份总汇，并给出后续尽调计划。事实基准 `main@c93c896`（CI 全绿 17/17 的最后一绿 SHA 为 `640cfb8`，本页为文档追加）。

## 1. 已完成的尽调（按领域）

### 1.1 安全尽调 —— 已闭环至 R1，余 R2–R4

| 尽调 | 结论 | 出处 |
|---|---|---|
| 安全规格 V1.1 三轮独立审查 | 零 P1/P2，用户批准后生效 | `docs/80_reviews/2026-09-13-security-spec-v11-glm-review.md` 等 |
| GPT 总审 F2（四阶段 ABI 缺陷） | 裁决成立，R1 已全部修复：durable AuditWriter、authorization 按 action×resource、identity JSON 严格校验、legacy cutoff 收窄 | `docs/70_operations/2026-09-14-coordination-ledger-glm.md` §6 |
| 本日复核（80_reviews 2026-09-15） | 66 路由 require_action 接线核对一致；CI 门禁清单与 workflow 一致 | `docs/80_reviews/2026-09-15-project-review-post-repair.md` |

**未闭环**：R2（治理写落地 + publishing/operations 接线 + pipeline 死代码）、R3（module-boundaries-v2 全树 AST）、R4（full-verification-v2：动态隔离/真实 CA/sentinel/双证明）。Task 6 因此维持不关闭。

### 1.2 多 Agent 执行尽调 —— 已闭环（流程类）

GPT 总审 F1–F7、三份车道修正单、接管计划 R0–R4 序列；跑偏心因（共用检出竞争、绕过合并序列、提交标题夹带、身份不可归因）已在单 Agent 模式下消除：worktree 14→1、git 身份归一、CI 同 SHA 全绿。

### 1.3 竞对与方法论尽调 —— 已完成（2026-09-15 沉淀）

- `docs/competitive/` 13 份：开源 AI 财分、商业 AI 报告、开源 BI、中国本土 BI、咨询方法论、综合定位、35 条优化清单、代码级对照矩阵（17 维度 × 精确代码路径）、AI 问数方案、顺丰 POC、行业基准数据源、物流行业深挖、MCP/数据层增量补充；
- `docs/knowledge-base/09_competitive/`：C01–C20 逐品调研 + 横向盘点（五层行业骨架）+ O-01~O-17；
- 核心结论：FLOW 的确定性计算 + 证据溯源 + 指标版本化是差异化护城河；最大缺口是 AI 问数、行业基准、数据规模、数据点级溯源与 MCP 通道。

### 1.4 项目整体尽调 —— 已完成（本日）

实现与战略重构设计 V1.1 一致；P1–P3 遗留清单见 `docs/80_reviews/2026-09-15-project-review-post-repair.md` §4（文档门禁已随 `640cfb8` 修复）。

## 2. 未尽调缺口（本次整合新识别）

| # | 缺口 | 风险 | 建议时点 |
|---|---|---|---|
| G1 | **反向解析数据质量无量化基准**：覆盖矩阵只答「能不能算」，不答「算得对不对」；阿里 FY2019 同比基数异常说明确有错配 | 高（事实库是一切的地基） | C 级出口协议执行时并入（冻结样本 + 数字级答案集 + 盲评） |
| G2 | **性能/容量尽调缺失**：事实库与报告渲染在 10× 数据量下无基线 | 中 | 数据扩张（5→15 公司）启动前 |
| G3 | **依赖供应链尽调缺失**：npm/pip 依赖漏洞与许可证扫描未见记录 | 中 | 随 R4 或下一次发布门禁 |
| G4 | **合规尽调（数据授权/隐私/信创）**：内部工作台需要企业数据授权框架 | 高（阻塞内部工作台） | C 级出口后、内部工作台启动前 |
| G5 | **U4 独立 oracle**：外部到料阻塞中，是公开模块质量裁决的前置 | 中 | 外部到料即启动 |
| G6 | **文档门禁 CI 覆盖不全**：CI 只跑 `check_docs --phase m1`，m6（链接/兼容/读者测试）仅本地可跑——本次竞对文档打断门禁即因此未在 CI 拦截到 m6 层 | 低 | 随 R2 顺带 |

## 3. 后续尽调计划

### 3.1 触发式尽调（事件驱动）

| 触发 | 尽调内容 | 验收 |
|---|---|---|
| R4 执行时 | 安全渗透面复验（动态隔离/真实 CA/sentinel）+ 依赖供应链扫描（G3） | 零 P1/P2；扫描报告入库 |
| C 级出口启动时 | 数据质量尽调（G1）：冻结样本答案集、抽取准确率/召回、重述样本对 | 基准可复算、进 CI 门禁 |
| 数据扩张启动时 | 性能基线（G2）：10× 数据量下的事实查询/矩阵生成/报告渲染耗时 | 基线文档 + 回归阈值 |
| 内部工作台启动前 | 合规尽调（G4）：数据授权框架、脱敏规程、云模型数据保护条款核验 | 授权清单 + 脱敏验收 |
| 每个大版本发布前 | 全量 review 刷新（本文件 supersedes 链） | 新 review 文档入库 |

### 3.2 周期式尽调

| 周期 | 内容 | 既有约定 |
|---|---|---|
| 季度（下次 2026-12） | 代码级对照矩阵刷新（17 维度 ✅/❌ 与代码路径） | `docs/competitive/comparison-matrix-code-level.md` §7 |
| 半年（下次 2027-03） | 竞对清单全量更新（定价/功能/融资可能过时） | `docs/competitive/optimization-checklist.md` §7 |
| 每次会话开始 | PROJECT_STATE + git log + CI 状态三点核对（防状态漂移） | 本仓库惯例 |

### 3.3 尽调纪律（从多 Agent 事故提炼）

1. 尽调结论必须锚定 SHA 与时点，禁止用过期快照下结论（GPT 总审 F-教训）；
2. 尽调发现只进 80_reviews/正式目录，不留在外部 worktree（GPT 审计七件套曾长期未入库）；
3. 「局部绿」「基本完成」不是尽调结论，只有同 SHA 全门禁绿才算；
4. 尽调与修复分离：尽调文档不夹带代码修复，修复走工作包。
