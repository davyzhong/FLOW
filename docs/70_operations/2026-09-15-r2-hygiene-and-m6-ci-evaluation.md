---
doc_id: FLOW-OPS-R2-HYGIENE-M6CI-20260915
title: R2 工程卫生包执行记录与 m6 文档门禁入 CI 评估
doc_type: operations
status: current
version: 1.0
created_at: 2026-09-15
updated_at: 2026-09-15
owner: FLOW
applies_to: repository
---

# R2 工程卫生包执行记录与 m6 文档门禁入 CI 评估（T04）

## 1. 已执行项

| 项 | 处置 | 验证 |
|---|---|---|
| `var/metric_library_audit.jsonl` 运行产物移出版本控制 | `git rm --cached` + `.gitignore` 增加 `var/`；本地文件保留 | `git check-ignore` 生效；仓库无运行产物 |
| ownership_v1.yaml owner 职责域化 | `sol`/`kimi`/`glm-coordinator` → 统一 `security` 职责域；新登记 `security/redaction.py` 与 `flow_api/publication/*`（owner: `publication-transaction`） | `tests/architecture/test_module_imports.py` 覆盖检查通过 |
| 指标库 JSONL 审计定位降级 | 数据库治理事件（`metric_governance_event`）+ durable AuditEvent 为权威审计；JSONL 仅为运维便利日志（`var/`，不入库） | TSV 治理写豁免注记已清除 |

## 2. m6 文档门禁入 CI：评估结论（待用户批准后实施）

背景：尽调缺口 G6——CI 只跑 `check_docs.py --phase m1`（frontmatter 元数据），
m6（链接完整性/兼容/读者测试）仅本地可跑。竞对文档曾因缺 `updated_at` 打断
m1（已拦截），但 m6 层的链接漂移在远端不可见。

**建议改动（单行）**：`.github/workflows/ci.yml` 的 `static-python` job 中

```yaml
      - run: python3 scripts/check_docs.py --phase m1
```

改为：

```yaml
      - run: python3 scripts/check_docs.py --phase m6
```

**评估**：
- 本地 `--phase m6` 当前全绿（239 文档 0 错误，含本日新增文档）；
- m6 耗时为秒级（纯静态检查），对 CI 时长无感；
- 风险：未来文档新增坏链接会拦 CI——这正是设计意图（等价于 commit 前必须
  本地跑 m6，与 §7 停机条件一致）。

**未实施原因**：用户全局红线约定「修改 CI/CD 配置须先询问」。本包按批准的
to-do（T04「评估并单独提交 m6 CI 门禁」）只完成评估与方案，改动待用户
回复后一行提交（可与 R3 开工同分支或 hotfix 独立提交）。
