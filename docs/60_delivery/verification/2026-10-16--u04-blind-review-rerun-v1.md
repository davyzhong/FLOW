---
doc_id: FLOW-VERIFY-U04-BLIND-RERUN-20261016-001
title: U04 盲评复评验证（旧三样本 199/199 全绿）
doc_type: verification
status: draft
version: "1.0"
created_at: 2026-10-16
updated_at: 2026-10-16
owner: FLOW
commit_refs: "[780a5307]"
evidence_refs: "[holdout-run-2026-10-16-blind-review-rerun]"
applies_to: public-financial-reports
supersedes: []
superseded_by: null
---

# U04 盲评复评验证

## 结论

C 级条件 5（盲评复评）**通过**。旧三样本（顺丰/腾讯/中通）在时间线迁移后的当前 HEAD 上重跑，
199/199 逐行匹配、零 mismatch、零 not_comparable。本次为盲评（抽取管线无预知 oracle 内容），
运行 ID `2026-10-16-blind-review-rerun`。

## 运行结果

| 样本 | 适配器 | 总行 | 匹配 | mismatch | not_comparable |
|---|---|---|---|---|---|
| 顺丰 sf_2026h1 | cn_ashare_table | 137 | 137 | 0 | 0 |
| 腾讯 tencent_fy2025 | hk_traditional_text | 32 | 32 | 0 | 0 |
| 中通 zto_2026q1 | hk_results_announcement | 30 | 30 | 0 | 0 |
| **合计** | | **199** | **199** | **0** | **0** |

## 运行环境

- 提交：`780a5307`（C-3 合并后 HEAD）
- 运行 ID：`2026-10-16-blind-review-rerun`
- 原始输出：`validation/financial_reports/holdout_runs/2026-10-16-blind-review-rerun/`

## C 级条件对账更新

| 条件 | 状态 | 变化 |
|---|---|---|
| 1: L0 挂 CI | ✅ 已挂（非阻断信号灯，CI job `l0-baseline`） | **新满足**（用户裁决 1C） |
| 2: 完整独立 oracle | ❌ 0/14（资源限制，非技术问题） | 不变 |
| 3: L1 100% | ✅ 1776/1776 | 不变 |
| 4: 泛化留出 | ❌ 小米 0/25、阿里 0/15、yunda 0/20、jdl 0/25 | 不变（用户裁决 2A：不扩大） |
| 5: 盲评复评 | ✅ **199/199 全绿** | **新满足** |
| 6: 溯源/supersedes | ✅ | 不变 |

**C 纍计：4/6 条件满足（条件 2、4 如实 No-Go）。整体 C 级仍为 No-Go（维持诚实标准，用户裁决 3A）。
条件 2 需 14 份报告各配独立 oracle（资源密集）；条件 4 需新样本适配器开发。两者列入后续迭代。**
