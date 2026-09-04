# FLOW 同步 GitHub 后的代码复审

日期：2026-09-04。审查远端代码基线：`a1662e850d5e58c377451998d932e772451da71f`。

结论：确认 **12 项问题（4 项 P1、8 项 P2）**。上一轮 9 项仍存在；最新更新新增 3 项：启用鉴权后 Web 业务请求不可用、生成合约漂移、鉴权测试破坏无数据库 unit job。建议优先恢复鉴权衔接和 CI，再修复报告可信度及导入流程，不应将当前状态认定为试点就绪。

## 同步结果与审查范围

- 已执行 `git fetch origin`，核实本轮抓取时 main 从 `f5549cb` 前进到 `a1662e8`，相差 1 个提交、7 个文件，新增 Bearer 鉴权、鉴权测试、用户闭环 CI 和两份计划。
- 已将本地上一轮审查文档提交重放到最新 origin/main 上，重放后为 `3cac366`；该提交只包含旧审查报告，业务代码等于远端基线。
- 同名未跟踪的 Phase 1 计划与远端 SHA-256 完全相同，先用定向 stash 保留副本再同步，原路径现为远端跟踪文件。其余 7 个未跟踪原始文件未修改、未提交。保留 stash：`preserve identical local plan before review sync`。
- 已重新核对最新 auth/router/CI/计划，并沿 Intake → 指标与分析 → Investigation → Copilot → Publishing → Web 链路复查上一轮发现。项目知识库、正式规格及 D033–D039 没有随本次远端提交变化，继续作为审查依据。
- 本次为代码审查与报告，不实施修复，也不是逐行穷尽、生产部署验收或依赖漏洞扫描。计划中尚未实现的登录、备份、HTTPS 等，不单独计为新增代码缺陷。

## 最新更新引入的问题

### N1. [P1] 启用 Bearer 认证后，Web 代理无法调用业务 API

位置：`apps/web/app/api/v1/[...path]/route.ts:28–33`；新增认证挂载：`services/api/src/flow_api/api/router.py:16–21`。

配置后端 `AUTH_TOKEN` 后，各业务 API 开始要求 Bearer；但代理仅发送 Accept/Content-Type，既不读取服务端 token，也不保留传入 Authorization。因此经同源代理的驾驶舱、导入、调查、AI 和报告请求都会得到 401。新安全计划 Task A 已明确要求代理附加服务端 token，此次实现遗漏了该部分。

验证：编译并执行真实 `route.ts`，以捕获参数的 fetch 替身模拟上游。传入 `Authorization: Bearer correct-token`，捕获到上游 headers 只有 `{"Accept":"application/json"}`，模拟受保护上游返回 401。该验证证明代理丢失凭据，未声称完成真实浏览器登录验收。

建议：完成服务端认证转发与浏览器会话边界，并增加开启认证时的同源请求测试。不能在没有 Web 会话保护的情况下简单给所有匿名代理请求注入后端 token，否则会削弱新认证边界；也不要把服务端共享密钥公开到前端。

### N2. [P2] 鉴权改变 OpenAPI，却没有同步生成合约

位置：`services/api/src/flow_api/api/router.py:16–21`；产物：`packages/contracts/openapi.json`、`packages/contracts/src/schema.d.ts`。

新增 Header dependency 后，运行时 OpenAPI 为业务操作增加 authorization 参数，但提交中的生成产物仍是旧版，导致接口描述与运行时不一致，独立 contracts 门禁失败。

验证：只在内存比较 `create_app().openapi()` 与已提交 JSON，确认 **27 个 operations 漂移**；例如 workspace GET 的旧 parameters 为空，新版包含 authorization header。未运行会覆写跟踪文件的生成脚本。GitHub 上该基线的 contracts job 也已失败，但本轮未逐行获取其日志归因。

建议：同步生成 OpenAPI/TypeScript，并在干净工作树执行 contracts-check；避免先生成再检查的顺序掩盖已提交产物漂移。

### N3. [P2] 新鉴权测试让无数据库的 unit job 强制连接 PostgreSQL

位置：`services/api/tests/api/test_auth_boundary.py:24–26`；选择该文件的 CI：`.github/workflows/ci.yml:44–59`。

模块 autouse fixture 无条件执行 Alembic upgrade。unit job 只安装 Python 依赖，没有启动数据库，但会收集整个 tests/api，且未排除新文件。因此即使测试只验证无 token 的 401，也在执行断言前因数据库连接失败。

验证：以不可用端口模拟无数据库环境，仅运行新增鉴权测试，得到 **5 errors**，全部位于迁移 fixture 的连接拒绝。GitHub 同基线 unit job 已失败；本轮未逐行获取远端日志归因。

建议：这些 health/workspace 鉴权用例不需要真实数据库，去掉强制迁移并隔离依赖；真正需要数据库的用例放进 integration job。保留与 CI 相同的无数据库运行方式作为回归。

## 上一轮问题的重新核对

以下 9 项均重新核对，相关实现未被最新提交修复。详细早期证据保存在同目录 `2026-09-04-project-code-review.md`，下表给出本轮可独立阅读的触发条件与影响。

