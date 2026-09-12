---
doc_id: FLOW-PROD-VISION-001
title: 产品愿景
doc_type: product
status: canonical
version: 1.1
created_at: 2026-09-12
updated_at: 2026-09-13
owner: FLOW
decision_refs: [D001, D049, D052, D053]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: product
supersedes: []
superseded_by: null
---

# 产品愿景

FLOW（Finance Intelligence OS）是**可追溯、确定性、可复核的财务与经营分析平台**。

- **核心目标（D052）**：面向单个企业内部财务经营分析团队的 AI 财务分析工作台——帮助经分专员从多源 Excel 和企业数据出发，自动完成月度财务经营分析的大部分工作，形成有证据、可追溯、接近可发布的交互式报告；最终由经分专员一次审核后正式发布。
- **一句话**：把「数据可信、统一指标、专业诊断、证据链、行动闭环」做成 AI 原生的分析操作系统，而不是又一张报表工具（D001：产品不是单一驾驶舱）。
- **三个不可妥协**：数字同源（同一指标快照身份链）；事实与推断分离（客观口径冻结，推断显式标注）；AI 不创造数字（生成内容不得进入事实层，TECH-COPILOT-001）。
- **目标结构（D053）**：三层、两模块——可见的专业治理底座 + 共享分析底座，支撑两个独立产品模块：**企业内部分析工作台**（最终目标产品）与**公开财报分析模块**（先行成熟共享底座，拥有独立入口、规格、路线图和验收）。
- **路径（D049/D053）**：客观事实与计算 → 证据支持的推断 → 改善行动；U8 收口后先冻结并重构模块边界，公开财报模块达到 C 级出口，再建设企业内部月度分析工作台，最终以授权脱敏真实企业数据完成验证。
- **成功标准（原型阶段）**：专业经分人员确认关键事实和 Finding 可用，报告质量不低于人工基准，人工工作量不超过传统流程的 20%（D052）。

详细范围见 [PRODUCT_SCOPE.md](PRODUCT_SCOPE.md)；固定原则见 [PRODUCT_PRINCIPLES.md](PRODUCT_PRINCIPLES.md)；能力现状见 [CAPABILITY_MAP.md](CAPABILITY_MAP.md)。
