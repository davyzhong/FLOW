---
doc_id: FLOW-DELIVERY-U8-PRODUCTION-FREEZE-001
title: U8 生产冻结与重构启动门禁交付记录
doc_type: delivery
status: verified
version: 1.0
created_at: 2026-09-13
updated_at: 2026-09-13
last_reviewed_at: 2026-09-13
owner: FLOW
applies_to: deployment
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D049, D051, D053]
supersedes: []
superseded_by: null
source_refs: [docs/operations/u8-closure-baseline.md, docs/superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md]
related_code: [scripts/accept_u8_production.sh, scripts/u8d_acceptance.sh, scripts/restore_u8_baseline.sh, scripts/backup_restore_drill.sh, infra/api.Dockerfile]
commit_refs: [079d546, 088977b, b3b2c22, d965cf6, 8b8109e]
evidence_refs: [docs/60_delivery/2026-09-13-u8-production-freeze.evidence.json, docs/operations/u8-closure-baseline.md, config/acceptance/u8-baseline.json]
confidentiality: project-internal
---

# U8 生产冻结与重构启动门禁交付记录

## 结论

U8-A～D 已完成。2026-09-13 在全新隔离 Compose project 与全新卷中运行 fail-closed 门禁，所有必需步骤通过且 `skipped=[]`；S01 可以从实施子规格阶段开始，规格批准前不得进入代码重构。

## 两级恢复锚

| 锚点 | 用途 |
|---|---|
| `u8-final-baseline` → `079d546` | U8 原始关闭基线；保留原始代码、文档和本地数据库备份恢复说明 |
| `flow-u8-freeze-20260913` | 严格门禁及生产 PDF 运行时修复后的重构启动锚；从此点进入 S01 |

本地冻结备份仍为 `backups/u8-baseline/flow-u8-final.dump`，不进入 Git。其机器可判定合同为 `config/acceptance/u8-baseline.json`：迁移头 `0024_operations_publication`，关键表计数和 12 个冻结快照的聚合哈希均须一致。

## 严格门禁结果

- TLS：以 `infra/nginx/dev-tls.crt` 验证 `https://localhost:3443`，API/Web 均为 200；未使用 `-k`。
- 真实存储：HTML 与 PDF 均写入 MinIO、下载并通过 SHA-256；未知尝试返回 404，真实删除对象后返回 409。
- 干净环境：从空数据库迁移至 `0024_operations_publication`，空态为 0，再导入治理种子和最小财报。
- 恢复：`pg_restore --exit-on-error` 成功；恢复前后 `statement_report`、`objective_report_snapshot` 计数和冻结载荷聚合哈希一致；恢复后 API 健康检查成功。
- 生产运行时修正：API/Worker 镜像补入 Chromium、容器沙箱包与中文字体；以 UID 10001 非 root 运行。仅容器镜像显式设置 `FLOW_CHROMIUM_NO_SANDBOX=1`，宿主执行继续使用浏览器沙箱。
- 本次隔离验收镜像：`u8accept-api@sha256:7b02d4def6249861650f8994964362fbe46d3b603ae4bd5f4b9f59eab32e4046`、`u8accept-worker@sha256:12e73e3886353db2a07339c43c11927752202d47ebeb066d5efcf9f3119b30e3`。镜像为本地构建冻结凭据；后续发布仍应由 CI 生成仓库级不可变 digest。

机器证据见 [2026-09-13-u8-production-freeze.evidence.json](2026-09-13-u8-production-freeze.evidence.json)。

## 验收与恢复命令

完整门禁：

```bash
FLOW_U8_BASE_URL=https://localhost:3443 \
FLOW_U8_CA_CERT=infra/nginx/dev-tls.crt \
bash scripts/accept_u8_production.sh full
```

冻结备份恢复核验必须使用受限命名的隔离数据库：

```bash
FLOW_U8_BASE_URL=https://localhost:3443 \
FLOW_U8_CA_CERT=infra/nginx/dev-tls.crt \
FLOW_U8_BACKUP_PATH=backups/u8-baseline/flow-u8-final.dump \
FLOW_U8_RESTORE_DATABASE=flow_u8_accept_manual \
bash scripts/accept_u8_production.sh restore-u8-baseline
```

任何 TLS、SHA、`pg_restore`、关键表、冻结哈希、健康检查失败或步骤跳过均令门禁非零退出。
