# 经营分析轨执行计划（O 系列）

- 制定日期：2026-09-09；依据：[D050](../../knowledge-base/04_decisions/DECISION_LOG.md)、[OP 方法论规格](../specs/2026-09-09-operations-track-methodology.md)、D045/D046 双轨结构
- 性质：经营轨（双轨第二轨）执行计划。与财务轨 [统一计划 U1–U10](2026-09-07-unified-next-plan.md) 并行；**财务轨优先级不变**（D046 步骤 1），经营轨任务在财务轨断点空档或并行会话中领取，文件层面与 U 系列任务不共享改动。
- 纪律：沿用统一计划完成动作——勾选 → PROJECT_STATE 滚动 → 提交推送 → CI 绿才算 done；TDD 每条先写正例+反例。

## 背景

经营轨现状仅为 `/operations` 只读演示页（D045）。D046 步骤 2 要求经营轨数据定义由知识库提炼；2026-09-09 用户导入外部 SOP 资料，经分析判断采纳为方法论骨架（D050），本计划把方法论落为系统框架。

## 任务队列

| ID | 任务 | 验收要点 | 状态 |
|---|---|---|---|
| O1 | 数据定义合同：`config/operations/operations_track_v1.yaml` 六主题注册表 + pydantic 加载器 + TDD | availability 分层标注；L2/L3 条目不得挂财报 formula_ref；口径标签必带；`not_applicable` typed 状态 | **doing（本次交付）** |
| O2 | L1 指标计算接线：结果层指标（趋势/同比/结构/比率）复用指标库 facts 与 U2 原语出数 | 财报样本（sf/tencent/zto）可算条目出数正确；L2/L3 全部 not_applicable；守恒桥残差显式 | todo |
| O3 | 经营分析条目报告：六主题客观分析条目 + 报告渲染（复用 objective 渲染链） | 每条事实陈述四要素（值/基准/口径/来源）；数学分解标注非因果 | todo |
| O4 | `/operations` 看板改版：OP-4 信息架构，DB→typed API→Next.js | 先总体后细分；数字可溯源；L2/L3 板块「待内部数据」态展示 | todo |
| O5 | L2/L3 内部数据接入与业务事件簿数据模型 | 依赖内部数据授权（同 U9 前提）；事件簿表结构先行定义 | todo（数据依赖） |

## 执行顺序

```
O1 → O2 → O3 → O4 →（内部数据授权）→ O5
```

O2–O4 依赖 O1 合同冻结；O5 依赖 U9 同款数据授权，表结构（业务事件簿）可在 O3 后先行定义。

## 断点

2026-09-09：O1 进行中——本计划与 `operations_track_v1.yaml`、加载器、测试同批交付。后续领取者从 O1 验收（`pytest services/api/tests/analysis/test_operations_catalog.py`）开始。

## 变更日志

| 日期 | 变更 | 操作者 |
|---|---|---|
| 2026-09-09 | 初版：D050 采纳 SOP 方法论后建立 O1–O5 队列，O1 同批启动 | ZCode |
