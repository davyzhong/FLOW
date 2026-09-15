---
doc_id: FLOW-REVIEW-INTEGRATED-OPT-20260915
title: 整合优化改进建议方案（2026-09-15，待裁决）
doc_type: review
status: open
version: 1.0
created_at: 2026-09-15
updated_at: 2026-09-15
last_reviewed_at: 2026-09-15
owner: FLOW
subject_ref: main@c93c896
findings: [opt-three-sources-integrated, opt-p0-consensus-identified, opt-non-goals-confirmed, opt-roadmap-order-constraint]
applies_to: product-strategy
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D049, D052, D053, D054]
supersedes: []
superseded_by: null
source_refs:
  - docs/competitive/optimization-checklist.md
  - docs/competitive/comparison-matrix-code-level.md
  - docs/knowledge-base/09_competitive/2026-09-14-optimization-backlog.md
  - docs/competitive/2026-09-15-ai-data-layer-mcp-supplement.md
  - docs/70_operations/2026-09-14-coordination-ledger-glm.md
confidentiality: project-internal
---

# 整合优化改进建议方案（待裁决）

> **纪律声明**：本文整合三个来源的优化清单（`docs/competitive/optimization-checklist.md` 35 条、kb `09_competitive` O-01~O-17、MCP 补充 S-1~S-6）与工程收口遗留（台账 §6 R2–R4、项目 Review P2/P3），**不是任务批准，不构成第二份总计划**。任何条目进入执行须经 `docs/50_plans/CURRENT_ROADMAP.md` 按 D053 裁决，并逐项过 D049/D054 纪律（确定性内核不放松、AI 临时计算必须复算、AI 不得自行发布、缺失不补造）。

## 0. 三份清单的共识与分歧

- **共识 P0 交集**：AI 问数、行业基准、数据扩张、溯源深化——四个来源独立指向同一组缺口，可信度高。
- **口径差异**：`optimization-checklist.md` 按商业价值排（含 ~150-200 人月估算，面向 8-10 人团队 12-18 个月）；O 系列按目标产品差异化排（更贴合 D052 内部工作台）；S 系列补 2026 通道层（MCP/基准/重述）。**本方案以 CURRENT_ROADMAP 的阶段门为硬约束重新排序，不采用任何单一来源的顺序。**
- **张力点**：竞对清单的 DCF/EVA、BSC、战略框架偏投资研究/咨询叙事，与 D052「企业内部月度经营分析」定位有距离——降级为候选，标注「需用户裁决是否属于本产品」。

## 1. 分组整合方案

### A 组 · 工程收口（阻塞一切，无条件最先）

| # | 条目 | 来源 | 验收 |
|---|---|---|---|
| A1 | R2：route-policy-v3 治理写落地 + publishing/operations 串行接线 + pipeline 死代码删除 | 台账 §6-1 | 治理写 7 条走策略化 403/落地；CI 全绿 |
| A2 | R3：module-boundaries-v2（全树 AST + path-glob manifest） | 台账 §6-2 | 全树扫描无越权导入 |
| A3 | R4：full-verification-v2（动态隔离/真实 CA/sentinel/双证明） | 台账 §6-3 | 恢复序列全绿；Task 6 可关闭 |
| A4 | 工程卫生包：`var/metric_library_audit.jsonl` 移出版本控制 + .gitignore；ownership_v1.yaml owner 改角色域命名；dashboard 404 数据态重发快照 | Review P3 | 逐项清零 |
| A5 | 文档门禁 m6 入 CI（当前只有 m1，竞对文档曾因此打断门禁未拦截） | 尽调 G6 | ci.yml 增加 m6 job 或并入 static-python |
| A6 | 反向解析基数异常数据层修复（阿里 FY2019 等季度列错配年度列） | Review P3-8 | 并入 B2 基准验收 |

### B 组 · 公开模块 C 级出口（CURRENT_ROADMAP 第 3 顺位）

| # | 条目 | 来源 | 验收 |
|---|---|---|---|
| B1 | C 级出口协议执行：冻结样本 + company-level holdout + 独立盲评 | 设计 §14.1 | 协议四项全过 |
| B2 | 反向解析准确率基准（数字级答案集，可复算进 CI） | S-2 + G1 + 清单 3.5 | 每样本准确率可见，回归即红 |
| B3 | 数据点级溯源闭环（页码/坐标 + 前端点击定位） | S-3 + 清单 3.11 | 抽 20 条人工核对全中 |
| B4 | 重述与更正检测（事实库 supersedes 链） | S-4 | 构造重述样本输出差异清单 |
| B5 | 事实库只读 MCP server（facts/指标/溯源三工具起步） | S-1 | 外部 LLM 经 MCP 取到带溯源事实 |
| B6 | 差异说明自动起草 + MD&A 生成（AI 只写叙事，数字全部来自确定性引擎） | O-09 + 清单 2.8 + demo-poc 升级路径 | 5 分钟出稿、引用全事实、经人工终审 |

### C 组 · 数据与分析深化（支撑 C 级出口质量与差异化）

