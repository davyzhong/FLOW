---
doc_id: FLOW-DECISION-D050
title: D050 经营分析轨方法论采纳（外部 SOP 分析判断后的默认推荐）
doc_type: decision
status: amended
version: 1.1
created_at: 2026-09-12
updated_at: 2026-09-13
owner: FLOW
decided_at: 2026-09-12
authority: user
amended_by: [FLOW-DECISION-D053]
source_refs: [docs/knowledge-base/04_decisions/DECISION_LOG.md]
---

# D050 经营分析轨方法论采纳（外部 SOP 分析判断后的默认推荐）

> **2026-09-13 注记（D053 修订）**：本决策的方法论内容（L1–L4 数据可得性分层、不自建第二套计算内核、发布链映射冻结）继续有效，并入三层两模块的共享底座与内部工作台；但"双轨第二轨"的框架前提（D045/D046）已被 D053 取代——经营分析不再是独立第二轨，其指标与方法论归入企业内部工作台的固定分析对象。原文中"启动双轨第二轨搭建""执行走经营轨计划 O1–O5"等行动指令按 D053 执行顺序重新裁决，不再自动生效。

- 状态（原文）：有效；用户于 2026-09-09 导入外部资料《终于有人把经营分析给说清楚了！》并明确指示：判断其有效性，有效则沉淀为经营分析方法论并启动双轨第二轨搭建。（映射为 accepted）

- 状态（原日志）：有效；用户于 2026-09-09 导入外部资料《终于有人把经营分析给说清楚了！》并明确指示：判断其有效性，有效则沉淀为经营分析方法论并启动双轨第二轨搭建。
- 判断结论：该 SOP 正确、结构完整，与 FLOW 已验证原则（口径统一、指标分层、守恒拆解、相关性≠因果）同频，**采纳为经营轨方法论骨架**；分析证据见[分析判断文档](../../knowledge-base/02_research/synthesis/2026-09-09-operations-sop-assessment.md)（原文档案同日归档）。
- 三项 FLOW 化适配（采纳前提）：
  1. **数据可得性分层为第一原则**——主题/指标标注 L1 财报可得 / L2 过程层 / L3 事件层 / L4 行动层；公开财报期只建 L1，L2/L3 注册占位返回 not_applicable（typed），缺失不补造、无量价数据不生成量价链；
  2. **拆解纪律复用 U2 原语**（C07/C08/C06/I12/I09），经营轨不自建第二套计算内核；数学分解一律标注非业务因果；
  3. **发布链映射冻结机制**（快照→冻结→发布），不建 BI 导出旁路。
- 不采纳/后置：预测性与推荐性分析（D049 顺序，U9 之后）；AARRR 模型（待 L2 内部数据按行业选用）；Tableau/PBI 工具链（方法论采纳，实现走 FLOW 自有 B/S 链）。
- 落地：[OP 方法论规格](../../superpowers/specs/2026-09-09-operations-track-methodology.md)；执行走 [经营轨计划 O1–O5](../../superpowers/plans/2026-09-09-operations-track-plan.md)（O1 数据定义合同同批交付：`config/operations/operations_track_v1.yaml` + `operations_catalog.py` + 8 项 TDD）。经营轨与 U 系列并行领取，不阻塞财务轨主线（D046 步骤 1）。
- 边界：本决策只覆盖经营轨框架与方法论，不改变 D045/D047/D049 既有效力；「劣质增长砍投入」等行动建议属 L4，主观证据门禁（U5）建成前不入报告。
