# A01 基线审计（客观财务分析主计划）

- 审计日期：2026-09-06；审计人：Kimi（接手 Agent）
- 代码基线：`63907ba`（docs: plan objective financial analysis delivery and complete backlog）
- 远端 CI：`63907ba` 起最近三次 push 的 FLOW CI 全部 success（16 jobs，runs 34020791625 / 34022341275 / 34023097164）
- 工作树：无已跟踪文件修改；未跟踪内容 `.zcode/`、`var/`、用户归档文件与图片（按既定规则不提交）
- 本地运行栈：审计时 Docker/Postgres/MinIO 与 dev 进程均未运行；本审计以代码、测试与 CI 证据为准，不引用旧"done"标记作为验收依据

## 1. 功能 / 实现 / 测试 / 缺口矩阵

| 能力域 | 实现证据（代码） | 测试证据 | 缺口与备注 |
| --- | --- | --- | --- |
| Phase 1–10 功能切片（接入/指标/分析/驾驶舱/调查/Copilot/发布/验收门禁） | `services/api/src/flow_api/{intake,metrics,analysis,publishing,investigation,copilot}` | `make acceptance` 七组门禁；CI 16 jobs 绿 | 无（历史验收成立） |
| 指标字典 v1.0（D047 定稿） | `config/metrics/metric_dictionary_v1.yaml`（`dictionary_id: flow.metric_dictionary.v1`、`status: effective`）、`accounting_foundation_v1.yaml`、`operations_dictionary_v1.yaml` | CI 静态与契约门禁 | v0 文件并存（`metric_dictionary_v0.yaml` 等），未删除；来源核验深度归 C01 |
| 指标库落库（WS-2，迁移 0012） | `migrations/versions/0012_metric_library_objects.py`；`GET /api/v1/metric-library` 为 **DB 优先、YAML v1 回退**（`metric_library.py:225` `_db_payload(session) or _yaml_payload()`） | `tests/api/test_metric_library_api.py` | 版本化变更治理（草稿/生效/退役、可靠审计）归 C04 |
| 引擎目录库内化（WS-3/D048，迁移 0013） | `migrations/versions/0013_metric_catalog_documents.py`；`resolve_metric_catalog(session, metrics_config)`（orchestration.py 调用） | `tests/integration/test_metric_catalog_store.py`（双源哈希 parity） | 旧 YAML 路径保留为回退；影响分析/试算归 C05 |
| 三公司财报抽取（WS-4） | `docs/implementation/p5/{sf_2026q1,tencent_2026q2,jdl_2025fy}_statements.yaml`；`scripts/p5_extract_statements.py`、`p5_extract_jdl.py`、`p5_extract_tencent.py`；导入器 `scripts/seed_statement_reports.py` → `statement_report`（0011） | `docs/implementation/p5/P5-validation-summary.md`：顺丰 163 行勾稽 20/20 跨文档 12/12、腾讯调节链闭合、京东物流 118 行勾稽 24/24；`tests/api/test_statement_api.py` | 抽取器为公司专用脚本，未抽象成统一适配接口（B02）；全行 diff 与独立答案未建（D03/A03） |
| 发布后编排（WS-2/T2.6） | `api/routes/orchestration.py`：`POST /api/v1/orchestration/batches/{id}/build` | `tests/api/test_orchestration_api.py`（build/404/409 三用例） | **生产路径固定演示月份**：`orchestration.py:92 months = list(DASHBOARD_MONTHS)`（常量位于 `dashboard/constants.py`）→ B06 缺口属实 |
| 月报冻结与发布 | `publishing/publication.py`（冻结 JSONB、四格式 attempt 持久化） | `tests/api/test_publishing_api.py`、`make test-publishing-golden` | **PDF 无打印器**：`publication.py:84-86` 未注入 printer 时 pdf attempt 显式 failed → E03 缺口属实；四表一注报告类型未接入（E01） |
| 双轨结构（D045） | 导航三组 + `/operations` 只读演示页 | Web 45 项单测 | 经营轨数据管线未建（预期内，D049 后置） |
| S3 代理根因修复 | `infrastructure/s3_client.py`（默认绕过系统代理 + 超时） | 真实 MinIO 上传/发布/下载链路浏览器验证（2026-09-06 验收记录） | 容器路径回归归 F01 |
| 会计知识基础 | `config/metrics/accounting_foundation_v1.yaml`（167 科目/48 准则/32 分录模板，WS-1 定稿） | CI 结构校验 | 来源/有效期核验归 C01 |
| 运维保障（D038 D–G） | 单用户认证已落地（`api/auth.py`、代理鉴权） | `tests/api/test_auth_boundary.py` | 备份恢复、HTTPS、结构化日志、部署验收未做（F 组） |

## 2. A01 指定的四个核查点结论

1. **固定演示月份**：属实。生产编排路径 `orchestration.py:92` 仍从 `DASHBOARD_MONTHS` 取月份列表，非演示期间的批次无法按真实期间构建快照 → 列入 B06。
2. **报表完整性**：三公司已落库但覆盖度不同——顺丰 163 行（三大报表，A 股季报无权益变动表/附注，属披露缺失而非解析缺失）、腾讯 20 行（业绩公告为简表 + Non-IFRS 调节）、京东物流 118 行（FY 年报）；**没有统一的四表一注覆盖度规则与 reconciliation**（通过/不适用/缺失/失败四态未定义）→ 列入 B04。
3. **PDF 打印器**：缺失属实。月报 PDF 在无打印器时必 failed（可重试但永不可成功）；四表一注渲染器亦未建 → 列入 E02/E03。
4. **字典多源**：并存四个来源——`metric_dictionary_v0/v1.yaml`、DB 对象（0012）、引擎目录文档（0013，D048 双源哈希 parity 门禁保证一致性）。API 侧 DB 优先 YAML 回退；尚无统一语义身份与变更影响链 → 列入 C02/C04/C05。

## 3. 审计结论

- 旧 WS 计划标记的完成项（WS-0～WS-4）经代码与测试抽查**属实**，可作为新计划的复用资产，但其验收口径（演示月份、锚点抽样比对）**不满足** D049 的客观基础五条链要求——差距正是 M0–M5 的工作内容；
- 无阻碍 A02 开工的问题；A02 的事实契约需要覆盖 §2.2 的四态覆盖规则与 §2.4 的多源身份；
- 遗留未提交内容均为用户/其他工具文件，不进入任何提交。

## 4. 对后续任务的输入

| 输入 | 去向 |
| --- | --- |
| 固定月份、期间语义（单季/累计/时点流量） | A02 事实契约、B06 |
| 四表覆盖四态规则（通过/不适用/缺失/失败） | A02、B04 |
| 三家样本 SHA 清单与已验证锚点 | A03 验收数据集登记的起点 |
| 字典四源并存现状 | C02 统一身份设计约束 |
