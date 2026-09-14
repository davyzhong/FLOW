---
doc_id: FLOW-REVIEW-PROJECT-POST-REPAIR-20260915
title: 项目整体 Review：单 Agent 接管修复后的状态核验（2026-09-15）
doc_type: review
status: partially-resolved
version: 1.1
created_at: 2026-09-15
updated_at: 2026-09-15
last_reviewed_at: 2026-09-15
owner: FLOW
subject_ref: main@042d937
findings: [r1-security-confirmed, ci-gate-inventory-consistent, frontend-governance-ok, m1-m6-gate-broken-by-competitive-docs, project-state-stale, r2-r4-pending, var-file-tracked, ownership-naming-stale, dashboard-404-data-state, reverse-parse-base-anomaly]
applies_to: repository
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053, D054]
supersedes: []
superseded_by: null
source_refs:
  - docs/80_reviews/2026-09-14-s01-multi-agent-overall-review.md
  - docs/70_operations/2026-09-14-single-agent-takeover-plan.md
  - docs/70_operations/2026-09-14-coordination-ledger-glm.md
evidence_refs:
  - "https://github.com/davyzhong/FLOW/actions/runs/34895309197"
confidentiality: project-internal
---

# 项目整体 Review（2026-09-15）

## 0. 审查对象与方法

- 固定对象：`main@4c02a3c`（CI run 34895309197 同 SHA 全绿，17/17，33m20s）；审查期间 main 前进到 `042d937`（竞对文档两个提交，CI 进行中）。
- 方法：文档链核对（PROJECT_STATE → 协调台账 §6 → 接管计划）、CI 门禁清单与实际工作流比对、安全代码抽查（auth.py / audit_writer.py / 路由清单 TSV）、前端治理守护（AppShell / navigation.spec.ts）、仓库卫生（worktree/分支/误入库文件）、设计符合性对照（战略重构设计 V1.1）、文档门禁 m1/m6 本地实测。
- 本报告不做全量代码逐行评审；结论以可核验证据为准。

## 1. 结论先行

**多 Agent 并行造成的混乱已被单 Agent 有效收敛，工程可信度恢复**：同一 SHA 的 17/17 CI 全绿、worktree 14→1、本地分支收敛到 4 个、git 身份归一、R0+R1 按冻结令执行完毕并有台账登记。**当前实现与已批准设计（战略重构 V1.1 + 安全规格 V1.1）方向一致，未发现方向性偏离。**

剩余问题分三类：(a) R2–R4 既定门禁尚未执行（计划内债务，非缺陷）；(b) 权威状态文档滞后于代码事实；(c) 文档门禁 m1/m6 被新竞对文档打断（本次审查顺带修复）与若干 P3 卫生项。

## 2. 已修复确认（有证据）

| 项 | 证据 |
|---|---|
| CI 同 SHA 全绿 | run 34895309197（main@4c02a3c）；`config/ci/required_jobs_s01.txt` 17 条与 `.github/workflows/ci.yml` 实际 job 一一对应，含新增 `module-boundaries-e2e` |
| 安全合同 R1 | durable AuditWriter（独立短事务、401/403/allow 三态、503 fail-closed）、correlation 中间件、identity JSON 严格校验、legacy cutoff 收窄为仅命中匹配 token（bc62937）、66 条路由全部接 require_action（TSV 66 行核对一致）、迁移 0027、create_batch 自愈引导 |
| 工作区清理 | `git worktree list` 仅剩主检出；本地 4 分支/远端 5 分支 |
| 提交可归因 | 近期提交统一 `davyzhong <zhong.davy@gmail.com>` |
| 前端治理 | 除 login 外全部 page 包裹 AppShell；`navigation.spec.ts` 守护 10 条交互路由，符合 AGENTS.md 规则 |
| 资料库资产 | 静态资料库（df11b44）→ 报告级视觉（f332b95）→ 11 板块合一 + SVG（e114ae3）→ 视觉反哺在线版（4be2c0f）→ DuPont（c9f4c6c）均在 main |
| 竞对研究资产 | `docs/competitive/`（7 份调研 + 定位总汇 + 30+ 条优化清单）与 `docs/knowledge-base/09_competitive/`（C01–C20 逐品调研 + 横向盘点 + O-01~O-17 清单）已入库，覆盖用户竞对研究诉求 |

