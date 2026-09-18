---
doc_id: FLOW-SPEC-metrics
title: metrics 规格域
doc_type: navigation
status: current
version: 1.1
created_at: 2026-09-12
updated_at: 2026-09-17
owner: FLOW
applies_to: specs
---

# metrics 规格域

域内规格与权威路径见 [SPEC_INDEX.md](../SPEC_INDEX.md)。规格只定义输入、输出、对象、状态、不变量、失败方式与验收，不维护进度。

## 设计输入（O-01 指标语义上下文暴露，2026-09-17 登记）

- **指标四元素同构映射**（借鉴 #21，木木自由 2024-12-09《如何理解指标》指标四元素；vault
  原文回溯 `ObsidianWiki/processed/微信知识库/木木自由/01_数据分析必备/`）：任何指标 =
  对象 + 维度 + 限定 + 值。与字典条目字段同构——metric_code/name = 对象、
  analysis_dimensions = 维度、caliber / default_caliber / alternative_calibers = 限定、
  formula + unit = 值。O-01 暴露语义上下文时按此映射生成，口径分歧走既有 governance 流程。
- **统一口径先行**（借鉴 #21，美团商家版指标体系实证）：行业参考包 v1.2
  （`config/metrics/metric_dictionary_v1_1.yaml` 顶层 `industry_reference_packs`，16 行业）
  的 financial_reference 由此登记行业口径实例；行业经营指标目录（ops_indicators）暂无
  取数源，仅作对标参考，提升须走指标新增流程。

