---
doc_id: FLOW-REVIEW-C-LEVEL-CELL-LEDGER-20260928
title: 公开财报 C 级逐格台账与来源复核
doc_type: review
status: partially-resolved
version: 1.8
created_at: 2026-09-28
updated_at: 2026-09-29
owner: FLOW
applies_to: public-analysis
subject_ref: main@db646f45
findings: [adjudicated-42-exceptions-v2, jdl-222-cell-ledger, jdl-readable-source-crosswalk, suspected-109-candidate-membership-reconstructed, suspected-109-semantic-adjudications-v2]
review_refs: [FLOW-REVIEW-ADJUDICATION-20260926, FLOW-REVIEW-C-LEVEL-BASELINE-20260928]
---

# 公开财报 C 级逐格台账首版与数量差异审计

## 结论

2026-09-29 最新裁决：111个唯一候选现均有逐格语义裁决，详见`validation/financial_reports/review-ledgers/suspected-109-cell-adjudications-v2.csv`和`validation/financial_reports/review-ledgers/suspected-109-group-adjudication-v2.csv`。109格组成可重建主集；两格BABA FY2020流动证券投资期初9,927、期末4,234是真实原件行值，但缺原评审筛选底稿，仍为109摘要分母未决。主集没有数值错误；问题是源行范围/报表身份限定以及一个评审bundle别名错误。组摘要BABA FY2020报告36/重建28（差8）和阿里股权报告15/重建14（差1）无法从已冻结逐格输入复原，明确结案为摘要成员不可重建，不伪称109组统计完全复现。当前C级仍未通过；下一步是对现金流范围、流动/非流动身份实施版本化行映射修正并跑种子/L1/P5隔离验证。

本报告建立了 42 条历史异常主张的初版和审定版、JDL 交叉评表 222 格、以及 109 疑点的五个分组记录。经逐格回到菜鸟招股书原件审定，初版将19个有效年度/比较期数值误标成空列错误；审定版补齐报告年度、来源期间与具体列，原版保留作审计历史。报告仍**不是 C 级通过结论**。

2026-09-28 更新：JDL 来源逐格复核提交`fdc96d63146e0ed8cb12e75a50f488dd3015398f`对应准确 SHA CI run `36404144739` 17/17 success。原 200 格已逐格匹配冻结英文版的报表行、期间列和值/空值。184 格（179 数值、5 源表破折号）来源行匹配；16 格定位到印刷页106的独立「合并综合收益表」。本轮已通过实现修正将这16格的8行×2列从利润表拆分到综合收益表；“年度利润/本公司所有者/非控制性权益”重复行按报表身份保留。JDL v3 与 L1 v3 不覆盖冻结 v2，使用物理页106/107提示，摘要页不得回退。实现提交`db646f45c43141468a2b4ee10a9114f0f141f066`的准确 SHA CI run `36427598983`为17/17 success。独立库实测 L0 1514/1514、L1 1775锚全部复现且值匹配、数据库匹配零缺失；相关测试通过，但外部 oracle/盲评、holdout 和其余42异常/109候选仍未结案，故本报告与 C 级均非通过结论。

逐行解析底层冻结评审表后，可枚举候选组为：BABA FY2020 资产负债表 current 列28格；阿里七份报告现金流56格；阿里股权投资14格；菜鸟非流动限定10格；JDL归属疑点4格。共112条组成员记录。FY2020「股权证券及其他投资」`value_current=9,927`同时属于BABA current与阿里股权投资两组；按公司/报告/报表/行/列/候选值去重后为111格。交叉评逐材料统计是 BABA FY2020 36、FY2021 10、FY2022 10、FY2023 9、FY2024 10、FY2025 10、FY2026 10、Cainiao 10、JDL 4，合计109。候选清单除 BABA FY2020 外均与逐材料计数相等；FY2020 被枚举为38，超出的两格正是「股权证券及其他投资」`value_begin=9,927`与`value_end=4,234`。它们被单独标记`excess_two_vs_FY2020_material_count_unresolved`，而非擅自删掉。原 PDF（SHA-256 `82065040738c226229951aa1b31f05fc05657ad61a432a8ad2cfa67825391de4`）物理第41页/印刷页39显示流动资产下“证券投资”2019/2020人民币值为9,927/4,234，另有非流动资产的“证券投资”行；这支持必须保留流动限定，也确认`value_current=9,927`不能替代2020比较值，但不能单独证明两格是否纳入109分母。若排除两格则计数正好109，现有裁决文字仍未证明应排除它们，需按原件与原始评审口径裁定。原裁决按问题组相加为121，不能直接当作去重单元格总数。

2026-09-28 菜鸟19条主张审定：原始招股书 SHA `3e2c367958eacf3bb50c165204a1093383381f5cdb9d8af506636b880b54b13c`。物理第474页现金流量表、第475页融资活动、第466页资产负债表列头显示 FY2021/FY2022/FY2023；FY2022 报表的上期列是 FY2021 比较数。19条的原值均可在相应原文年度列找到，并与`cainiao_2021fy_statements.yaml`或`cainiao_2022fy_statements.yaml`一致。故19条均为因缺失报告年度/比较期间身份造成的误报，不是要清空的空值；未修改抽取 YAML。新文件`confirmed-42-adjudicated-v2.csv`记录报告年、来源期间、来源列、物理页、原件 SHA、状态及逐格裁决；旧`confirmed-42-exceptions-v1.csv`保持原样作为历史证据。审定台账生成器对年度 YAML 做数值断言，避免身份错配回归。

