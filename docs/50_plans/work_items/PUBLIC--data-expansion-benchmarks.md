---
doc_id: FLOW-WP-PUBLIC-DATA-EXPANSION-001
title: 数据扩张、行业基准与性能容量基线（T11）
doc_type: work-item
status: active
version: 1.0
created_at: 2026-09-15
updated_at: 2026-09-15
owner: FLOW
applies_to: public-analysis
roadmap_phase: 3
depends_on: [FLOW-WP-PUBLIC-C-EXIT-001]
acceptance_refs: [roadmap-unique-invariant]
gates: [PUBLIC-C-EXIT]
---

# T11：数据扩张 + 行业基准 + 10× 性能容量基线

> 门禁：C 级出口（T09）通过。扩张先于内部工作台数据面，二者共用底座。

## C1 数据扩张（5→15 家 / 14→80 份）

- 行业优先级：物流 → 电商 → SaaS（对照 docs/competitive/logistics-deep-dive）；
- 每批 5 家：抽取 → L0 基准（管线保真）→ L1 抽样核验（每家 ≥20 点）→
  发布冻结 → 快照；
- 报告身份沿用 source_pdf + supersedes 链；别名映射走新版本文件，不覆盖。

## C2 行业基准

- 先接入公开可得基准（Wind/同花顺 iFinD 手工快照、上市公司行业中位数聚合），
  记录来源、期间、样本集合；杜邦对照表在 dashboard 呈现时标注口径；
- 禁止无来源基准进入正式数字通道（D049 缺失不补造）。

## G2 性能容量基线（10×）

- 目标规模：≥150 份报告 / ≥15 公司下，事实查询 P95 < 阈值（用户裁决，
  建议 500ms）、覆盖矩阵生成 < 阈值、报告渲染 < 阈值；
- 方法：脚本化压测（seed 翻倍数据 → 计时 → 记录 baseline.json）→
  回归阈值进 CI 可选；
- 交付：`docs/60_delivery/`性能基线报告 + 可复跑压测脚本。

## 验收

按批交付、按批过门禁；性能不低于批准阈值；全部数字有来源与复算路径。
