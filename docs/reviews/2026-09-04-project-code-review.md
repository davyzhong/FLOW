# FLOW 项目代码审查总结

> **适用性说明（2026-09-04，代码基线 `c1a59d1`）**：本文是修复前代码的审查快照，保留原问题、行号、测试失败和当时 CI 结果。R1–R9 及追加 N1–N3 已分别由 `fa171ec`、`e688f1b`、`c1a59d1` 修复，不再是当前待修缺陷；历史 CI 状态不代表当前提交。真实 S3 发布链路、Pilot Phase 2 剩余部署工作和真实数据试点仍须单独验收。
> 当前入口见[文档导航](../README.md)，后续缺陷修复与验证边界见[2026-09-04 修复验收](../implementation/2026-09-04-review-repairs.md)。

审查日期：2026-09-04。代码基线：`f5549cbfd901a055993c0a4fc783d768ee956498`。

结论：当前代码存在 **3 项 P1、6 项 P2**，建议修复后再验收真实数据用户闭环。主要风险集中在报告冻结、证据签发资格、手工映射以及 API/前端之间的衔接；现有测试通过不能证明这些跨步骤行为正确。本次只审查并输出报告，未修复业务代码。

审查以知识库起点、项目状态、正式 V1 规格、决策日志 D033–D039 和变更影响图为依据，覆盖 Intake、指标/分析链路的重点代码、Investigation、Copilot、Publishing、Web 用户闭环与验收脚本。不是逐行穷尽或依赖漏洞审计。身份权限、部署加固和真实数据试点已明确延期，不作为本次新发现的代码缺陷。工作区既有未跟踪材料未纳入审查交付。

## 按优先级排列的发现

### 1. [P1] 同一冻结报告会随当前分析和复核状态改变内容

- 位置：`services/api/src/flow_api/publishing/service.py:141–145,205–210`。
- 触发：冻结报告后，退回原已批准 Finding、批准另一 Finding，或为同一指标快照生成新的 Analysis Run，然后重新发布原报告。
- 原因：`build_report_view` 不读取冻结的 `ReportSnapshotItem`，而重新选择最新 Analysis Run 和当前 approved Findings。`PublicationService.publish` 每次都会重建视图。
- 影响：相同 report ID/version 的内容和分析运行身份会漂移，分时生成不同格式也可能不一致，违反同一冻结快照和历史可追溯要求。
- 证据：静态核对冻结、视图构建和发布完整调用链；本次未运行数据库状态变更复现。
- 建议：冻结时保存确定的运行、条目及可变结论/证据内容；后续渲染只读冻结内容，变更须生成新报告版本。增加“冻结后改变复核状态/新增运行再重试”的回归。

### 2. [P1] 否决关键证据后，Finding 仍保留正式发布资格

- 位置：`services/api/src/flow_api/investigation/state_machines.py:167–176`；发布检查在 `services/api/src/flow_api/publishing/service.py:71–76`。
- 触发：批准 Finding 后，将其 verified Evidence 改为 rejected，再冻结报告。
- 原因：证据决策只更新 Evidence，不检查或退回已 approved 的 Finding；冻结只检查 Finding.status，渲染仅过滤掉 rejected Evidence。
- 影响：证据已被否决的发现仍能作为已签发结论进入新报告，破坏证据决定发布资格的核心约束。
- 证据：状态迁移、调用层和发布筛选静态核对。此问题不同于第 1 项：这里即使尚未冻结报告，新冻结动作也会接受失效资格。
- 建议：证据降级时原子地退回 Finding，或要求先退回复核；新报告冻结必须重新检查全部必要证据与完整结论。已冻结历史报告另以版本/撤回记录处理。

### 3. [P1] 后端确认和校验拒绝已保存的手工映射版本

- 位置：`services/api/src/flow_api/api/routes/intake.py:403–405,467–469`。
- 触发：通过 overrides 创建新映射版本，再确认该版本或使用它校验源文件。
- 原因：接口重建自动映射并比较 mapping hash，而非使用已持久化的手工映射。manual_override 元数据本身也改变 hash。
- 影响：真实外部工作簿需要人工修正时，流程固定返回 `409 mapping_source_mismatch`，无法校验与发布。
- 证据：使用真实 `external_logistics_nonstandard_v1.xlsx`、真实映射覆盖逻辑和 `validate_source`，仅 DB/storage 使用 stub。即使覆盖回原来同一源列，得到 `Override persisted different hash: True`，随后 `validate: 409 mapping_source_mismatch`。
- 建议：从保存的 mapping_spec 恢复 proposal，校验源文件身份与 SHA，再使用该 proposal 提取；回归应串联 override → confirm → validate。

### 4. [P2] 前端手工映射请求发送空 SHA，必然被接口拒绝

- 位置：`apps/web/components/data/data-workbench.tsx:107–112`。
- 触发：用户修改任一映射源表头并确认。
- 原因：`applyOverrides` 的 sourceSha256 参数固定传空字符串，但 `MappingOverrideRequest.source_sha256` 要求长度为 64；上传返回的 `state.source.sha256` 已存在却未使用。
- 影响：请求在 schema 校验阶段返回 422，甚至无法到达第 3 项的后端映射逻辑。这是需要独立修复的前端断点。
- 证据：调用参数与 `services/api/src/flow_api/api/schemas/intake.py:109–113` 直接对照。现有组件 mock 不验证请求体。
- 建议：传入上传返回的 SHA，并增加请求体断言及真实 API 串联覆盖。

### 5. [P2] 有可确认警告的导入无法从工作台完成发布

