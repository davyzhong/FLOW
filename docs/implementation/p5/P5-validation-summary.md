# P5 反向解析验证 — 三公司证据汇总（2026-09-06）

> 对应：主计划 WS-4（D041-2、D042、D046 步骤 3）；规格 `2026-09-05-flow-metric-dictionary-design.md` §10。
> 样本原文：`docs/knowledge-base/02_research/original/p5_samples/`（SHA-256 溯源清单见该目录 README）。

## 1. 样本与抽取结果

| 公司 | 报告 | 准则 | 抽取产物 | 行项目 | 勾稽 |
|---|---|---|---|---|---|
| 顺丰控股 002352.SZ | 2026 一季报 | CAS | `sf_2026q1_statements.yaml` | 163 | 报表内 20/20；跨文档 12/12（`sf_2026q1_diff_report.md`） |
| 腾讯控股 0700.HK | 2026 Q2 业绩公告 | IFRS + Non-IFRS | `tencent_2026q2_statements.yaml` | 20 | 收入分部加总 ✓、毛利链 ✓、期内盈利归属 ✓、IFRS→Non-IFRS 调节链 ✓（`scripts/p5_extract_tencent.py` 断言） |
| 京东物流 2618.HK | FY2025 年报 | IFRS | `jdl_2025fy_statements.yaml` | 118 | IFRS 勾稽 24/24（毛利/除税前逐项/年度利润归属/资产=权益+负债/现金桥/财状表现金=现金流年末，两期全验） |

抽取器：A 股 `p5_extract_statements.py`（表头特征定位）、港股 `p5_extract_jdl.py`（繁体文本行解析 + 附注号识别）、`p5_extract_tencent.py`（业绩公告锚点 + 调节表勾稽）。全部从原始 PDF 现解析，锚点缺失即失败，不硬编码数字。

## 2. 系统内呈现（T4.2）

三公司已通过 `scripts/seed_statement_reports.py` 导入 `statement_report`/`statement_line_item`（迁移 0011），`GET /api/v1/statements` 列表与 `/statements` 页面（KPI 卡 + 瀑布 + 环形 + 现金流柱 + 四表全量表）均按报告切换呈现；数值保持披露原值与单位（顺丰/京东物流千元、腾讯百万元，随 `unit_note` 记录）。

## 3. 指标计算与披露比对（T4.3，已有证据）

- 事实层：`statement_facts.yaml` + `scripts/p5_build_fact_store.py`/`p5_query_facts.py`，报表项目经 `item_alias_map_v0.yaml` 归一为事实，`metric_coverage_matrix.md` 记录指标库 40 通用指标的可计算覆盖；
- 抽取值与披露值一致性（抽样锚点，全部一致）：
  - 顺丰 2026Q1：营业收入 74,142,121 千元、归母净利润 2,525,728 千元 —— 与一季报「主要会计数据」及 FY2025 年报分季度列一致（12/12 跨文档核对）；
  - 腾讯 2Q2026：收入 204,785 百万、归母 56,022 百万、Non-IFRS 归母 68,415 百万 —— 与业绩公告收益表及调节表逐项闭合；
  - 京东物流 FY2025：收入 217,146,986 千元、年度利润 6,890,045 千元、资产总额 124,599,558 千元 —— 与年报财务概要及三表勾稽全一致；
- 报告视图重建：`sf_2026q1_report_view.html`（五季度趋势 + 利润瀑布）、`tencent_2026q2_report_view.html`（IFRS→Non-IFRS 调节瀑布）、`sf_vs_jdl` 同业对比与杜邦树（`p5_build_report_view.py`）。

**尚未完成（如实记录）**：三公司统一的「完整分析报告反向生成 + 全行项目逐项 diff 表」将由 WS-5 报告管线接入后产出（四表一注作为正式报告类型从冻结快照渲染），届时差异三级分类（口径差异/解析误差/披露缺失）覆盖到全部行项目。

## 4. 结论

P5 首批三公司（CAS + IFRS×2、物流 + 互联网）的反向解析链路已全通：原始 PDF → 结构化行项目 → 勾稽验证 → 系统落库 → 图形化呈现 → 指标计算。抽取值与披露值在全部已验证锚点上一致，未发现解析误差类差异；「准确性承诺」（D039/D041）在公开真实财报上初步成立，完整逐项比对随 WS-5 收口。
