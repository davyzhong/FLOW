---
doc_id: FLOW-REVIEW-C-LEVEL-BASELINE-20260928
title: 公开财报 C 级来源基线与 JDL 复核准备
doc_type: review
status: partially-resolved
version: 1.2
created_at: 2026-09-28
updated_at: 2026-09-28
owner: FLOW
applies_to: public-analysis
subject_ref: main@f1ab4283
findings: [jdl-equity-page-range-error, jdl-readable-source-available, cross-review-bundle-coverage-difference]
review_refs: [FLOW-REVIEW-AI-CROSS-RESULT-20260925, FLOW-REVIEW-ADJUDICATION-20260926]
---

# 公开财报 C 级来源基线与 JDL 复核准备

## 结论

公开财报 C 级出口仍未通过。第一轮只读复核确认：交叉评裁决指出的 42 项真实抽取错误具有明确实现根因；JDL 可读英文版年报已经纳入仓库，200 格复核输入条件已具备；但这些 200 格尚未逐项人工/机器结合核验。当前又发现交叉评输入证据束与当前 JDL 抽取/答案集数量不一致，必须先统一记录身份和单元格再宣称覆盖。

## 来源与可复现信息

| 对象 | 路径 | SHA-256 / 观察 |
|---|---|---|
| JDL 中文原始年报 | `docs/knowledge-base/02_research/original/p5_samples/jd_logistics_2618/JDL_FY2025_annual_report.pdf` | `809957cc3f42a77227963ef327cc74e08abf4666d91f0866b0aa6e3d50b85c5c`；受不可变清单保护，未修改 |
| JDL 英文可读版年报 | `validation/financial_reports/original/jdl_fy2025_readable/JDL_FY2025_annual_report_EN.pdf` | `32a99c3a4341a32db84073eeb93c9679969b0ad8216514707cdf9d2dd1825009`；210页；与既有裁决记录 SHA 一致，文本可读 |
| 当前 JDL 抽取 YAML | `docs/implementation/p5/jdl_2025fy_statements.yaml` | 保留为历史输入，不原地重写 |
| 当前 L1 答案集 | `config/statements/answer_set_l1.yaml` | 文件 SHA-256 `8adb229687eb8fd8496418d1751a336b5912ca83ef8b403db89e505195609ceb`；228 条 JDL 锚记录 |
| 独立交叉评材料表 | `work/ai-cross-review-bundle/JDL_FY2025_annual_report.md` | 本地 ignored 工作产物，不是版本化权威；表中222行，含8个空值单元格 |

交叉评总体统计仍按其原口径保留：1,530 格 = 1,183 未发现异常 + 42 已确认异常 + 105 已核对但存疑 + 200 无法完整核对；109 个存疑标签中有4个属于 JDL，且已包含在200格内，禁止重复加总。42 项由菜鸟19、JDL 22、阿里1组成。

## 已复现的 JDL 抽取缺陷

### 2026-09-28 修复状态

已按测试先行修正`end_page=110`的页界限错误：资产负债表不再纳入物理第110页（印刷页109）的权益变动表。新版本抽取资产位于`validation/financial_reports/corrections/jdl_2025fy_statements_v2.yaml`，来源SHA与中文原件一致，三张表分别为26/47/34行，勾稽24/24；旧P5 YAML保持原样。JDL抽取/勾稽回归18项通过。新L1答案集位于`config/statements/answer_set_l1_v2.yaml`，1,775/1,775锚可定位；该值表示定位覆盖，不代表L1数值准确率。新建隔离Compose栈迁移至0031并导入14份报告后，L0 1508/1508一致；L1页锚1775条（strong 981 / weak 775 / sign-flip 15 / visual 4），锚失效0、值不一致0、未入库0。财报目录76项与脚本目录110项测试、M1及链接检查通过。提交`5c84c81fdd3c0908891d16f8dcfe05e1d2e64b6c`的准确SHA CI run `36382657675` 17/17成功；常驻`flow`未用于测试，隔离卷已清理。

来源映射目录后缀及FY2023阿里来源错配已修正，并增加逐项路径存在性测试；答案集构建、基准与seed入口改为使用版本化JDL修订输入，旧答案集保留。代码与准确SHA CI已闭环，但不得据此宣称C级通过。剩余200格、42异常与109口径疑点仍须规范化逐格审计。

JDL 抽取器在 `services/api/src/flow_api/statements/extraction.py` 将资产负债表抽取结束页设为 `end_page=110`。区间按零起始页号、右端不包含解释时，PDF物理第110页（印刷页109）“Consolidated Statement of Changes in Equity”被并入资产负债表。

用现有 PDF 只读调用验证：当前资产负债表58行，包含11条权益变动表伪行；在内存中把右界设为109后，资产负债表为47行，权益变动表项目全部消失，`資產總額`、`負債總額`、`權益總額`、`權益及負債總額`等主要余额保持正确。这个行为与既有裁决的22个错误单元格一致。后续需将该边界写成自动化回归，再修实现；历史 YAML 与原 PDF 不覆盖。

## 待解决的证据束覆盖差异

- 独立评报告将 JDL 清单统计为222格，交叉评 bundle 的抽取表亦有222行。
- 当前 `answer_set_l1.yaml` 有228条 JDL 锚记录；按 statement/item/column/value 去重后有226个不同记录，其中年度利润两格重复出现一次，且答案集不包含空值。
- bundle 的222行含8个显式空值；与答案集对账时，存在若干仅在一边出现的值/空值行，不能简单把“228 对 222”解释为新增6个数值，也不能用 L1 页锚覆盖数代替逐格真值核验。
- `answer_set_sources.yaml` 的 `source_pdf_suffix` 多处与磁盘目录不匹配（例如 JDL 写为 `istics_2618/...`，实际为 `jd_logistics_2618/...`；阿里亦有 `baba_9988`/`alibaba_9988` 命名差异）。目前 L1 构建器按 sample 使用该表身份字段，未以该 suffix 定位 PDF；但这一来源映射仍须校正并增加路径存在性门禁，避免后续复核把错误路径当来源。

上述差异尚未完成逐条裁定。下一步将针对独立评审行、当前抽取 YAML 与 L1 答案记录生成规范化逐格对账：包含来源文件 SHA、报告身份、报表、行名、列名、数值/空值、页码和处置状态。先完成 JDL 22项回归及证据清单，再逐项复核原先200格；不得把“同页出现数字”作为正确行列的充分证据。

## 本轮验证边界

- 原始 JDL 中文 PDF 与英文 PDF 均只读；常驻数据库未访问。
- 英文版 PDF 逐页文本可提取。数字 token 的同页搜索只能用作定位辅助；页上数字出现不证明行名、列头或值归属正确。
- 本文不改写答案集、不更新抽取器、不作 C 级 Go/No-Go；这些应按工作包后续步骤逐次提交并复验。
