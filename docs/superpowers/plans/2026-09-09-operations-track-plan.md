---
doc_id: FLOW-PLAN-OPS-000
title: 经营轨 O 系列计划（历史）
doc_type: plan
status: archived
version: 1.0
created_at: 2026-09-07
updated_at: 2026-09-12
owner: FLOW
depends_on: []
acceptance_refs: []
superseded_by: FLOW-PLAN-CURRENT
do_not_execute: true
---

> **已接替**：唯一路线图见 [docs/50_plans/CURRENT_ROADMAP.md](../../../docs/50_plans/CURRENT_ROADMAP.md)。本文件保留任务细节与完成证据，不得领取新任务。

# 经营分析轨执行计划（O 系列）

- 制定日期：2026-09-09；依据：[D050](../../knowledge-base/04_decisions/DECISION_LOG.md)、[OP 方法论规格](../specs/2026-09-09-operations-track-methodology.md)、D045/D046 双轨结构
- 性质：经营轨（双轨第二轨）执行计划。与财务轨 [统一计划 U1–U10](2026-09-07-unified-next-plan.md) 并行；**财务轨优先级不变**（D046 步骤 1），经营轨任务在财务轨断点空档或并行会话中领取，文件层面与 U 系列任务不共享改动。
- 纪律：沿用统一计划完成动作——勾选 → PROJECT_STATE 滚动 → 提交推送 → CI 绿才算 done；TDD 每条先写正例+反例。

## 背景

经营轨现状仅为 `/operations` 只读演示页（D045）。D046 步骤 2 要求经营轨数据定义由知识库提炼；2026-09-09 用户导入外部 SOP 资料，经分析判断采纳为方法论骨架（D050），本计划把方法论落为系统框架。

## 任务队列

| ID | 任务 | 验收要点 | 状态 |
|---|---|---|---|
| O1 | 数据定义合同：`config/operations/operations_track_v1.yaml` 六主题注册表 + pydantic 加载器 + TDD | availability 分层标注；L2/L3 条目不得挂财报 formula_ref；口径标签必带；`not_applicable` typed 状态 | **done**（`ff75240`） |
| O2 | L1 指标计算接线：结果层指标（趋势/同比/结构/比率）复用指标库 facts 与 U2 原语出数 | 财报样本可算条目出数正确；L2/L3 全部 not_applicable；守恒桥残差显式；经营事实严格按报告期间匹配 | **done（财报 L1 + 字典周转 + 顺丰/腾讯/菜鸟泛化 + 菜鸟年度分部系列 + 经营指标 typed 中间层 `operations/facts.py`：OperatingFact 合同、严格期间筛选不摊分不回退、同频可比基期、来源 SHA-256 前缀校验、Q1 stub 如实标注 unaudited；公开期间目录与无财报期间概览 typed API；zto 未抽取如实标注。CI 同口径 operations/api/analysis 175 通过、web 组件测试/tsc/eslint 绿，2026-09-11 复验）** |
| O3 | 经营分析条目报告：六主题客观分析条目 + 报告渲染（复用 objective 渲染链） | 每条事实陈述四要素（值/基准/口径/来源）；行动章显式标注不在客观范围；经营报告进入统一发布与下载链 | **done**（六主题 XLSX/PPTX/HTML/PDF 渲染；`PublicationAttempt` 追加式正式发布、对象存储与统一下载；报告中心经营快照列表/格式选择/历史记录；跨格式黄金值与 production 闭环验证；迁移 `0024`） |
| O4 | `/operations` 看板改版：OP-4 信息架构，DB→typed API→Next.js | 先总体后细分；数字可溯源；L2/L3 板块「待内部数据」态展示 | **done（slice-3 `debc715` 达成全部验收要点：管理关注 + 六主题网格、事实卡片带基准/口径、L2/L3「待内部数据」态）** |
| O5 | L2/L3 内部数据接入与业务事件簿数据模型 | 依赖内部数据授权（同 U9 前提）；事件簿表结构先行定义 | todo（数据依赖） |

## 执行顺序

```
O1 → O2 → O3 → O4 →（内部数据授权）→ O5
```

O2–O4 依赖 O1 合同冻结；O5 依赖 U9 同款数据授权，表结构（业务事件簿）可在 O3 后先行定义。

**2026-09-10 数据输入就绪（ZCode）**：菜鸟运营指标序列已抽取为 `docs/implementation/p5/cainiao_operating_metrics.yaml`——Selected Operating Data（国际包裹量/国内履约单量 FY2021-2023 + 两个 Q1 stub，百万件）、Non-IFRS 调整序列（经调整净利/EBITA 及利润率，含调节口径）、FY2023 业务线收入占比（国际 47.4%/中国 46.2%/技术其他 6.4%）、网络快照（2023-06-30：200+ 国家、2 e-Hub、1,100+ 仓、17 万驿站、2,700+ 干线）。管理层/申报口径如实分层标注；O2/O3 渲染菜鸟主题时以此为经营数据输入（与 `cainiao_segment_series.yaml` 财务分部序列互补）。

## 断点

2026-09-12：**O2/O3 done**——经营事实、严格期间对齐和公开期间 UI 已完成；经营快照已进入统一发布与下载链。迁移 `0024_operations_publication` 允许 objective statement 与 operations overview 各自从 v1 独立版本化，并让一次发布尝试严格归属且只归属一种快照。重复冻结以业务内容幂等，生产栈实测 PPTX/XLSX/HTML 发布成功且下载 SHA-256 与登记一致；缺失对象返回 typed 409。当前 O 系列唯一未完成项为 O5，依赖内部数据授权（同 U9 前提）。

## 变更日志

| 日期 | 变更 | 操作者 |
|---|---|---|
| 2026-09-09 | 初版：D050 采纳 SOP 方法论后建立 O1–O5 队列，O1 同批启动 | ZCode |
| 2026-09-12 | O2/O3 收口：typed 经营事实、严格期间对齐、六主题多格式渲染、统一发布下载与报告中心 | Codex |
