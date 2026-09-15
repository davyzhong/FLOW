---
doc_id: FLOW-WP-PUBLIC-PROV-RESTATE-MCP-001
title: 数据点级溯源、重述检测、AI 起草与只读 MCP（T10）
doc_type: work-item
status: completed
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

# T10：数据点级溯源、重述检测、AI 起草与只读 MCP（四个子包）

> 门禁：C 级出口（T09）通过后领取。每个子包独立分支独立验收，规格先行。

## B3 数据点级溯源闭环（S-3 / 清单 3.11）

- 事实库每数值点补 `(page, bbox|anchor)` 定位（抽取层写入，迁移 + 代码）；
- 前端报告/表格点击数值 → 定位原文页码与高亮；
- 验收：随机抽 20 条人工核对全部命中原文位置；定位写入进入 L1 基准
  answer_set 的必填列。

## B4 重述与更正检测（S-4）

- `statement_report.supersedes_id`（迁移）+ 同身份多版本报告检测；
- 同期间重述 → 自动差异报告（逐行 delta + 归因字段）；
- 验收：构造重述样本（阿里 FY 某期改写版）输出完整差异清单且不覆盖历史
  （append-only 语义与 publication_attempt 一致）。

## B6 差异说明自动起草 + MD&A（O-09 / 清单 2.8）

- AI 仅起草叙事文本；全部数字经确定性引擎产出并附证据引用；
- 「提议表达式 → 程序复算 → 一致性校验 → 报告候选」（D054 工程化）；
- 验收：5 份报告出稿、每个数字可点击回源、经分专员终审界面可用。

## B5 事实库只读 MCP server（S-1）

- 三个工具起步：`get_facts`、`get_metric`、`get_provenance`；只读，
  无写入/发布/授权面；复用 require_action 服务账号通道（identity JSON）；
- 验收：外部 LLM（Claude/其他）经 MCP 取到带溯源的事实；越权工具调用
  fail-closed；审计事件完整。

## 验收纪律

每子包：批准规格 → 红灯测试 → 实现 → 全链测试 → 同 SHA CI 全绿；
禁止以「演示可用」代替验收。
