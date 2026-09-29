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

## 4. 新留出首跑（2026-09-29，系统现状，零适配）

前置：U04 旧三样本适配器回归 199/199（run `2026-09-29-adapter-v4`）；准确 SHA CI
run `36511316012` 17/17 success（提交 `229069ca`，解析器代码与 `1b313cb` 相同、仅
CI 配置差异）。运行 ID `2026-09-29-holdout-first-run`，按 oracle-register §4 全量
保留原始输出，未调参。

| 样本 | 适配器 | 抽取行数 | matched | mismatched | not_comparable | 结论 |
|---|---|---|---|---|---|---|
| xiaomi_2026h1 | 无（显式降级） | 0 | 0 | 0 | 25 / 25 | **首跑失败（原始保留）**：UnsupportedLayoutError，各适配器得分 cn_ashare_table=0 / hk_traditional_text=1 / hk_results_announcement=1。harness 已按登记指向英文版 `XIAOMI_2026_interim_report_e.pdf`（与 oracle 同源），失败为真实版式泛化失败：小米中期报告版式无适配器 |
| alibaba_fy2027q1 | hk_traditional_text（页锚命中后失败） | 0 | 0 | 0 | 15 / 15 | **首跑失败（原始保留）**：StatementExtractionError「未在提示页 106±5 内定位到『合併損益表』页首标题」——106/107/108/112 为 `hk_traditional_text` 硬编码的京东物流年报页锚，对 26 页简体季度公告必然失效；阿里季度公告版式无适配器 |

两样本合计 40 行 oracle 全部 not_comparable，0 行进入值比对。**归因**：均为版式
泛化失败（解析器为按公司/页码硬编码适配器架构），非输入缺项、非文件身份错误、
非静默错值；两样本降级路径均显式抛错，无伪造输出，行为符合设计预期。

原始证据：`validation/financial_reports/holdout_runs/2026-09-29-holdout-first-run/`
（`*_extracted.yaml` + `*_diff.json` + `summary.json`）。oracle 哈希：xiaomi
`104f1eeb…31d36`、alibaba `1b6fb5e2…0ace9`（manifest 登记值）。人工介入计数：0
（两样本均未用于适配或调参；首跑后仅做只读取证）。

按 oracle-register §4.5：若使用该两样本开发适配器，则自动降为回归集，并按 §3
启用备选候选（yunda_2026h1 / jdl_2026h1）补新留出；届时在 §5 污染史登记。
