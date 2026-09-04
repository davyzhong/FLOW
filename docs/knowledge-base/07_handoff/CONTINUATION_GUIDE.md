# Agent 接续指南

## 场景一：从零理解项目

阅读顺序：

1. `00_start_here/AGENT_START_HERE.md`
2. `00_start_here/PROJECT_STATE.md`
3. `04_decisions/DECISION_LOG.md`
4. `docs/superpowers/specs/2026-08-29-flow-v1-design.md`
5. `05_design/PROTOTYPE_INDEX.md`
6. `02_research/INDEX.md`

完成后应能够准确回答：

- FLOW 为谁解决什么问题？
- 为什么必须有数据中间层？
- Excel 模板与数据库标准层有什么区别？
- 为什么 AI 不能直接计算或发布数字？
- V1 包含和不包含什么？
- 当前下一步是什么？

## 场景二：从当前状态继续

截至 2026-09-04（代码基线 `c1a59d1`），Phase 1–10 功能窄切片、Pilot Phase 1 数据工作台/报告中心和单用户认证已实现；当前从 Pilot Phase 2 安全部署剩余工作继续，不再从 Phase 1 基础架构启动。

优先阅读以下文件（路径以仓库根目录为基准）：

1. `docs/implementation/2026-09-04-review-repairs.md`：R1–R9、N1–N3 最新修复、定向验收与真实存储限制；
2. `docs/operations/authentication.md`：AUTH_TOKEN、FLOW_WEB_PASSWORD、FLOW_WEB_ORIGIN 与签名会话；
3. `docs/superpowers/plans/2026-09-03-flow-pilot-readiness-phase-2-security-deployment.md`：核对已完成 A/B，补齐其余安全部署任务；
4. `docs/implementation/phase-pilot-1-user-closure.md` 与 `docs/implementation/phase-10-acceptance.md`：历史门禁及其边界；
5. `docs/knowledge-base/04_decisions/CHANGE_IMPACT_MAP.md`：确定变更传播范围。

先检查当前代码、迁移与服务配置。迁移头为 `0010_frozen_reports`，升级执行 `cd services/api && uv run alembic upgrade head`；旧快照缺少冻结 payload 时不可重渲染，已有产物可下载，需要新输出时从符合审批条件的数据重新冻结。

剩余工作包括真实 MinIO PutObject 超时调查与全链路补验、备份恢复、HTTPS 部署/回滚、密钥与网络边界、结构化日志。完成独立部署验收后再用脱敏真实数据检验准确性，依据试点证据确定 V1.1。浏览器导入的存储替身验证、真实认证验证与真实 S3 验收必须分别记录，不得互相替代。

## 场景三：修改已批准设计

1. 在决策日志中找到对应决策 ID；
2. 阅读变更影响图；
3. 说明修改原因和被替代方案；
4. 新增决策记录，不删除历史记录；
5. 修改正式规格并更新快照；
6. 重新检查所有下游对象和验收标准；
7. 重新生成文件清单和哈希。

## 场景四：核查原始依据

- 核查用户原话：读取可读 Codex 转录或历史 ChatGPT 会话；
- 核查机器级事件：读取 raw Codex JSONL；
- 核查研究来源：读取研究 Markdown，再查看对应图片；
- 核查页面演进：读取原型索引和相关 HTML；
- 核查文件未被修改：验证 `sha256sums.txt`。

## 防止上下文漂移

- 不把未来方向自动加入 V1；
- 不把被取代决策恢复为当前需求；
- 不让前端页面直接依赖 Excel；
- 不让 AI 绕过指标、证据和审阅；
- 不把外部参考图中的数据、品牌和水印当成 FLOW 内容；
- 任何新指标都必须说明标准数据依赖和计算口径；
- 任何新输出都必须引用同一 Report Snapshot。

## 已确定与仍待完成的边界

- 已确定：Next.js + FastAPI + Celery，PostgreSQL + Redis + S3 兼容存储；`flow.excel.v1` 标准契约、15 个版本化指标、5 个确定性 Playbook；
- 已实现：数据工作台、报告中心、API Bearer token 和单用户登录；未实现多角色、SSO 或多租户；
- 待完成：安全部署拓扑落地与验收、备份恢复、结构化日志、真实存储补验及真实数据试点；
- 待试点细化：指标阈值、企业报告品牌模板与正式品牌释义；
- AI 默认确定性/脚本 provider 与固定评估已落地，live provider 仍为 opt-in，不进入 CI。

## 任务完成与 GitHub 交付

规范仓库为 <https://github.com/davyzhong/FLOW>，本地远程名称为 `origin`。

用户已授权并要求：每次完整任务完成后，验证任务结果，将范围内的变更独立提交并推送当前分支到 `origin`。不得强制推送，不得夹带无关用户文件；推送失败时应保留本地提交并报告认证、权限或冲突等具体原因。