## 固定来源与复现

| 资产 | 路径 | 数量与身份 |
|---|---|---|
| 初版异常表（历史，不作当前分类依据） | `validation/financial_reports/review-ledgers/confirmed-42-exceptions-v1.csv` | 42 格：菜鸟19条原主张、JDL22格、阿里1格；保留初始标签供追溯 |
| 审定异常表 | `validation/financial_reports/review-ledgers/confirmed-42-adjudicated-v2.csv` | 42条逐项审定；菜鸟19条全部确认为有效来源值/比较值（无需修复），JDL22格已修复，BABA FY2023比较期1格仍待修复 |
| JDL 逐格底表 | `validation/financial_reports/review-ledgers/jdl-222-cell-reconciliation-v1.csv` | 222 格：22 格为已确认权益变动表误入资产负债表；余下 200 格已逐格附原文行证据，184 格来源匹配、16 格现已拆分为独立综合收益表身份 |
| JDL 可读版交叉表 | `validation/financial_reports/review-inputs/jdl_readable_twin_crosswalk_v1.csv` | 对应 200 个唯一 ledger ID；记录物理/印刷页、文本行、原文行、原中文 PDF 与可读英文版 SHA。英文版 SHA-256 `32a99c3a4341a32db84073eeb93c9679969b0ad8216514707cdf9d2dd1825009` |
| JDL 评审值快照 | `validation/financial_reports/review-inputs/jdl_review_values_v1.csv` | 来源为本地忽略目录评审 bundle，bundle SHA-256 `748d7d3de96c312ed76d11effe5ec1fb3a00f614908bfc05155e2237e7f1f4cf`；中文原 PDF SHA-256 `809957cc3f42a77227963ef327cc74e08abf4666d91f0866b0aa6e3d50b85c5c`；可读英文版 SHA-256 `32a99c3a4341a32db84073eeb93c9679969b0ad8216514707cdf9d2dd1825009` |
| 109 疑点分组底表 | `validation/financial_reports/review-ledgers/suspected-109-group-reconciliation-v1.csv` | 原裁决五组 121 格；底层逐行重建112条组成员，扣1格重叠得111唯一格，与109摘要差2 |
| 逐格候选集 | `validation/financial_reports/review-ledgers/suspected-109-cell-candidates-v1.csv` | 112条组成员，按来源单元格去重111格；109格普通候选 + FY2020两格溢出候选（单列未决状态） |
| 候选输入快照 | `validation/financial_reports/review-inputs/suspected_109_candidate_cells_v1.csv` | 112条；冻结9份bundle路径与SHA、组归属、报表/行列/候选值，生成器不依赖CI中的忽略目录 |

生成器：`scripts/build_public_c_level_ledgers.py`。回归：`scripts/tests/test_public_c_level_ledgers.py`。运行 `python3 scripts/build_public_c_level_ledgers.py` 可确定性重建台账；`--snapshot-suspicion-sources work/ai-cross-review-bundle` 仅用于从本机忽略目录重建候选输入快照，不要覆盖已跟踪冻结快照。

## 状态解释

- **42 条历史异常主张**：审定版中菜鸟19条已证实为报告期间未标清导致的误报；JDL22格已在 v2 修复；仅阿里 FY2023 比较期1格仍是已确认抽取遗漏。不要用初版42条总数描述当前缺陷数。
- **JDL 222 格**：来自交叉评输入表。22 格由旧/新 YAML 差异精确识别为权益变动表误入资产负债表，已在 JDL v2 排除。其余 200 格逐格映射到同版式英文年报的报表行与期间列：179 个数值、5 个空值/破折号匹配；16 格已由 JDL v3 分为独立综合收益表，重复行身份按 `statement_type` 区分。独立隔离测试库实测 L0 1514/1514、L1 1775条覆盖全、页锚复验/值匹配/入库匹配均零差异。L1含 strong 981、weak 775、sign-flip 15、visual 4；弱锚总体仍需 oracle 评估。该结果不证明外部独立复核、整体准确率阈值、holdout或 C 级出口通过。
- **109 疑点**：已重建111格候选，其中109格处于一般未裁定状态，另2格为 FY2020 股权投资行的期初/期末候选，超出逐材料36格的计数。它们与109分母是否纳入尚未裁定；先按 PDF 的列头/流动性限定复核这两格并对原评审计数口径，再定成员身份。不得为了凑109而静默丢弃。

## 下一步及局限

1. 原件复核 FY2020 两格溢出候选（期初9927、期末4234），核清 current/non-current 限定及评审计数口径；若原作者底稿仍无法把逐格总数闭合到109，结案为“评审摘要的109分母不可完全复现”，保留候选及其未决状态，然后继续下一步。
2. JDL 16 格拆分、同名行身份、页提示及勾稽已完成；后续对照独立 oracle 复核弱锚与分类，再将本资产作为回归证据，不覆盖冻结 v2。
3. 唯一尚待修复的已确认抽取异常是 BABA FY2023 比较期1格；菜鸟19条无需改抽取，JDL22格已以 v2 修复并已有同 SHA CI 证据。
4. 原始 PDF 不可变；复核只新增派生台账。常驻开发/演示数据库不用于测试。

本报告不改变 `CURRENT_ROADMAP` 的 C 级出口标准。16 格语义未决及其余全量基准/异常处置不可计作通过，C 级仍未通过。
