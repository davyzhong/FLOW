# 财务报告验收数据集（A03）

本目录是客观财务分析主计划（M0/A03、M3/D03–D04）的验收基线：**验收数据集登记 + 独立参考答案规范**。

## 文件

- [`manifest.yaml`](manifest.yaml)：三份基线报告（顺丰 2026Q1、腾讯 2026Q2、京东物流 FY2025）+ 两份留出报告（腾讯 FY2025 年报 = 新期间，圆通速递 2026Q1 = 新公司）的登记与独立参考答案。

## 使用规则

1. **独立录入**：manifest 中的 expected 值由人直接阅读披露原文抄录，逐项带页/表/行定位；**禁止**用被测抽取器（`scripts/p5_extract_*.py`、`scripts/seed_statement_reports.py`）的输出生成或回填 expected——发现回填即整份作废重录。
2. **容差预登记**：行项目 exact（容差 0）；主要会计数据百分比 ±0.5 个披露末位；派生比率 ±0.1pp。执行 D03 之前不得修改容差。
3. **覆盖率口径**：分母为全部关键项目与全部报表行项目，不允许只报告通过的锚点；差异按三级分类（口径差异 / 解析误差 / 披露缺失）留痕。
4. **留出样本纪律**：留出报告只做首跑评估；原始失败全保留于 `docs/implementation/objective-analysis/holdout-results.md`；修复适配后该样本退出留出池，并登记新候选保持池非空。
5. **原文不可变**：样本 PDF 归档于 `docs/knowledge-base/02_research/original/p5_samples/`，SHA-256 溯源（圆通速递于 2026-09-06 新增下载校验）。

## 与既有证据的关系

基线三家与 P5 已验证锚点（`docs/implementation/p5/P5-validation-summary.md` §3）同源同值，但本清单按 A03 流程重新抄录并补齐定位与容差；D03 执行时以本 manifest 为唯一答案来源。
