---
doc_id: FLOW-VERIFY-HOLDOUT-RESULTS-001
title: 留出泛化验收结果登记（U4）
doc_type: verification
status: verified
version: 1.0
created_at: 2026-09-24
updated_at: 2026-09-24
owner: FLOW
applies_to: repository
subject_ref: codex/damai-logistics-data-audit@1153724
commit_refs: ["1153724"]
evidence_refs: [
  "validation/financial_reports/holdout_runs/2026-09-24/",
  "validation/financial_reports/oracle/sf_2026h1.yaml",
  "validation/financial_reports/oracle/tencent_fy2025.yaml",
  "validation/financial_reports/oracle/zto_2026q1.yaml",
  "scripts/holdout_u4_run.py",
]
---

# 留出泛化验收结果登记（U4）

> 规程：oracle-register §4（首跑原始失败全部保留；不得为通过而调参）。
> Harness：`scripts/holdout_u4_run.py`（自动适配器选择 = 系统现状；
> diff 三级分类 matched / mismatched / not_comparable；行名匹配为确定性归一匹配，
> 多候选不猜测从严判 not_comparable）。

## 1. 首跑（2026-09-24，系统现状，零适配）

| 样本 | 适配器 | 抽取行数 | matched | mismatched | not_comparable | 结论 |
|---|---|---|---|---|---|---|
| sf_2026h1 | cn_ashare_table（自动选中） | 0 | 0 | 0 | 137 / 137 | **首跑失败（原始保留）**：半年报表头为「2026 年 6 月 30 日合并资产负债表」「合并及公司利润表」等合版标题，适配器按定报独占标题定位，三表均未定位（warnings 原文：「未定位到报表：合并利润表、合并现金流量表、合并资产负债表」） |
| tencent_fy2025 | 无（显式降级） | 0 | 0 | 0 | 32 / 32 | **首跑失败（原始保留）**：UnsupportedLayoutError，各适配器得分 cn_ashare_table=0 / hk_traditional_text=1 / hk_results_announcement=0，低于启用阈值——282 页年报全文版式未适配（符合 manifest 登记预期） |
| zto_2026q1 | hk_traditional_text（自动选中） | 0 | 0 | 0 | 30 / 30 | **首跑失败（原始保留）**：StatementExtractionError「未在提示页 106±5 内定位到『合併損益表』页首标题」——年报页码提示对 15 页业绩公告不适用 |

三样本 199 行 oracle 全部 not_comparable，0 行进入值比对。这与留出设计预期一致
（三份均为未适配版式/新公司），首跑价值在于锁定"系统现状对未见版式的显式降级行为"：
**三样本均无伪造输出、无静默错值**——降级路径全部显式抛错/告警，这是正确行为。

## 2. 原始证据

- 抽取原始输出与逐行 diff：`validation/financial_reports/holdout_runs/2026-09-24/`
  （`*_extracted.yaml` + `*_diff.json` + `summary.json`）；
- oracle 文件哈希：sf_2026h1 `16cf22eb…bf69`、tencent_fy2025 `561f31c2…6914`、
  zto_2026q1 `1050cc03…b99f`（manifest key_items_precise 段登记）；
- 人工介入计数：三样本在首跑前均未用于适配或调参（介入次数 0）。

## 3. 后续（修复后须遵守）

按 manifest rule：修复后该样本不再称留出，须按 oracle-register §3 补新候选；
修复过程若接触样本原文进行调参，须在 §5 污染史登记并降级为回归集。
