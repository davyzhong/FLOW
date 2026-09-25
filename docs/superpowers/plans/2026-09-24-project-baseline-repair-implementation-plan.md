---
doc_id: FLOW-PLAN-BASELINE-REPAIR-20260924
title: 项目基线修复实施计划
doc_type: plan
status: archived
version: 1.2
created_at: 2026-09-24
updated_at: 2026-09-24
owner: FLOW
depends_on: [FLOW-SPEC-DAMAI-DEMO-001]
acceptance_refs: [FLOW-SPEC-DAMAI-DEMO-001]
applies_to: repository
superseded_by: FLOW-PLAN-INTEGRATED-EXECUTION-20260924
do_not_execute: true
---

# Project Baseline Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 恢复当前 main 的文档门禁绿色状态，并把权威状态、导航和交接更新到实际工程基线。

**Architecture:** 只修文档元数据和权威叙述，不更改业务代码、CI 配置或数据库。所有状态更新必须由当前提交、Alembic head、GitHub Actions 和大麦发行版实测证据支撑。

**Tech Stack:** Markdown frontmatter、FLOW 文档门禁、Git/GitHub Actions。

---

### Task 1: 修复顶层文档元数据门禁

**Files:**
- Modify: `CODE_OF_CONDUCT.md`
- Modify: `CONTRIBUTING.md`
- Modify: `SECURITY.md`

- [ ] 为三份文档分别写符合治理合同的唯一 `doc_id`、title、doc_type、status、version、日期和 owner。
- [ ] 确认设计规格使用合法 `doc_type: specification`，不把新错误带入 M6。
- [ ] 运行 `python3 scripts/check_docs.py --phase m6`，要求全量零失败，而不仅是原有三条 missing frontmatter 消失。
- [ ] 运行 `git diff --check`。
- [ ] 提交 `fix(docs): restore top-level metadata gate` 并立即 push。

### Task 2: 在大麦实现完成后刷新权威状态

**Files:**
- Modify: `docs/00_start_here/PROJECT_STATE.md`
- Modify: `docs/00_start_here/READING_ORDER.md`
- Modify: `docs/50_plans/CURRENT_ROADMAP.md`
- Modify: `docs/50_plans/views/active.md`（仅由生成器写）
- Modify: `HANDOFF.md`
- Modify: `docs/README.md`
- Modify: `README.md`

- [ ] 先采集实际 Alembic head、测试结果、seed receipt、页面覆盖和最新 CI head SHA。
- [ ] 把迁移头统一为实际值，删除过时“当前”说法，不改写历史审计记录。
- [ ] 在 CURRENT_ROADMAP 登记大麦演示发行版工作包和真实状态；运行 plan view 生成器。
- [ ] README 增加空环境与大麦演示两种启动命令，所有数字来自 manifest/实测。
- [ ] HANDOFF 写入已完成、未完成、恢复/重建命令和已知限制。
- [ ] 运行 `make docs-check`、链接检查、`git diff --check`。
- [ ] 提交 `docs: refresh project state after damai demo release` 并立即 push。
