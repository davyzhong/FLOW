# Pilot Readiness Phase 1 — 验证证据

> 对应计划：`docs/superpowers/plans/2026-09-02-flow-pilot-readiness-phase-1-user-closure.md`
> 状态：**✅ 出口门禁已通过（exit=0）**，Task 1–9 全部完成；CI job 独立化与基线 tag 已落地。

## 出口门禁执行记录（2026-09-04）

`make test-user-closure-e2e` → **PASSED（exit=0）**，依次通过：

1. 浏览器用户闭环（Playwright 4 用例）：/data 工作台加载 + 治理化模板真实下载 + 标准工作簿
   上传→映射→清洗全旅程 + /reports 报告中心加载 + 仪表盘导航真实路由；
2. 契约漂移检查；
3. Phase 3/6/7/9 回归：intake 41 ✅、dashboard 2 ✅、investigation 10 ✅、publishing golden 35 ✅；
4. API 全量（含本轮新增 12 个契约测试）；
5. 前端 lint/typecheck/vitest 18 ✅。

## 已完成（全部 TDD：先测后码，见 git 历史逐任务提交）

| 任务 | 交付 | 证据 |
|---|---|---|
| Task 1 | 契约测试先行（模板下载 / override / 清洗摘要 / 导出 / 快照冻结列表 / 下载） | `tests/api/test_intake_template.py`、`test_intake_overrides.py`、`test_intake_cleaning_export.py`、`test_publishing_api.py`（均先 RED 后 GREEN） |
| Task 2 | `GET /api/v1/intake/templates/flow.excel.v1`：确定性空白模板（说明页 + 契约行保护 + 字节稳定） | 8239779 + a26722c；4 契约测试 |
| Task 3 | `POST /intake/mappings/{id}/overrides`：类型化修正、append-only 新 MappingVersion、确认审计；拒绝未知目标/未知源列/重复源列/过期 hash/跨批次 | f7732a7；5 契约测试 |
| Task 4 | `GET /imports/{id}/cleaning-summary`（计数+转换规则+≤3 有界血缘样本+质量/对账计数）、`GET /imports/{id}/standardized-workbook`（确定性 xlsx） | a4d5da8 + 7e3038d；3 契约测试 |
| Task 6 | 成功 PublicationAttempt 必须持久化 StoredObject 行（修复 NULL 假成功）；失败 attempt 无对象；append-only 重试 | 3700cb6；`test_succeeded_attempt_persists_reusable_stored_object` |
| Task 7 | `POST/GET /publishing/snapshots`、attempt 明细（attempt_id/size/content_type/created_at/download_available/stored_sha256）、`GET /attempts/{id}/download`（sha 校验 + 服务端命名 + no-store/nosniff；失败 attempt 409） | c4185e4 + db973e1；3 契约测试 |
| Task 9 | `make test-user-closure-e2e` + `scripts/test_user_closure_e2e.sh` + `apps/web/e2e/user-closure.spec.ts`；门禁顺序：回归先行、浏览器闭环最后（自管栈） | 514e525 + 641e71c；门禁 exit=0 |
| Task 5/8 前端 | `/data` 五阶段工作台 + `/reports` 报告中心 + 工作流导航真实路由；组件测试 5 个 | 51802bd/b834151 + 本轮 reports 提交 |
| Task 10 | 证据文档、PROJECT_STATE 阶段 21、基线 tag `v0.2-pilot-baseline` | 见本文档与 git tag |

## 修复的真实缺陷

1. `render_workbook` 字节不确定：openpyxl 将当前时间写入 zip 条目与 `docProps/core.xml`
   的 dcterms:modified —— 新增 `stable_zip_bytes` 归一（7e3038d）；
2. `read_canonical_package_by_version` 四张事实表查询无 ORDER BY —— 行序不稳定导致
   导出不可复现（7e3038d）；
3. PublicationAttempt 成功时引用未持久化的 StoredObject（NULL 假成功，3700cb6）；
4. Next 代理以 `request.text()` 转发 multipart 导致文件上传二进制损坏
   （改为 FormData 整体转发，本轮）；
5. Next 16 单 dev 服务器限制导致并发栈互踢 —— 门禁顺序调整为回归先行、
   浏览器闭环最后自管栈（本轮）。

## 待完成（移入下一阶段）

- CI workflow 的 user-closure 独立 job（门禁脚本已就绪，仅剩 workflow YAML）；
- 指标阈值和预警规则明细；最小安全部署（D038 下一步）。

