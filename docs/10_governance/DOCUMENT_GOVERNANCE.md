---
doc_id: FLOW-GOV-DOC-001
title: 文档治理规则
doc_type: governance
status: current
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
applies_to: repository
knowledge_release: pre-static-obsidian-2026-09-12T15:46+08:00
---

# 文档治理规则

依据：[静态知识库与文档体系总体设计 V1.1](../../superpowers/specs/2026-09-12-static-knowledge-and-document-architecture-design.md)。本页为执行摘要，冲突时以设计规格为准。

## 生命周期与状态

各 doc_type 使用独立状态枚举（design/spec: draft→review→approved→superseded→archived；plan: proposed→active↔blocked→completed/cancelled；decision: proposed→accepted→amended/superseded/retired/rejected 等），由 `scripts/documentation/metadata.py` 按 doc_type 校验，CI 经 `check_docs.py --check` 强制。

## 命名

- 稳定当前文件不加日期：`PROJECT_STATE.md`、`CURRENT_ROADMAP.md`、`PRODUCT_SCOPE.md`、`FACT_CONTRACT.md`、`DECISION_INDEX.md`；
- 历史与一次性交付：`YYYY-MM-DD--type--topic--version.md`；
- 更新时间写元数据，不通过改名表达。

## 元数据合同

核心字段（doc_id/title/doc_type/status/version/created_at/updated_at/owner）+ 按 doc_type 附加字段；M1 后新增/修订的正式文档必须合规；历史豁免清单 `legacy-exemptions.tsv` 以 SHA-256 锁定，实质修改即失去豁免。

## 禁止的旁路

外部文章直接成为需求；历史会话覆盖当前规格；README 复制状态正文；计划重复定义事实合同；为整齐移动不可变档案或破坏机器引用。
