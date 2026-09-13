---
doc_id: FLOW-DELIVERY-U8-CLOSURE-BASELINE-001
title: U8 关闭与可恢复冻结基线记录
doc_type: delivery
status: verified
version: 1.0
created_at: 2026-09-13
updated_at: 2026-09-13
last_reviewed_at: 2026-09-13
owner: FLOW
applies_to: deployment
knowledge_release: pre-static-obsidian-2026-09-12T15:46+08:00
decision_refs: [D049, D051]
supersedes: []
superseded_by: null
source_refs: [docs/superpowers/plans/2026-09-07-unified-next-plan.md, docs/operations/u8d-acceptance.md]
related_code: [scripts/backup_restore_drill.sh, scripts/u8d_acceptance.sh, scripts/u8a_storage_journey.sh]
commit_refs: [088977b, b3b2c22, d965cf6, 36c2618, 8b8109e]
evidence_refs: [docs/operations/u8d-acceptance.md, docs/operations/u8a-journey-evidence.jsonl]
confidentiality: project-internal
---

# U8 关闭与可恢复冻结基线记录

## 1. U8 正式关闭

U8（运行保障）四个子项全部完成并验证，本记录为其关闭凭证：

| 子项 | 交付 | 提交 |
|---|---|---|
| U8-A 真实存储旅程 | 冻结→发布→下载 SHA 15/15 + 404/409 失败态实证；证据 `docs/operations/u8a-journey-evidence.jsonl` | b3b2c22 |
| U8-B HTTPS 拓扑 | nginx TLS 反代（443/80→301）+ 安全头实证；部署图 infra/nginx/README.md | d965cf6 |
| U8-C 结构化日志 | JSON 行 + 旅程关联 + 脱敏；请求中间件；六处旅程埋点 | 088977b |
| U8-D 干净环境验收 | 隔离 project 全新卷：迁移→健康→旅程→备份恢复 PASS | d965cf6 |

- CI 证据：run `34734757639` success（8b8109e）；
- 迁移头：`0024_operations_publication`；
- 备份恢复演练：PASS（此前 U8-A 前置轮 + u8d_acceptance 内复跑）。

## 2. 冻结基线（可恢复状态）

| 锚 | 值 |
|---|---|
| Git 标签 | `u8-final-baseline`（annotated，打在基线记录提交上） |
| 基线提交 | 见标签指向（含本文件） |
| 数据库备份 | `backups/u8-baseline/flow-u8-final.dump`（pg_dump -Fc，4.4MB，SHA-256 前 16 位 `1811ebb266625415`；不入 git，.gitignore 已排除） |
| 数据状态 | statement_report 11 / metric_dictionary_entry 65（v1.1 全量）/ objective_report_snapshot 12 |
| 常驻栈 | web:3000 api:8000 nginx:3443(TLS) worker + postgres/redis/minio，全 healthy |
| 验收脚本 | `u8a_storage_journey.sh`、`u8d_acceptance.sh`（重构后回归验收复用） |

## 3. 恢复步骤（按序执行）

1. 检出基线：`git checkout u8-final-baseline`（或以该标签为起点建重构分支）；
2. 起基础设施与应用栈：`make stack-up`（或 `docker compose -f infra/compose.yaml up -d --wait`）；
3. 恢复数据（二选一）：
   - **快速路径**（恢复到本记录时刻）：`docker exec -i flow-postgres-1 pg_restore -U flow -d flow --clean --if-exists < backups/u8-baseline/flow-u8-final.dump`；
   - **确定性路径**（从零重灌）：`alembic upgrade head` → `import_all(config/metrics)` → `seed_statement_reports.py` ×11 → 归一化/发布/冻结链 → `seed_dashboard_demo.py --fresh-batch`（全链命令见 PROJECT_STATE 与各脚本 docstring）；
4. 验收：`bash scripts/u8a_storage_journey.sh`（SHA 全过）+ `python3 scripts/check_docs.py --phase m1`（元数据 PASS）+ 三端点 200（`/`、`/api/v1/statements` 11 份、`/api/v1/metric-library` 64 条）。

## 4. 已知限制

- TLS 为开发自签证书，生产需替换真实 CA；
- 量价类指标（volume_growth/price_change_rate）依赖 L2 内部数据，绑定如实缺失；
- `backups/u8-baseline/flow-u8-final.dump` 为本地工件（.gitignore），跨机器恢复走确定性重灌路径；
- U4 oracle、U9/O5 授权、U10 证据决策、rnd_exp 原文核验为 U8 之外的外部依赖项。