| # | 条目 | 来源 | 工作量参考 |
|---|---|---|---|
| C1 | 数据扩张：5→15 公司、14→80 份财报（物流/电商/SaaS 三行业优先） | 清单 1.3 + logistics-deep-dive | 6-9 人月 |
| C2 | 行业基准数据（第三方接入或自建聚合，杜邦对照表） | 清单 1.1 + industry-benchmark 方案 + matrix D5 | 4-6 人月 |
| C3 | 趋势分析：多期 + 跨公司对比（matrix D6） | 清单 2.1 | 2-3 人月 |
| C4 | 情景/敏感性控件（杜邦假设联动） | 清单 2.2 + matrix D7 | 2 人月 |
| C5 | 指标字典 v2：查询编译层（维度切片 → 可执行查询） | 清单 4.2 + S-5 + O-01 | 4 人月 |
| C6 | 多业务线杜邦拆解 | 清单 2.6 | 6-8 人月 |
| C7 | 校验型勾稽规则清单化 + 报表推导树显式化 | O-16/O-17 | 内部工作台前置 |

### D 组 · AI 能力（与 B/C 并行设计，实施在 C 级出口后）

| # | 条目 | 来源 | 备注 |
|---|---|---|---|
| D1 | AI 问数 v1→v3（RAG → 多步推理 → 反事实） | 清单 1.2 + ai-qa-design.md（464 行已成方案）+ O-01 | 验收：100 条问数 ≥90% 命中且引用事实 |
| D2 | AI 临时计算「提议→程序复算」管线 | O-02 | D054 既定原则的工程实现 |
| D3 | 多模型按任务路由 | O-03 + FinRobot Smart Scheduler | 成本控制 |
| D4 | 历史分析问题 RAG 复用 | O-04 | 引用原 Finding 身份，不重放计算 |
| D5 | LLM 私有化部署（Qwen/DeepSeek 本地可选） | 清单 4.5（标 P0） | 与「允许合规云 API」原则并裁决 |

### E 组 · 内部工作台（gated：C 级出口 + 数据授权后启动）

| # | 条目 | 来源 |
|---|---|---|
| E1 | 月度周期工作流状态机（收集→校验→扫描→调查→补证→双版本生成→终审→发布） | 设计 §3.1 + O-06 关账清单 |
| E2 | 缺失证据请求工作流（Finance BP 定向提问） | O-08 |
| E3 | 双 AI 角色例外队列 UI | O-05 + D054 |
| E4 | Excel 共生导出（数字带溯源批注） | FP&A 共识（Datarails/Aleph/MS Copilot for Finance） |
| E5 | ERP/账务连接器抽象（先定义接口） | O-15 |
| E6 | 持续化对账（按日推进） | O-07 |
| E7 | 拖拽式 dashboard | 清单 2.5（12-18 人月，最重单项，建议延后裁决） |
| E8 | BSC 四维度（仅企业内版，依赖内部上报数据） | 清单 2.7 |

### F 组 · 生态与远期（P2，记录备查）

PDF/PPTX 导出（3.1）、实时告警推送（3.2/O-13）、第三方嵌入（3.3）、战略框架 BCG/五力（3.4，需裁决定位适配性）、API SDK 三语言（3.6）、多语言（3.7）、自有数据导入工具（3.8）、协作评论（3.9）、多角色 RLS（3.10）、K8s/Helm（4.3）、信创适配（4.4）、Prometheus 监控（4.6）、ECharts 替换自绘 SVG（4.1）、国际合规认证（3.12）、OSI 标准跟踪（S-6）、多维归因组件（O-10）、Value Driver Tree（O-11）、逐行对照披露标记（O-12）、假设联动建模（O-14，L2/L3 依赖）。

## 2. 明确不做（各来源一致的负面清单）

1. 不做通用金融终端（Wind 路线：1 万+指标/3.5 万公司，资源不匹配）；
2. 不做通用 BI（FineBI 路线：千人团队多年沉淀）；
3. 不做海外 SaaS 内容库（AlphaSense 路线：授权壁垒）；
4. 不自训金融 LLM（FinGPT 路线：成本/收益不匹配，用通用模型 + 受治理数据层）；
5. 不在无数据基础时上马 BSC/五力等定性框架（空壳风险）；
6. 不用 AI 替代分析师拍板（AI 辅助 + 经分专员终审是固定原则）；
7. 不做仓库锁定语义层（Snowflake/Databricks 原生路线）。

## 3. 推荐排序（与 CURRENT_ROADMAP 对齐）

```text
A 组（工程收口，R2→R3→R4，Task 6 关闭）
→ B 组（C 级出口：B1/B2/B3/B4 为协议硬项，B5/B6 增强）
→ C1/C2（数据扩张 + 行业基准，C 级出口质量的支撑）
→ 用户裁决点：D 组 AI 能力与 C3-C6 的排期
→ E 组（内部工作台，需 C 级出口 + 数据授权双门禁）
→ F 组（按季度复核滚动裁决）
```
