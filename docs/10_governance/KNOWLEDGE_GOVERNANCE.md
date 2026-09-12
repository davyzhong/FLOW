---
doc_id: FLOW-GOV-KB-001
title: 知识治理规则
doc_type: governance
status: current
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
applies_to: knowledge-base
knowledge_release: flow-knowledge-2026-09-12.1
---

# 知识治理规则

依据：设计规格 V1.1 §4。M2 建成前本页为规则预登记。

## 关键规则（摘要）

- **三层资产**：来源证据 → 静态知识 → 产品定义/决策/规格/计划/实施，依赖单向；
- **来源登记**：`SOURCE_REGISTER` 覆盖基线全部来源，每项有处置记录（adopted/partially-adopted/duplicate/background/rejected/pending-verification）；「全部整理」= 全部有处置，非全文复制；
- **知识状态**：candidate → verified → canonical → deprecated；canonical 必须有 source_ref 与所在 release lock；
- **权威等级**：A 法规官方 / B 审计披露与权威标准 / C 专业机构教材 / D 企业实践 / E AI 摘要（仅线索，不得定稿）；低权威不得覆盖高权威；
- **敏感等级**：public / project-internal / authorized-internal / restricted；授权与降敏必须新版本+新发布；
- **静态发布**：release lock（版本化文件 + SHA-256）；`CURRENT_RELEASE` 切换须用户批准，发布后不原位改写；
- **存储分级**（设计 §4.9）：A git / B LFS / C Release / D 冗余清除；docx/pptx/zip 不重压缩；不可变档案永久原位。

## 更新纪律

动态源（Obsidian）变化不触发项目文档/代码变更；知识维护由用户明确发起，形成新截面与新发布。
