# FLOW API 路径索引

从当前已提交 `packages/contracts/openapi.json` 提取；代码基线 `c1a59d1`，核对日期 2026-09-04。字段约束、错误体和完整 schema 以 [OpenAPI](../packages/contracts/openapi.json) 及 [生成式 TypeScript](../packages/contracts/src/schema.d.ts) 为准。运行后可访问 FastAPI `/docs`。

状态列只列出契约声明，不穷举运行时错误；认证可能返回 401，上传还可能返回 413/404 等领域错误。详见 [Intake 错误语义](intake/flow-v1-intake.md)。

## 访问边界

浏览器经 Next.js 同源 `/api/v1` 代理；启用单用户登录时由服务端验证会话并附加 Bearer。直接调用 FastAPI 则自行提供 `Authorization: Bearer <token>`。`GET /api/v1/health` 豁免。Web 的登录/退出路由不属于 FastAPI OpenAPI，另列于文末。

| 方法 | 路径 | 操作 | OpenAPI 声明状态 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health` | Health | 200 |
| `GET` | `/api/v1/workspace` | Get Workspace | 200, 422 |
| `GET` | `/api/v1/intake/templates/{template_id}` | Download Template | 200, 422 |
| `POST` | `/api/v1/intake/batches` | Create Batch | 201, 422 |
| `POST` | `/api/v1/intake/batches/{batch_id}/sources` | Upload Source | 201, 422 |
| `GET` | `/api/v1/intake/sources/{source_file_id}/profile` | Get Profile | 200, 422 |
| `POST` | `/api/v1/intake/sources/{source_file_id}/mapping-proposals` | Create Mapping Proposal | 201, 422 |
| `POST` | `/api/v1/intake/mappings/{mapping_version_id}/confirm` | Confirm Mapping | 200, 422 |
| `POST` | `/api/v1/intake/mappings/{mapping_version_id}/overrides` | Override Mapping | 201, 422 |
| `POST` | `/api/v1/intake/sources/{source_file_id}/validate` | Validate Source | 200, 422 |
| `POST` | `/api/v1/intake/issues/{quality_issue_id}/acknowledge` | Acknowledge Warning | 200, 422 |
| `POST` | `/api/v1/intake/imports/{import_version_id}/publish` | Publish Import | 200, 422 |
| `GET` | `/api/v1/intake/batches/{batch_id}/versions` | Version History | 200, 422 |
| `GET` | `/api/v1/intake/imports/{import_version_id}/cleaning-summary` | Cleaning Summary | 200, 422 |
| `GET` | `/api/v1/intake/imports/{import_version_id}/standardized-workbook` | Export Standardized Workbook | 200, 422 |
| `GET` | `/api/v1/dashboard/overview` | Dashboard Overview | 200, 404, 422 |
| `GET` | `/api/v1/investigations/{finding_id}` | Investigation Context | 200, 404, 409, 422 |
| `POST` | `/api/v1/investigations/{finding_id}/evidence/{evidence_id}/decision` | Decide Evidence | 200, 404, 409, 422 |
| `PUT` | `/api/v1/investigations/{finding_id}/conclusion` | Save Conclusion | 200, 404, 422 |
| `POST` | `/api/v1/investigations/{finding_id}/transition` | Transition Finding | 200, 404, 409, 422 |
| `POST` | `/api/v1/copilot/investigations/{finding_id}/ask` | Ask Investigation Question | 200, 404, 409, 422 |
| `POST` | `/api/v1/copilot/explain-mapping` | Explain Mapping | 200, 404, 422 |
| `POST` | `/api/v1/copilot/report-outline` | Draft Report Outline | 200, 404, 422 |
| `POST` | `/api/v1/publishing/snapshots/{report_snapshot_id}/publish` | Publish Report | 200, 404, 409, 422 |
| `GET` | `/api/v1/publishing/snapshots/{report_snapshot_id}/attempts` | Publication Attempts | 200, 404, 422 |
| `POST` | `/api/v1/publishing/snapshots` | Freeze Report Snapshot Route | 201, 409, 422 |
| `GET` | `/api/v1/publishing/snapshots` | List Report Snapshots | 200, 422 |
| `GET` | `/api/v1/publishing/attempts/{attempt_id}/download` | Download Publication Attempt | 200, 404, 409, 422 |

合计 **28 个 HTTP operation**。这里的 schema/路由存在不代表每种部署依赖已配置：PDF 默认无打印器，生成尝试会显式失败；新导入批次的指标与分析需要服务层编排。

## Web 会话路由

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| POST | `/api/auth/login` | 同源表单验证密码；正确后签发 HttpOnly cookie 并重定向 |
| POST | `/api/auth/logout` | 同源请求清除当前浏览器 cookie 并返回登录页 |

认证配置详见[会话说明](operations/authentication.md)。会话 cookie 不替代直接访问后端所需的 Bearer token。
