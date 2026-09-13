---
doc_id: FLOW-OPS-THREE-AGENT-001
title: FLOW 三智能体并行执行使用手册
doc_type: operations
status: active
version: 1.0
created_at: 2026-09-13
updated_at: 2026-09-13
owner: FLOW
applies_to: s01-parallel-agent-execution
---

# FLOW 三智能体并行执行使用手册

## 1. 谁使用这份手册

- 产品负责人：只需要确认是否启动/暂停整个波次，不逐提交协调；
- 主协调者：建立基线、派发工作单、审查、合并、验证、更新权威状态；
- GPT-5.6 Sol、Kimi K3、GLM 5.3：各自在独立 worktree 完成被分配的白名单工作。

权威范围与依赖见[编排设计](../superpowers/specs/2026-09-13-flow-three-agent-parallel-orchestration-design.md)，逐步执行见[实施计划](../superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md)。本手册只说明怎么运行。

## 2. 启动前五项检查

主协调者必须确认：

1. 最新 main CI 绿色；
2. `git status --short` 无范围外修改；
3. 安全规格已按 `approved → review → 独立审查 → 用户明确批准最终字节 → approved` 完成修订，三份 S01 规格均为 approved 且无空白占位；
4. `make docs-check` 通过；
5. integration branch、当前 checkpoint 名称和该波次 `base_sha` 已明确写入当次派发消息。

任一不满足，不创建执行分支。

## 3. 标准分支创建方式

每名执行者使用自己的 worktree。示例中的 SHA 必须替换为主协调者公布的精确值：

```bash
git fetch origin --prune
git worktree add .worktrees/<lane-name> -b codex/<lane-name> <base_sha>
```

执行者禁止从未提交工作区复制文件，禁止把另一个执行分支当作基线，禁止直接推 `main`。

## 4. 通用工作单格式

主协调者给每个智能体的消息必须含：

```text
任务：<唯一任务名>
共同基线：<base_sha>
分支：<branch>
权威规格：<exact paths>
允许修改：<exact file/path allowlist>
禁止修改：状态文档、生成视图、不可变档案、其他 lane 文件
前置接口：<exact symbols/schema>
红灯测试：<exact command and expected failure>
绿色测试：<exact commands>
提交信息：<exact message>
交付：commit SHA、push 结果、测试摘要、改动文件列表、已知限制
停机条件：接口不完整、需要越界文件、迁移产生第二 head、测试环境异常
```

执行者遇到停机条件必须停止并报告，不能自行扩大范围。

## 5. 三个智能体的固定工作说明

### 5.1 GPT-5.6 Sol：安全正确性负责人

适合任务：明确合同下的安全领域模型、迁移、事务和负向测试。

工作提示词模板：

```text
你是 FLOW S01 的安全正确性执行者。严格依据 approved RBAC/审计规格和公布的 base_sha 工作。
先写失败测试，再实现最小行为。只修改工作单白名单中的 security core、身份配置、0026、publication/object-store 事务边界和对应测试。
除后续串行工作单明确授权的 publishing/operations 两条 route 外，不得修改业务 route、前端、路线图、HANDOFF、生成契约或任何不可变知识档案。
特别证明：deny-by-default、跨企业拒绝、规则不可自批、AI 无发布权、旧 Bearer 到期、AuditEvent UPDATE/DELETE 被数据库拒绝、writer 不自行 commit。
publication/object-store 已由工作单明确授权：使用调用方持有的数据库事务，并以 intent/outcome 覆盖对象存储成功与失败；不得引入第二套通用 outbox。若需要改变业务 route，停止并向主协调者提交具体文件与原因，不自行扩围。
结束时返回 commit、push、测试命令与结果、文件列表和残余风险。
```

Sol 的 `publishing.py`/`operations.py` 仅在 Wave 1 两条主分支已合并后，从新的 integration SHA 创建串行分支修改。该工作单必须带最终 route_policy 和已批准的四阶段 publication ABI；不得在并行 service 分支提前修改 route。

### 5.2 Kimi K3：跨仓路由与证据负责人

适合任务：利用长上下文盘点大量 route/schema/历史工作包并保持全局清单一致。

工作提示词模板：

```text
你是 FLOW S01 的跨仓路由与证据执行者。先完整读取工作单列出的规格和安全 ABI，不读取动态 Obsidian。
只修改 route_policy、工作单逐项列出的七组业务 route/schema 和测试；publishing/operations 两条发布 route 归 Sol 后续串行接线。不得使用可选 glob，不得实现第二套 Principal、authorize、Audit ORM 或迁移。
对最终挂载的 intake、investigations、metric_library、publishing、objective_reports、statements、operations、copilot、orchestration 入口逐项记录 method、normalized path、实际副作用、action、resource loader 和 owner；dashboard、workbench、workspace 等只读入口也必须记录明确豁免理由。不能按 GET/POST 或路径名称猜测副作用；会冻结快照的 GET 必须按写入口处理。
先写扫描与 API 失败测试，再接线。请求体中的 actor/operator 不得覆盖 Principal 身份。
遇到 ABI 缺字段、资源无法判定企业、需要修改非白名单 service 时立即停止并报告。
结束时返回 commit、push、route inventory 摘要、测试结果、文件列表和未闭合入口。
```