## 3. 设计符合性核对（实现 vs 战略重构设计 V1.1）

| 设计要求 | 实现状态 | 判定 |
|---|---|---|
| 三层两模块（共享底座 + 公开模块 + 内部工作台） | `modules/registry.py`：public_analysis=implemented、internal_workbench=designed、professional_governance=designed、shared_core 内部登记；ownership_v1.yaml + AST 守护 | ✅ 一致 |
| 内部工作台不在门禁前提前实施 | 保持 designed 状态，UI 走 /internal#governance 锚点 | ✅ 一致（符合时序） |
| 单一路线图纪律 | CURRENT_ROADMAP 唯一入口；模块只有 workstream 视图 | ✅ 一致 |
| Financial Facts Contract V2 先行 | S01 Task 1–5 已完成入 main | ✅ 一致 |
| 安全/权限子规格 | route-inventory-v1.tsv + require_action + 0027 | ✅ 一致 |
| 公开模块 C 级出口协议（冻结样本/holdout/盲评量化） | 未启动 | ⬜ 计划内待办 |
| 真实企业验证（三个完整月度周期） | 未启动（需数据授权） | ⬜ 计划内待办 |

## 4. 仍存在的问题与缺陷

### P1 —— 门禁完整性

1. **文档门禁 m1/m6 被竞对文档打断**（042d937/1af369d 引入，本次审查修复）：8 份 `docs/competitive/*` 使用未注册 doc_type `competitive-research` 且 7 份缺 `updated_at`；kb 两个 2026-09-14 新文件无 frontmatter；`09_competitive/INDEX.md` 修改后失去 legacy 豁免。CI 只跑 m1 也会红（unknown doc_type 属 m1 错误），对应 in-progress run 34905532195/34905811633 预计 static-python 失败。修复方式：`metadata.py` 注册 `competitive-research` 类型（遵循既有 8 份文档的既定用法，属类型表补全而非放宽断言）+ 补齐 frontmatter。教训：**文档类提交前必须本地跑 `check_docs.py --phase m1`**。

### P2 —— 治理/计划层

2. **PROJECT_STATE.md 滞后于代码事实**（v1.5，2026-09-14）：仍称「Task 6 维持不关闭」「当前唯一恢复基线为 ba5f34c」，未反映 R0/R1 完成与 main 推进；台账 §6 遗留项 5（登记最终 checkpoint SHA）也未闭环。「唯一 current state」与 HEAD 脱节会误导下一个会话。
3. **R2–R4 未执行**（台账 §6 遗留，计划内）：R2 route-policy-v3 治理写落地 + publishing/operations 串行接线（含 pipeline 死代码处置）；R3 module-boundaries-v2（全树 AST + path-glob manifest）；R4 full-verification-v2（动态隔离/真实 CA/sentinel/双证明）。
4. **Task 6 未正式关闭**：R1 使其「closure-ready」，按接管计划的完成定义需 R2–R4 全绿后才可宣布 S01 完成。

### P3 —— 工程卫生

5. **`var/metric_library_audit.jsonl` 误入库**（7d179ec 带入）：运行时审计日志被 git 跟踪，应移出版本控制并加入 .gitignore。
6. **ownership_v1.yaml 的 owner 命名是多 Agent 时代残留**（sol/kimi/glm-coordinator）：单 Agent 时代语义失效，建议改为角色域命名（security/api/web/docs）。
7. **dashboard 404 not-ready 数据态**：0027 批次转 internal 后需重新发布快照（台账已登记为非安全回归），影响演示与第一印象。
8. **反向解析样本的同比基数异常**（如阿里 FY2019 季度列对年度列）：展示层已按财报惯例标注 n.m.（f332b95），数据层未修；归入竞对清单中的准确率基准方向一并解决。

## 5. 建议的下一步顺序

1. 同步 PROJECT_STATE.md 与台账最终 checkpoint（P2-2，半小时级）；
2. 按台账 §6 顺序推进 R2 → R3 → R4；
3. P3 卫生包随 R2 分支顺带清理（条目 5/6/7）；
4. C 级出口协议启动时并入竞对研究的 P0 方向（见 `docs/competitive/` 与 kb `09_competitive` 两份清单的交集：AI 问数、数据点级溯源、准确率基准、重述检测）。