- 位置：`apps/web/components/data/data-workbench.tsx:252–273`。
- 触发：导入校验产生至少一条未确认 warning。
- 原因：界面只展示问题计数，没有问题详情、原因填写或确认操作；虽有 `intakeApi.acknowledgeWarning`，工作台未调用它。
- 影响：点击发布被后端拒绝，用户无法在该流程中完成允许的警告确认；阻断问题也没有行列级修复信息。
- 证据：后端 `intake/service.py:486–487` 明确要求所有 warning 已确认；前端组件测试带两条 warning 却直接 mock 发布成功，未复现真实契约。
- 建议：保留并显示 validate 返回的 issues、修复建议、确认状态，提供有原因的逐条确认与重新校验入口，再允许发布。

### 6. [P2] 成功的 Copilot 交互审计在请求结束时回滚

- 位置：`services/api/src/flow_api/copilot/service.py:208–212`；`api/routes/copilot.py:92,123,154`；`api/routes/investigations.py:32–34`。
- 触发：三个 Copilot API 任意一个成功返回。
- 原因：service 仅 add/flush；成功 route 没有 commit；共享 session dependency 关闭普通 Session，不提交。只有验证拒绝路径显式 commit。
- 影响：用户拿到 interaction_id，但成功交互记录不持久化，审计无法还原正常回答。
- 证据：静态核对三条路由、service 和 sessionmaker/依赖的事务语义；本次未完成真实数据库持久化测试。
- 建议：明确成功和拒绝的事务边界，增加请求完成后以独立 Session 查询 interaction_id 的测试。

### 7. [P2] 新批次产生分析后，旧批次报告大纲错误返回 404

- 位置：`services/api/src/flow_api/copilot/service.py:123–129`。
- 触发：A、B 均有有效分析，B 的运行较新，再请求 A 的 report-outline。
- 原因：查询先取全库最新 Analysis Run，之后才比对 batch_id，没有在 SQL 中限定目标批次和 published 状态。
- 影响：A 明明有可用分析仍被判定不存在，历史批次无法生成大纲。
- 证据：静态 SQL 查询与错误分支核对。
- 建议：先按请求批次及 published 状态过滤，再取该批次最新运行；增加双批次测试。

### 8. [P2] PPTX 多类正文文本框尺寸为零

- 位置：`services/api/src/flow_api/publishing/renderers.py:50–53,64–67,88–91`。
- 触发：使用当前默认模板生成 PPTX。
- 原因：layout 5 只有标题，因此正文走 `add_textbox(0, 0, 0, 0)`。
- 影响：经营概览、指标正文和证据索引没有有效显示区域，文本可能溢出或裁切，不能作为正常汇报页面交付。
- 证据：运行真实 `render_pptx`，重新加载产物，确认正文文本框 bounds 为 `0 0 0 0`。未以 PowerPoint/LibreOffice 完成视觉渲染验收；具体裁切表现依赖阅读器。
- 建议：设置实际位置、宽高和分页规则；文本提取之外增加渲染截图及溢出检查。

### 9. [P2] 同源代理丢弃下载文件名，报告下载没有扩展名

- 位置：`apps/web/app/api/v1/[...path]/route.ts:7–12`；`apps/web/components/reports/reports-center.tsx:142–148`。
- 触发：通过报告中心下载任一成功产物。
- 原因：代理只保留 content-type，丢弃后端 Content-Disposition；报告中心读取不到 filename，统一回退为 `flow-report`。
- 影响：PPTX/XLSX/PDF/HTML 下载失去格式扩展名与版本文件名，文件识别和多格式归档受影响。模板下载的带扩展名 fallback 掩盖了相同代理问题。
- 证据：后端下载头、代理响应构造和前端 anchor.download 静态核对；现有代理测试仅验证 JSON 与 content-type。
- 建议：透传允许的 Content-Disposition 等下载元数据，同时按产物格式提供可靠 fallback；通过同源代理检查四格式 suggestedFilename。

## 验证结果与限制

| 检查 | 本次结果 |
| --- | --- |
| `make test-web` | 9 个测试文件、18 个测试全部通过 |
| API Ruff | 通过 |
| Web ESLint | 通过，有 1 条既有 warning：copilot-panel.tsx 的 context 未使用 |
| API mypy | 113 个源文件通过 |
| Web TypeScript | 通过 |
| `make test` 中的 API pytest | 189 passed、5 failed、96 errors；未通过 |
| 后端环境 | 已确认 localhost:5432 PostgreSQL 连接拒绝；未将所有失败逐个归因为环境，也不据此上报新的业务缺陷 |
| 手工映射定向复现 | 真实 fixture/映射逻辑，DB/storage stub，确认 409 |
| PPTX 定向检查 | 实际生成并重新读取，确认零尺寸正文框 |

`make test` 在 API 阶段退出，Web 测试另行独立运行。未执行会清空 public schema 的 `scripts/acceptance.sh`，未运行全栈浏览器门禁，未启动或重置现有数据库。未声称本次完成全量验收。

## 修复与后续验收建议

1. 首先修复报告冻结与证据资格两个 P1，保证同一报告版本稳定、失效证据不能进入新报告。
2. 联合修复前后端手工映射与警告确认，使用需要修正的非标准工作簿跑完整用户路径。
3. 修复 Copilot 事务与批次筛选，以及 PPT 排版、报告下载元数据。
4. 在隔离测试数据库中运行全量回归，并补充真实上传 → 手工映射 → 警告确认 → 发布 → 调查签发 → 冻结 → 四格式下载的浏览器测试。

当前 `user-closure.spec.ts` 的上传用例止于“清洗与校验结果”，报告中心用例仅检查页面表单，尚不能证明完整用户闭环。报告黄金测试中的文本一致性也不能代替冻结后状态变化测试及 PPT 视觉验收。
