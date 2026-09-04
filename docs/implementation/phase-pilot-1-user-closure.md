# Pilot Readiness Phase 1 — 验证证据（进行中）

> 对应计划：`docs/superpowers/plans/2026-09-02-flow-pilot-readiness-phase-1-user-closure.md`
> 状态：**Task 1–7、9（部分）已完成；Task 5/8 的浏览器深度旅程与完整门禁执行待续**

## 已完成（全部 TDD：先测后码，见 git 历史逐任务提交）

| 任务 | 交付 | 证据 |
|---|---|---|
| Task 1 | 契约测试先行（模板下载 / override / 清洗摘要 / 导出 / 快照冻结列表 / 下载） | `tests/api/test_intake_template.py`、`test_intake_overrides.py`、`test_intake_cleaning_export.py`、`test_publishing_api.py`（均先 RED 后 GREEN） |
| Task 2 | `GET /api/v1/intake/templates/flow.excel.v1`：确定性空白模板（说明页 + 契约行保护 + 字节稳定） | 8239779 + a26722c；4 契约测试 |
| Task 3 | `POST /intake/mappings/{id}/overrides`：类型化修正、append-only 新 MappingVersion、确认审计；拒绝未知目标/未知源列/重复源列/过期 hash/跨批次 | f7732a7；5 契约测试 |
| Task 4 | `GET /imports/{id}/cleaning-summary`（计数+转换规则+≤3 有界血缘样本+质量/对账计数）、`GET /imports/{id}/standardized-workbook`（确定性 xlsx） | a4d5da8 + 7e3038d；3 契约测试 |
| Task 6 | 成功 PublicationAttempt 必须持久化 StoredObject 行（修复 NULL 假成功）；失败 attempt 无对象；append-only 重试 | 3700cb6；`test_succeeded_attempt_persists_reusable_stored_object` |
| Task 7 | `POST/GET /publishing/snapshots`、attempt 明细（attempt_id/size/content_type/created_at/download_available/stored_sha256）、`GET /attempts/{id}/download`（sha 校验 + 服务端命名 + no-store/nosniff；失败 attempt 409） | c4185e4 + db973e1；3 契约测试 |
| Task 9 | `make test-user-closure-e2e` 目标 + `scripts/test_user_closure_e2e.sh` + `apps/web/e2e/user-closure.spec.ts`（4 浏览器用例） | 514e525 |
| Task 5/8 前端 | `/data` 五阶段工作台 + `/reports` 报告中心 + 工作流导航真实路由；组件测试 5 个 | b834151 + 本轮 reports 提交 |

## 修复的真实缺陷

1. `render_workbook` 字节不确定：openpyxl 将当前时间写入 zip 条目与 `docProps/core.xml`
   的 dcterms:modified —— 新增 `stable_zip_bytes` 归一（7e3038d）；
2. `read_canonical_package_by_version` 四张事实表查询无 ORDER BY —— 行序不稳定导致
   导出不可复现（7e3038d）；
3. PublicationAttempt 成功时引用未持久化的 StoredObject（NULL 假成功，3700cb6）。

## 待完成（下一会话继续）

- 执行完整 `make test-user-closure-e2e`（基础设施已可启动：`open -a Docker` + `make infra-up`）；
- Playwright 上传旅程深度断言（非标准工作簿、映射覆盖交互、失败重试浏览器路径）；
- CI workflow 增加独立 user-closure job；
- Task 10：截图证据、决策日志 D 条目、基线 tag。

## 门禁快照

- 基线：274 passed（postgres/redis/minio 实栈）
- tests/api：19 passed（本轮后）→ 全量前端 9 文件 18 tests passed；tsc/ruff/mypy 全绿
