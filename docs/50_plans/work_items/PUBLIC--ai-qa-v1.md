---
doc_id: FLOW-WP-PUBLIC-AI-QA-V1-001
title: AI 问数 v1 与 100 问评测集（T12）
doc_type: work-item
status: blocked
version: 1.0
created_at: 2026-09-15
updated_at: 2026-09-15
owner: FLOW
applies_to: public-analysis
roadmap_phase: 3
decision_refs: [D054]
gates: [PUBLIC-C-EXIT, PUBLIC-DATA-EXPANSION]
---

# T12：AI 问数 v1（检索引用型）与评测集

> 门禁：C 级出口 + 首批数据扩张完成（语料与事实面足够出题）。
> v2 多步受控计算、v3 反事实建模另行裁决，不在本包。

## D1 范围（v1 = 检索 + 引用，不做计算）

- 问题 → 事实检索（指标/报表行/期间过滤）→ 组织答案；
- 每个答案必须附事实引用（报告 + 期间 + 行项目 + 溯源 id）；
- 无事实支撑 → 拒答并说明缺口（缺数据 ≠ 编造）；
- 临时计算类问题转「提议 → 复算」管线（T10-B6 组件），本包只预留接口。

## 评测集（100 问）

- 构成：事实查询 60 / 口径解释 20 / 应拒答 20（含陷阱题：期间错配、
  单位换算、口径混淆、无数据公司）；
- 每题标注：期望答案、必须引用的事实 id、允许表述差异；
- 验收：命中率 ≥ 约定阈值（用户裁决，建议 ≥90%），拒答类零误答，
  全部引用可回链事实库；
- 评测进 CI（LLM 评测 job 可选 nightly），评测集版本化、题目不得泄漏进提示词。

## 依赖

- 评测模型走既有 copilot provider 抽象（多模型路由属 D3，另行裁决）；
- 评测成本预算与数据保护条款（T14-G4 合规尽调输出）先行确认。
