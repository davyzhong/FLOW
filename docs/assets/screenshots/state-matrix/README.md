---
doc_id: FLOW-NAV-STATE-MATRIX-001
title: 前端状态矩阵归档索引（Task 9 证据）
doc_type: navigation
status: current
version: 1.0
created_at: 2026-09-18
updated_at: 2026-09-18
owner: FLOW
applies_to: docs
---

# 前端状态矩阵归档（Task 9 证据）

> 由 `apps/web/e2e/state-matrix-archive.spec.ts` 按需生成
（`FLOW_STATE_MATRIX_ARCHIVE=1 pnpm exec playwright test e2e/state-matrix-archive.spec.ts`）。
覆盖数据密集四页 × {正常 / 空 / 加载 / 错误 / 403} × {390 / 1024 / 1440}；
结构合同由 `frontend-states.spec.ts` 与 `frontend-responsive.spec.ts` 门禁自动化，本目录为人审证据。

| 页面 | 截图目录 |
|---|---|
| `/statements` | [statements/](statements/) |
| `/reports` | [reports/](reports/) |
| `/metric-library` | [metric-library/](metric-library/) |
| `/investigations` | [investigations/](investigations/) |

生成时间：2026-09-18T15:27:56.778Z

