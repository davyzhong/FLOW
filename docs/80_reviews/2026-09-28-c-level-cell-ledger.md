---
doc_id: FLOW-REVIEW-C-LEVEL-CELL-LEDGER-20260928
title: 公开财报 C 级逐格台账首版与数量差异审计
doc_type: review
status: partially-resolved
version: 1.0
created_at: 2026-09-28
updated_at: 2026-09-28
owner: FLOW
applies_to: public-analysis
subject_ref: main@1439a064
findings: [confirmed-42-exceptions-ledger, jdl-222-cell-ledger, suspected-109-count-mismatch]
review_refs: [FLOW-REVIEW-ADJUDICATION-20260926, FLOW-REVIEW-C-LEVEL-BASELINE-20260928]
---

# 公开财报 C 级逐格台账首版与数量差异审计

## 结论

本版建立了三个版本化审计资产：42 格已确认异常、JDL 交叉评表 222 格、以及 109 疑点的五个分组记录。它们是后续逐格原件核查的工作底稿，**不是 C 级通过结论**。

首轮发现不可忽略的汇总矛盾：交叉评裁决列出分组数量 36+56+15+10+4=121。裁决只明确说明阿里股权投资组与 BABA FY2020 组有 1 格重叠，扣除后应为 120，而摘要称 109，仍差 11 格。按可见来源候选复数，BABA FY2020 当前列在冻结证据文字表中只见 28 个项目；阿里股权投资疑点的字段展开不能从现有表格直接复现 15 格。故本版保留源报告数字、记录差异，不自行补造 11 格归属。

## 固定来源与复现

| 资产 | 路径 | 数量与身份 |
|---|---|---|
| 已确认异常表 | `validation/financial_reports/review-ledgers/confirmed-42-exceptions-v1.csv` | 42 格：菜鸟 19、JDL 22、阿里 1；JDL 22 已随抽取 v2 排除，菜鸟列对齐与 BABA FY2023 prior 尚待修复 |
| JDL 逐格底表 | `validation/financial_reports/review-ledgers/jdl-222-cell-reconciliation-v1.csv` | 222 格：22 格为已确认权益变动表误入资产负债表，200 格仍标 unknown，不计通过 |
| JDL 评审值快照 | `validation/financial_reports/review-inputs/jdl_review_values_v1.csv` | 来源为本地忽略目录评审 bundle，bundle SHA-256 `748d7d3de96c312ed76d11effe5ec1fb3a00f614908bfc05155e2237e7f1f4cf`；中文原 PDF SHA-256 `809957cc3f42a77227963ef327cc74e08abf4666d91f0866b0aa6e3d50b85c5c`；可读英文版 SHA-256 `32a99c3a4341a32db84073eeb93c9679969b0ad8216514707cdf9d2dd1825009` |
| 109 疑点分组底表 | `validation/financial_reports/review-ledgers/suspected-109-group-reconciliation-v1.csv` | 原裁决五组 121 格；扣唯一明示重叠后 120；与 109 差 11；确切成员尚未恢复 |

生成器：`scripts/build_public_c_level_ledgers.py`。回归：`scripts/tests/test_public_c_level_ledgers.py`。运行 `python3 scripts/build_public_c_level_ledgers.py` 可确定性重建台账；首次快照选项只适用于再现本版，不应以可能变化的忽略目录重刷已跟踪输入。

## 状态解释

- **42 已确认异常**：台账把每格绑定到公司、期间、行列、抽取值、源 PDF 路径/SHA 和实现状态。尚待修复项为菜鸟 19 格与阿里 FY2023 1 格；登记入表不等于修复。
- **JDL 222 格**：来自交叉评输入表。22 格由旧/新 YAML 差异精确识别为权益变动表误入资产负债表，已在 JDL v2 排除；其余 200 格仍无逐行原文页码/坐标与数值裁定。英文版文本可读只提供复核条件，不自动构成已核验。
- **109 疑点**：本版只有分组核算，不能声称已逐格建立身份。继续追溯原始交叉评答案集、评审工作表与字段身份；在恢复成员清单前，不修改 109 个疑点字段合同，不把字段口径问题改判为数值错误。

## 下一步及局限

1. 追溯 109 疑点原始逐条证据/答案集，重建成员映射和去重键，解释 11 格差额后再逐项裁决。
2. 用冻结英文 PDF 按报表、行项、期间和原始列头复核 JDL 200 格，填写原文值/空值、PDF 物理页与印刷页、表头/行坐标及裁定；不能只以数值在页上出现作为匹配证据。
3. 42 异常待修复项按测试先行单项处理：菜鸟空列不借邻值；BABA FY2023 prior 补抽；JDL 已以 v2 修复并已有同 SHA CI 证据。
4. 原始 PDF 不可变；复核只新增派生台账。常驻开发/演示数据库不用于测试。

本报告不改变 `CURRENT_ROADMAP` 的 C 级出口标准。未知格不可计作正确，C 级仍未通过。
