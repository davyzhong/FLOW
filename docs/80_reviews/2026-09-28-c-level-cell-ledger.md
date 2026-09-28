---
doc_id: FLOW-REVIEW-C-LEVEL-CELL-LEDGER-20260928
title: 公开财报 C 级逐格台账首版与数量差异审计
doc_type: review
status: partially-resolved
version: 1.2
created_at: 2026-09-28
updated_at: 2026-09-28
owner: FLOW
applies_to: public-analysis
subject_ref: main@1439a064
findings: [confirmed-42-exceptions-ledger, jdl-222-cell-ledger, suspected-109-candidate-membership-reconstructed]
review_refs: [FLOW-REVIEW-ADJUDICATION-20260926, FLOW-REVIEW-C-LEVEL-BASELINE-20260928]
---

# 公开财报 C 级逐格台账首版与数量差异审计

## 结论

本版建立了三个版本化审计资产：42 格已确认异常、JDL 交叉评表 222 格、以及 109 疑点的五个分组记录。它们是后续逐格原件核查的工作底稿，**不是 C 级通过结论**。

逐行解析底层冻结评审表后，可枚举候选组为：BABA FY2020 资产负债表 current 列28格；阿里七份报告现金流56格；阿里股权投资14格；菜鸟非流动限定10格；JDL归属疑点4格。共112条组成员记录。FY2020「股权证券及其他投资」`value_current=9,927`同时属于BABA current与阿里股权投资两组；按公司/报告/报表/行/列/候选值去重后为111格。交叉评逐材料统计是 BABA FY2020 36、FY2021 10、FY2022 10、FY2023 9、FY2024 10、FY2025 10、FY2026 10、Cainiao 10、JDL 4，合计109。候选清单除 BABA FY2020 外均与逐材料计数相等；FY2020 被枚举为38，超出的两格正是「股权证券及其他投资」`value_begin=9,927`与`value_end=4,234`。它们被单独标记`excess_two_vs_FY2020_material_count_unresolved`，而非擅自删掉。原 PDF（SHA-256 `82065040738c226229951aa1b31f05fc05657ad61a432a8ad2cfa67825391de4`）物理第41页/印刷页39显示流动资产下“证券投资”2019/2020人民币值为9,927/4,234，另有非流动资产的“证券投资”行；这支持必须保留流动限定，也确认`value_current=9,927`不能替代2020比较值，但不能单独证明两格是否纳入109分母。若排除两格则计数正好109，现有裁决文字仍未证明应排除它们，需按原件与原始评审口径裁定。原裁决按问题组相加为121，不能直接当作去重单元格总数。

## 固定来源与复现

| 资产 | 路径 | 数量与身份 |
|---|---|---|
| 已确认异常表 | `validation/financial_reports/review-ledgers/confirmed-42-exceptions-v1.csv` | 42 格：菜鸟 19、JDL 22、阿里 1；JDL 22 已随抽取 v2 排除，菜鸟列对齐与 BABA FY2023 prior 尚待修复 |
| JDL 逐格底表 | `validation/financial_reports/review-ledgers/jdl-222-cell-reconciliation-v1.csv` | 222 格：22 格为已确认权益变动表误入资产负债表，200 格仍标 unknown，不计通过 |
| JDL 评审值快照 | `validation/financial_reports/review-inputs/jdl_review_values_v1.csv` | 来源为本地忽略目录评审 bundle，bundle SHA-256 `748d7d3de96c312ed76d11effe5ec1fb3a00f614908bfc05155e2237e7f1f4cf`；中文原 PDF SHA-256 `809957cc3f42a77227963ef327cc74e08abf4666d91f0866b0aa6e3d50b85c5c`；可读英文版 SHA-256 `32a99c3a4341a32db84073eeb93c9679969b0ad8216514707cdf9d2dd1825009` |
| 109 疑点分组底表 | `validation/financial_reports/review-ledgers/suspected-109-group-reconciliation-v1.csv` | 原裁决五组 121 格；底层逐行重建112条组成员，扣1格重叠得111唯一格，与109摘要差2 |
| 逐格候选集 | `validation/financial_reports/review-ledgers/suspected-109-cell-candidates-v1.csv` | 112条组成员，按来源单元格去重111格；109格普通候选 + FY2020两格溢出候选（单列未决状态） |
| 候选输入快照 | `validation/financial_reports/review-inputs/suspected_109_candidate_cells_v1.csv` | 112条；冻结9份bundle路径与SHA、组归属、报表/行列/候选值，生成器不依赖CI中的忽略目录 |

生成器：`scripts/build_public_c_level_ledgers.py`。回归：`scripts/tests/test_public_c_level_ledgers.py`。运行 `python3 scripts/build_public_c_level_ledgers.py` 可确定性重建台账；`--snapshot-suspicion-sources work/ai-cross-review-bundle` 仅用于从本机忽略目录重建候选输入快照，不要覆盖已跟踪冻结快照。

## 状态解释

- **42 已确认异常**：台账把每格绑定到公司、期间、行列、抽取值、源 PDF 路径/SHA 和实现状态。尚待修复项为菜鸟 19 格与阿里 FY2023 1 格；登记入表不等于修复。
- **JDL 222 格**：来自交叉评输入表。22 格由旧/新 YAML 差异精确识别为权益变动表误入资产负债表，已在 JDL v2 排除；其余 200 格仍无逐行原文页码/坐标与数值裁定。英文版文本可读只提供复核条件，不自动构成已核验。
- **109 疑点**：已重建111格候选，其中109格处于一般未裁定状态，另2格为 FY2020 股权投资行的期初/期末候选，超出逐材料36格的计数。它们与109分母是否纳入尚未裁定；先按 PDF 的列头/流动性限定复核这两格并对原评审计数口径，再定成员身份。不得为了凑109而静默丢弃。

## 下一步及局限

1. 原件复核 FY2020 两格溢出候选（期初9927、期末4234），核清 current/non-current 限定及评审计数口径；若原作者底稿仍无法把逐格总数闭合到109，结案为“评审摘要的109分母不可完全复现”，保留候选及其未决状态，然后继续下一步。
2. 用冻结英文 PDF 按报表、行项、期间和原始列头复核 JDL 200 格，填写原文值/空值、PDF 物理页与印刷页、表头/行坐标及裁定；不能只以数值在页上出现作为匹配证据。
3. 42 异常待修复项按测试先行单项处理：菜鸟空列不借邻值；BABA FY2023 prior 补抽；JDL 已以 v2 修复并已有同 SHA CI 证据。
4. 原始 PDF 不可变；复核只新增派生台账。常驻开发/演示数据库不用于测试。

本报告不改变 `CURRENT_ROADMAP` 的 C 级出口标准。未知格不可计作正确，C 级仍未通过。
