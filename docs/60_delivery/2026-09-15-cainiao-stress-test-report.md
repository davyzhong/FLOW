---
doc_id: FLOW-DELIVERY-CAINIAO-STRESS-20260915
title: C 级出口回归压力测试报告——菜鸟子集 + 抽取错误候选抓捕
doc_type: delivery
status: verified
version: 1.0
created_at: 2026-09-15
updated_at: 2026-09-15
owner: FLOW
applies_to: public-analysis
subject_ref: main@db9ac83
commit_refs: ["5a9e788", "c9dcd47", "44acd16"]
evidence_refs: [
  "config/statements/answer_set_l1.yaml",
  "scripts/accuracy_benchmark.py",
  "scripts/build_answer_set_l1.py",
]
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053]
gates: [PUBLIC-C-EXIT]
pre_registered_rules: docs/50_plans/work_items/PUBLIC--c-level-exit-protocol.md §3.7
---

# C 级出口回归压力测试报告（菜鸟子集）

> 按 §3.7 预注册规则执行：回归层指定最难一家（菜鸟招股书），失败归因区分
> 「管线退步」vs「源文件固难」。本报告为 C 级出口 Go/No-Go 的证据之一。

## 1. 执行结果

| 指标 | 结果 |
|---|---|
| 菜鸟子集锚定 | 468 条全部带页锚（weak 模式 100%——英文招股书，行名简繁/语言不一致，仅数值同页弱锚） |
| 菜鸟子集值比对 | 全部通过（0 不一致） |
| 全量 L1 | 1775 条已定位值：锚失效 0、值不一致 0 |
| 全量 L0 | 1454 值：一致 1454 |

## 2. 压力测试抓捕：10 条抽取错误候选

定位过程发现 10 条抽取值在源 PDF 文本层**全文档不存在**（含括号负数形态
`(9,083)`→`-9083` 的归一检索），按预注册归因规则判定为**抽取错误候选**
（非管线退步、非源文件固难——是「答案集里的值在原文中找不到」）：

| # | 源 PDF | 报表 | 行名 | 列 | 记录值 | 取证 |
|---|---|---|---|---|---|---|
| 1–8 | BABA_FY2020/2021/2022/2024/2025/2026_annual_results.pdf | 合并利润表 | 歸屬於非控制性權益損益 | 本期/上期 | -9083、-7652 等 | 值串仅作为 29,083 / 67,652 等无关数字的子串出现；负数括号形态全 PDF 0 命中（以 FY2020 p38 为例：淨損失行实际值为 2,534/2,872/4,067/6,529 系） |
| 9–10 | JDL_FY2025_annual_report.pdf | 合并现金流量表 | 存放受限制現金 / 已付利息 | 本期/上期 | 见答案集 unlocated | 全 PDF 0 命中 |

**处置（按 Q4 全量 100% 零容忍）**：
1. 这 10 条不得进入 L1 通过集（当前已通过「不进答案集 entries」实现）；
2. 待人工翻页查源：确认 P5 抽取当时读到的原始数字（可能是列读错位、
   正负号方向、或单位段落差异），修正抽取 YAML（新版本文件，不改原件）；
3. 修正后重跑 `build_answer_set_l1.py` + `accuracy_benchmark.py`，
   覆盖率应 ≥ 99.4%（1785/1795）且双零维持。

**处置状态更新（2026-09-25，P1 关闭）**：10 条全部复核完毕，**均为误报，
抽取值正确**，非抽取错误——
- 1–8（BABA NCI）：港交所公告将亏损行印为正数，YAML 按会计符号记负值，
  行名+绝对值同页成立。已通过新定位模式 `strong-sign-flip-loss-row` 重新入库；
- 9–10（JDL 现金流量表）：主表页为图像层无文本，已渲染 PNG 目视核对无误，
  通过新模式 `visual-verified`（证据 SHA fail-closed）重新入库。
- 复核顺带抓获两处真错误（本测试未捕获）：alibaba_2023fy 上期列 23 项
  整列误抓、alibaba_2019fy NCI 上期 -406 误抓，均已修正（详见
  validation/financial_reports/corrections.md §2）。
- 重跑结果：1794/1794 覆盖率 100%（2019fy NCI 上期改 null 故总数 -1），
  锚失效 0 / 值不一致 0 / 未入库 0。C 级出口此前置项已关闭。

## 3. 结论

- 回归压力测试**通过并产出实质战果**：菜鸟弱锚场景 468 条全对；
- 抓获 10 条抽取错误候选——零容忍阈值（Q4）在第一次真跑中即证明其价值；
- C 级出口 Go/No-Go 前置项更新：上述 10 条人工查源关闭后方可进入盲评。