### 5.3 GLM 5.3：模块工程与全链验证负责人

适合任务：高密度前后端工程、AST 守护、生成契约和长链验证。

工作提示词模板：

```text
你是 FLOW S01 的模块工程执行者。严格区分产品可见三个模块与内部 shared_core owner。
前端工作只使用批准的静态模块描述，不提前依赖未合并 API；所有页面包裹 AppShell，旧路由保留在兼容分组，不用按钮暗示未实现能力。
模块后端工作必须让 ownership manifest 覆盖每个纳管文件恰好一次，并以 AST 证明 public 与 internal 不互相导入。
新增 /api/v1/modules 后必须从 FastAPI 重新生成契约，禁止手改 openapi.json 或 schema.d.ts。前端入口必须同时交付受控 Playwright runner，使 `make test-module-boundaries-e2e` 可在本地与 CI 使用动态端口运行并可靠清理。
只修改工作单白名单；不得更新路线图、PROJECT_STATE、S01 状态或 HANDOFF。
结束时返回 commit、push、测试与生成命令、文件列表、浏览器证据和残余风险。
```

## 6. 执行者交付格式

每个智能体必须以如下格式交接：

```text
状态：ready-for-integration | blocked
base_sha：...
branch：...
commit：...
push：success | failed(reason)
修改文件：逐项列出
红灯证据：命令 + 预期失败
绿色证据：命令 + 结果
范围检查：零越界 | 越界文件与原因
迁移/契约：无 | 精确 head/digest
残余风险：...
建议合并顺序：...
```

没有 commit、测试结果或文件清单的交付不进入合并队列。

## 7. 主协调者合并操作

主协调者为每个候选提交执行：

1. 确认 commit 基于所属 checkpoint 公布的 base 或已批准前置，并记录 base lineage；
2. 比对 `git diff --name-only <base>..<commit>` 与白名单；
3. 阅读完整 diff，不只看执行者总结；
4. 在 integration 分支使用普通 merge commit；
5. 每个候选合并后只运行该 lane 的本地目标测试和交叉测试；
6. 在 Bootstrap、Task 6 security、Wave 2、最终 Wave 3 四个检查点各推送一次 integration 并等待远端 `FLOW CI` workflow；
7. 用仓库内 S01 job 清单核对目标 SHA：workflow conclusion 为 success、清单中每个 job 为 success 且无 skip，才发布下一基线；main 没有 branch protection，不能以“required checks 为零”放行。

`.github/workflows/ci.yml` 只由主协调者修改；必须纳入安全纯测试与集成测试、模块 AST/API 测试、导航 Vitest 和 `make test-module-boundaries-e2e`，避免“CI 绿色但新门禁未运行”。

固定合并序列：安全 ABI → Sol 审计/0026/发布 service → Kimi 路由 → Sol 串行接入两条发布 route → GLM 模块 API → GLM 前端集成分支 → 全链证据 → 旧工作包 review 备忘 → 主协调者状态关闭。

## 8. 状态沟通节奏

执行者只在以下事件报告，不进行高频流水账：

- 红灯测试已建立；
- 遇到停机条件；
- 已推送 ready-for-integration；
- CI 失败且已定位原因。

主协调者维护唯一状态表：`queued / running / review / merged / ci-green / blocked`。只有 `ci-green` 才能作为下一依赖的 base。

## 9. 冲突与失败处理

- 两个分支修改同一文件：后到者停止，主协调者重新划分，不在执行分支自行合并；
- 执行者改了状态文档：从候选提交中排除该改动，要求重新提交；
- migration 出现多 head：拒绝合并，0026 只能由 Sol 创建；
- generated contract 冲突：删除人工解决结果，从最终 API 重生；
- CI 红：不合并下一 lane，不用重跑掩盖确定性失败；
- integration 合并后需回退：`git revert -m 1 <merge_commit>`，禁止 force-push；
- U8 恢复失败：立即停止 S01 关闭，保留 `flow-u8-freeze-20260913` 和备份不动。

## 10. 一次完整波次的完成检查

- [ ] 三个执行分支都从公布 SHA 建立；
- [ ] 文件白名单无重叠；
- [ ] 每条 lane 有红灯与绿灯证据；
- [ ] 主协调者逐 diff 审查；
- [ ] 按固定顺序合并；
- [ ] 交叉测试通过；
- [ ] integration CI 全绿；
- [ ] 状态文档只由主协调者更新；
- [ ] main 只用可追溯合并前进；
- [ ] main CI 全绿后才宣布完成。