| 编号 | 优先级 | 当前定位 | 触发条件、问题与建议 |
| --- | --- | --- | --- |
| R1 | P1 | `services/api/src/flow_api/publishing/service.py:141–145,205–210` | 冻结后退回/新增批准 Finding 或新增 Analysis Run，再发布原报告时重新选最新运行和当前 approved Findings，忽略冻结条目。同一 report ID/version 可变内容。应持久化冻结视图及可变结论内容，重试只读冻结版本。 |
| R2 | P1 | `services/api/src/flow_api/investigation/state_machines.py:167–176` | 已批准 Finding 的证据可改为 rejected，但 Finding 保留 approved；冻结只检查 Finding.status，仍可进入新报告。证据降级必须原子退回复核，冻结再次验证证据资格。 |
| R3 | P1 | `services/api/src/flow_api/api/routes/intake.py:403–405,467–469` | 手工 override 后确认/校验重新生成自动 proposal 比 hash，新版本固定被 409 拒绝。应恢复持久化 mapping_spec 并校验源身份，再按该版本提取。本轮核对逻辑仍在；上一轮真实 fixture + DB/storage stub 已复现。 |
| R4 | P2 | `apps/web/components/data/data-workbench.tsx:107–112` | 用户修改映射时 source_sha256 固定传空，schema 要求 64 字符，直接 422；应传上传返回 SHA。这与 R3 是两个独立断点，修复一个不能打通流程。 |
| R5 | P2 | `apps/web/components/data/data-workbench.tsx:252–273` | 校验存在未确认 warning 时，界面只有计数和发布按钮，没有问题确认/原因输入；后端拒绝发布，用户无法继续。应展示 issues、原因、确认状态与修复入口。组件 mock 带 warning 却直接发布成功，掩盖真实阻断。 |
| R6 | P2 | `services/api/src/flow_api/copilot/service.py:208–212` | 成功交互只 flush，三个 route 成功路径没有 commit，session dependency 退出时关闭并回滚。返回 interaction_id 却无持久审计；应补成功事务提交并用独立 Session 验证。 |
| R7 | P2 | `services/api/src/flow_api/copilot/service.py:123–129` | report-outline 先取全库最新 run 再比较请求 batch；B 更新后请求 A 会错误 404。应先过滤目标 batch 和 published 状态，再选最新运行。 |
| R8 | P2 | `services/api/src/flow_api/publishing/renderers.py:50–53,64–67,88–91` | 默认 layout 5 无正文占位符，走零宽高 textbox，概览/指标/证据正文没有有效区域。应设置实际几何尺寸并做视觉验收。上一轮真实 PPTX 重读确认 bounds 为零；本轮代码未变，未追加阅读器视觉验收。 |
| R9 | P2 | `apps/web/app/api/v1/[...path]/route.ts:7–12`、`apps/web/components/reports/reports-center.tsx:142–148` | 代理丢弃 Content-Disposition，报告下载统一 fallback 为 flow-report，缺格式扩展名和版本文件名。应透传受控下载头并提供按格式 fallback。 |

R1、R2、R6、R7 本轮证据为重新核对完整调用链与事务/查询逻辑，未声称完成真实数据库状态变更复现。P1 表示应优先修复的核心流程或正确性问题，P2 表示需要安排修复的功能/工程缺陷。

## 验证结果

| 本轮检查 | 结果 |
| --- | --- |
| 后端无数据库测试子集 | 97 passed，23.13 秒 |
| 前端 Vitest | 9 个文件、18 个测试通过 |
| Ruff | 通过 |
| mypy | 114 个源文件通过 |
| Web TypeScript | 通过 |
| ESLint | 无错误；1 条既有 warning：copilot-panel.tsx 的 context 未使用 |
| OpenAPI 内存对比 | 27 个 operations 漂移，确认 N2 |
| 鉴权代理定向验证 | 真实代理函数丢失 Authorization，确认 N1 |
| 新鉴权测试无数据库定向验证 | 5 个 fixture errors，确认 N3 |

后端子集命令（从 services/api 执行）：

```sh
uv run pytest tests/domain tests/data_contract tests/intake tests/fixtures tests/dashboard tests/test_health.py tests/api/test_workspace.py -q --tb=short
```

本轮没有重跑上一轮已知受本地 PostgreSQL 不可用阻断的全量后端测试，没有清空数据库或运行破坏性 acceptance reset。没有把旧轮的 189/5/96 结果冒充新基线测试结果。

## GitHub CI 实际状态

查询来源：[FLOW CI — a1662e8](https://github.com/davyzhong/FLOW/actions/runs/33881177857)。以下为本轮读取时的快照，不代表未来状态：

- 已失败：unit、contracts、intake-e2e、user-closure-e2e。
- 已通过：static-python、static-web、data-contract、metrics-known-answers、analysis-invariants、dashboard、investigation-e2e、publishing-golden、copilot-evals、migrations、smoke。
- 仍运行：integration；workflow 整体当时仍为 in_progress。

没有逐一诊断远端失败日志，因此不把 intake-e2e/user-closure-e2e 的失败直接归因于上述任意缺陷。已通过的 publishing-golden 也不覆盖冻结后状态漂移和 PPT 阅读器布局，不能消除 R1/R8。

## 建议修复顺序

1. 补齐认证的 Web 接入与会话边界，同步合约，恢复无数据库 unit job；明确最新绿色代码基线。
2. 修复冻结报告和证据签发不变量，验证跨时刻、跨格式重试及证据否决后的新报告资格。
3. 联合修复前后端手工映射和 warning 确认，使用非标准工作簿跑完整导入路径。
4. 修复 Copilot 审计/批次、PPT 排版、下载文件名；在隔离数据库与浏览器中验证上传到四格式下载的完整闭环。

本轮交付只增加本报告，保留上一轮报告作为历史基线；不改知识库事实或业务实现。
