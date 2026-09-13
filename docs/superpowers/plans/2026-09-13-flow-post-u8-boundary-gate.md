---
doc_id: FLOW-PLAN-POST-U8-BOUNDARY-001
title: U8 后战略边界、事实合同与安全门禁实施计划
doc_type: plan
status: proposed
version: 1.0
created_at: 2026-09-13
updated_at: 2026-09-13
owner: FLOW
depends_on: [FLOW-DESIGN-STRATEGIC-RESET-001, FLOW-WI-U08]
acceptance_refs: [strategic-reset-stage-1, facts-contract-v2-gate, security-rbac-audit-gate]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: post-u8-boundary-gate
supersedes: []
superseded_by: null
---

# U8 后战略边界、事实合同与安全门禁 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不破坏 U8 冻结版本和现有公开财报/物流能力的前提下，建立三层两模块工程边界、Financial Facts Contract V2、企业周期身份、角色权限与审计门禁。

**Architecture:** 现有 API、数据库对象和冻结报告保留为兼容层；企业周期、V2 事实上下文和授权对象全部追加实现。公开模块与内部工作台只依赖共享底座，不相互调用；旧入口在等价验证前不删除。

**Tech Stack:** Python 3.13、FastAPI、Pydantic v2、SQLAlchemy 2、Alembic、PostgreSQL、pytest、Next.js 16、React 19、TypeScript、Vitest、Playwright、OpenAPI TypeScript。

---

## 执行边界

本计划只覆盖战略设计阶段 1，不是第二份路线图。状态只回写 `docs/50_plans/CURRENT_ROADMAP.md` 和 `docs/50_plans/work_items/S01--post-u8-boundary-contract-security.md`。

Task 2 只可在 U08 completed、有可恢复冻结点且工作区无范围外修改后开始。Task 3–8 还必须等待三份子规格全部 approved，并在各任务开始前用 `SPEC_INDEX.md` 和文档门禁重新确认。本计划不实现公开模块 C 级完整报告链、内部月度工作台或真实企业三周期验证，它们在门禁关闭后分别制定计划。

Task 3–8 的共同 Step 0：运行 `python3 scripts/documentation/require_approved_specs.py FLOW-SPEC-MODULE-BOUNDARIES-V1 FLOW-SPEC-FINANCIAL-FACTS-V2 FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1 && make docs-check`。脚本解析三个精确 doc_id 的 frontmatter、权威路径与 `SPEC_INDEX` 行，并强制三者 `status: approved`；任一不符即非零退出，不写代码。

## 文件结构

| 单元 | 路径 | 职责 |
|---|---|---|
| 模块规格 | `docs/40_specs/platform/module-boundaries-v1.md` | 依赖方向、兼容入口、禁用耦合 |
| 事实规格 | `docs/40_specs/financial-facts/financial-facts-contract-v2.md` | V2 字段、比较身份、血缘、兼容策略 |
| 安全规格 | `docs/40_specs/security/internal-workbench-rbac-audit-v1.md` | 角色动作矩阵、审计、模型输入边界 |
| V2 模型 | `services/api/src/flow_api/financial_facts_v2/` | 纯领域模型和 V1/canonical 适配 |
| 企业周期 | `services/api/src/flow_api/enterprise/` | Enterprise、AnalysisCycle |
| 权限审计 | `services/api/src/flow_api/security/` | Principal、授权判断、追加式审计 |
| 企业迁移 | `services/api/migrations/versions/0025_enterprise_cycle.py` | 企业、周期和可判定批次身份 |
| 安全迁移 | `services/api/migrations/versions/0026_security_audit.py` | 角色绑定、追加式审计和 DB 不可变保护 |
| 模块 API | `services/api/src/flow_api/modules/`、`api/routes/modules.py` | 模块 registry 与入口 |
| 模块 UI | `apps/web/app/public/`、`apps/web/app/internal/` | 两模块入口和可见状态 |
| 契约 | `packages/contracts/openapi.json`、`src/schema.d.ts` | 从 FastAPI 生成，不手改 |

### Task 1：冻结 U8 基线并开启 S01

**Files:**
- Modify: `docs/50_plans/work_items/U08--production-readiness.md`
- Modify: `docs/50_plans/work_items/S01--post-u8-boundary-contract-security.md`
- Modify: `docs/50_plans/CURRENT_ROADMAP.md`
- Modify: `docs/50_plans/views/active.md`
- Modify: `docs/50_plans/views/blocked.md`
- Modify: `docs/50_plans/views/completed.md`
- Create: `docs/60_delivery/YYYY-MM-DD-u8-production-freeze.md`
- Create: `scripts/accept_u8_production.sh`
- Create: `scripts/documentation/plan_views.py`
- Modify: `scripts/check_docs.py`
- Modify: `Makefile`
- Test: `scripts/tests/test_u8_acceptance_gate.py`
- Test: `scripts/tests/test_plan_views.py`

- [ ] **Step 1: 先为计划视图生成器写失败测试**：work-item 与 CURRENT_ROADMAP 状态缺失、重复或不一致时失败；确定性生成 active/blocked/completed。

- [ ] **Step 2: 运行 `python3 -m unittest -v scripts.tests.test_plan_views`，确认因生成器或一致性规则不存在而 FAIL。**

- [ ] **Step 3: 实现 `plan_views.py`，接入 `scripts/check_docs.py` 与 `make docs-check`；运行 `python3 scripts/documentation/plan_views.py --write && python3 scripts/documentation/plan_views.py --check` 生成三视图，再重跑测试确认 PASS。**

- [ ] **Step 4: 为 U8 专属验收写失败测试**：缺 HTTPS URL、TLS 校验失败、发布/下载 SHA 不一致、`pg_restore` 非零、关键表或冻结载荷哈希不一致、恢复后健康检查不可达、任何步骤被 skip，均必须令总门禁非零退出。测试同时固定 `full` 和 `restore-u8-baseline` 两种模式的参数合同；未知模式必须失败。

- [ ] **Step 5: 实现 fail-closed 的 U8 验收入口**：`scripts/accept_u8_production.sh full` 要求显式 `FLOW_U8_BASE_URL=https://...`；`restore-u8-baseline` 还要求显式备份路径和隔离验收数据库。恢复模式只验证 U8/0024 基线、关键表、旧冻结载荷哈希和 HTTPS 健康；两种模式都禁止 `|| true` 和“跳过也成功”。

- [ ] **Step 6: 运行 U8 专属验收**

Run: `python3 -m unittest -v scripts.tests.test_u8_acceptance_gate && FLOW_U8_BASE_URL=https://<验收域名> bash scripts/accept_u8_production.sh full && make docs-check`

Expected: 全部退出码为 0 且无 skip；冻结→发布→下载→SHA-256、真实 HTTPS、严格恢复和恢复后健康检查均有证据。

- [ ] **Step 7: 写冻结记录**：登记提交、迁移头、镜像、TLS 终止位置、对象存储、恢复点和命令结果；禁止写密钥或企业数据。
- [ ] **Step 8: 创建并核验 `flow-u8-freeze-YYYYMMDD` annotated tag**，日期使用执行日。
- [ ] **Step 9: 证据齐全后将 U08 改 completed、S01 改 active，并同批运行 `python3 scripts/documentation/plan_views.py --write && python3 scripts/documentation/plan_views.py --check`；否则保持原状态。**
- [ ] **Step 10: 提交并推送**：`git commit -m "feat(ops): enforce and freeze U8 production gate"`，随后推送提交和标签；远端 CI 绿后才能开始 Task 2。

### Task 2：编写并批准三份实施子规格

**Files:**
- Create: `docs/40_specs/platform/module-boundaries-v1.md`
- Create: `docs/40_specs/financial-facts/financial-facts-contract-v2.md`
- Create: `docs/40_specs/security/internal-workbench-rbac-audit-v1.md`
- Modify: `docs/40_specs/SPEC_INDEX.md`
- Create: `scripts/documentation/require_approved_specs.py`
- Test: `scripts/tests/test_require_approved_specs.py`

- [ ] **Step 1: 以 review 状态登记三份规格**，分别定义输入、输出、对象、状态、不变量、失败行为、迁移和验收。
- [ ] **Step 2: 固定模块依赖**：`public_analysis -> shared_core <- internal_workbench`；两模块禁止互相导入，旧路由只是兼容层。
- [ ] **Step 3: 固定 V2 最小字段**：scenario/version、enterprise/cycle、组织范围、比较期间、文件 SHA、workbook/sheet/cell-or-range、import/mapping/management-basis version。
- [ ] **Step 4: 固定权限矩阵**：Finance BP、经分专员、规则负责人、两个 AI、服务账户逐动作 allow/deny；规则不可自批、AI 无发布权、跨企业默认拒绝。
- [ ] **Step 5: 先为 approved-spec 门禁写测试**：精确 doc_id 缺失、路径错、SPEC_INDEX 缺行、draft/review 均失败；三个 approved 才通过。实现脚本并把它接入 Task 3–8 的共同 Step 0。
- [ ] **Step 6: 运行 `make docs-check` 并对每份 review 规格执行最多三轮独立规格审查。**
- [ ] **Step 7: 用户批准后转 approved，在最终字节上重跑 `python3 scripts/documentation/require_approved_specs.py ... && make docs-check && git diff --check`，再提交并推送；远端 CI 绿后才能开始 Task 3。**

### Task 3：建立 Financial Facts Contract V2 纯领域模型

**Files:**
- Create: `services/api/src/flow_api/financial_facts_v2/__init__.py`
- Create: `services/api/src/flow_api/financial_facts_v2/models.py`
- Test: `services/api/tests/financial_facts_v2/test_models.py`

- [ ] **Step 1: 写失败测试**：内部事实缺 enterprise、cycle、import、mapping 或 workbook locator 任一字段均被拒绝；float 金额被拒绝。
- [ ] **Step 2: 运行 `cd services/api && uv run pytest tests/financial_facts_v2/test_models.py -v`，确认因模块不存在而 FAIL。**
- [ ] **Step 3: 实现最小冻结模型**：

```python
class Scenario(StrEnum):
    ACTUAL = "actual"
    BUDGET = "budget"
    FORECAST = "forecast"

class FactContext(FrozenModel):
    module: Literal["public", "internal"]
    enterprise_id: UUID | None = None
    analysis_cycle_id: UUID | None = None
    scenario: Scenario
    scenario_version: str
    import_version_id: UUID | None = None
    mapping_version_id: UUID | None = None
    management_basis_version: str | None = None
```

`WorkbookLocator` 强制 64 位 SHA、workbook、sheet、cell/range；validator 对 internal 强制完整身份，对 public 保留 page/table/row。

- [ ] **Step 4: 增加比较测试**：同比、环比、实际预算必须引用两个完整 V2 身份；跨企业、单位、范围或预算版本不可比较。
- [ ] **Step 5: 运行 pytest、ruff、mypy 并确认 PASS。**
- [ ] **Step 6: 提交 `feat(facts): add Financial Facts Contract V2 models`。**
- [ ] **Step 7: 执行 `git push origin HEAD`，远端 CI 绿后进入下一任务。**

### Task 4：实现 V1 与 canonical 显式适配

**Files:**
- Create: `services/api/src/flow_api/financial_facts_v2/adapters.py`
- Test: `services/api/tests/financial_facts_v2/test_adapters.py`
- Test: `services/api/tests/statements/test_fact_contract.py`

- [ ] **Step 1: 写 V1 公开事实无损适配测试**，保留 subject、period、unit、scope、standard、value/missing reason、restated 和 source。
- [ ] **Step 2: 写 canonical 内部事实缺身份失败测试**：冻结 `FactContext` 或 `WorkbookLocator` 中 scenario/version、enterprise/cycle、import/mapping、管理口径版本、文件 SHA、workbook/sheet/cell-range 任一缺失都失败，禁止制造默认值。
- [ ] **Step 3: 实现 `from_public_v1(fact)` 与 `from_canonical_row(row, *, context: FactContext, provenance: WorkbookLocator)`；context/provenance 必须由持久化 join 得到并完整冻结，不从单条 canonical row 猜测身份；不提供会丢字段的通用 V2→V1。**
- [ ] **Step 4: 运行 `cd services/api && uv run pytest tests/financial_facts_v2 tests/statements/test_fact_contract.py -v`，确认新旧合同同时 PASS。**
- [ ] **Step 5: 提交 `feat(facts): adapt public and canonical facts to V2`。**
- [ ] **Step 6: 执行 `git push origin HEAD`，远端 CI 绿后进入下一任务。**

### Task 5：新增企业空间和月度分析周期

**Files:**
- Create: `services/api/src/flow_api/enterprise/__init__.py`
- Create: `services/api/src/flow_api/enterprise/models.py`
- Modify: `services/api/src/flow_api/infrastructure/models/intake.py`
- Modify: `services/api/src/flow_api/infrastructure/models/__init__.py`
- Create: `services/api/migrations/versions/0025_enterprise_cycle.py`
- Test: `services/api/tests/integration/test_enterprise_cycle_schema.py`
- Test: `services/api/tests/integration/test_migrations.py`

- [ ] **Step 1: 写失败测试**：enterprise code 唯一；cycle 在 `(enterprise_id, period_key)` 唯一；批次持久化 `module_kind`（legacy/public/internal）和 `fact_context_version`；新 internal/v2 batch 必须有 cycle；迁移前 batch 明确回填 legacy/v1 并允许 cycle 为空。
- [ ] **Step 2: 运行目标测试确认缺表 FAIL。**
- [ ] **Step 3: 追加 enterprise、analysis_cycle、`analysis_batch.analysis_cycle_id`、`module_kind` 和 `fact_context_version`；不修改任何 frozen_view 或历史事实值。**
- [ ] **Step 4: 加数据库合法组合矩阵**：仅允许 `legacy/1/cycle NULL`、按子规格定义的 `public/1|2`、以及 `internal/2/cycle NOT NULL`；`internal/1`、`internal/2/cycle NULL`、`legacy/2` 等全部由单一 CHECK 拒绝。内部创建服务重复校验，并为每个非法组合写直接 SQL 与 ORM 测试。
- [ ] **Step 5: 验证 upgrade→downgrade→upgrade；迁移前 fixture 可读且冻结载荷哈希不变。**
- [ ] **Step 6: 提交并推送 `feat(enterprise): add enterprise and analysis cycle identity`；远端 CI 绿后进入下一任务。**

### Task 6：实现 deny-by-default RBAC 与追加式审计

**Files:**
- Create: `services/api/src/flow_api/security/principal.py`
- Create: `services/api/src/flow_api/security/authorization.py`
- Create: `services/api/src/flow_api/security/audit.py`
- Modify: `services/api/src/flow_api/api/auth.py`
- Modify: `services/api/src/flow_api/settings.py`
- Create: `services/api/migrations/versions/0026_security_audit.py`
- Create: `services/api/src/flow_api/security/route_policy.py`
- Modify: `services/api/src/flow_api/api/routes/intake.py`
- Modify: `services/api/src/flow_api/api/routes/investigations.py`
- Modify: `services/api/src/flow_api/api/routes/metric_library.py`
- Modify: `services/api/src/flow_api/api/routes/publishing.py`
- Modify: `services/api/src/flow_api/api/routes/objective_reports.py`
- Modify: `services/api/src/flow_api/api/routes/statements.py`
- Modify: `services/api/src/flow_api/api/routes/operations.py`
- Test: `services/api/tests/security/test_authorization.py`
- Test: `services/api/tests/integration/test_security_schema.py`
- Test: `services/api/tests/api/test_auth_boundary.py`

- [ ] **Step 1: 子规格先冻结 credential→Principal 解析、全部敏感 route→action/resource 映射及旧 Bearer 兼容期限；用 OpenAPI/路由扫描守护测试保证新增 freeze/publish/approve/review/mutate 路由未登记即失败。**
- [ ] **Step 2: 写逐入口 API 端到端测试**：intake 提交、Finding/证据审批、规则审批，以及 publishing、objective_reports、statements、operations 中每个冻结/发布入口分别覆盖 401、跨企业/跨角色 403、合法 allow 和审计事件；旧 bearer 不得绕过任一发布路径。
- [ ] **Step 3: 实现纯函数 `authorize` 和集中 FastAPI dependency `require_action(action, resource_loader)`；没有明确 allow 即拒绝，路由不得散落角色字符串。**
- [ ] **Step 4: 保留 development principal；非 development 环境缺身份配置时启动失败。**
- [ ] **Step 5: 0026 新增角色绑定和 AuditEvent；保存事件类型、actor/role、enterprise、resource、decision、reason、correlation、模型边界和时间。用数据库 trigger 拒绝 UPDATE/DELETE，并以直接 SQL 测试证明不可变；敏感输入只记哈希/摘要。**
- [ ] **Step 6: 运行 `cd services/api && uv run pytest tests/security tests/api/test_auth_boundary.py tests/integration/test_security_schema.py -v`。**
- [ ] **Step 7: 提交并推送 `feat(security): enforce scoped RBAC and append-only audit`；远端 CI 绿后进入下一任务。**

### Task 7：建立模块边界 API 和兼容层

**Files:**
- Create: `services/api/src/flow_api/modules/shared_core/__init__.py`
- Create: `services/api/src/flow_api/modules/public_analysis/__init__.py`
- Create: `services/api/src/flow_api/modules/internal_workbench/__init__.py`
- Create: `services/api/src/flow_api/modules/registry.py`
- Create: `services/api/src/flow_api/api/routes/modules.py`
- Create: `config/modules/ownership_v1.yaml`
- Modify: `services/api/src/flow_api/api/router.py`
- Test: `services/api/tests/api/test_module_boundaries.py`
- Test: `services/api/tests/architecture/test_module_imports.py`

- [ ] **Step 1: 写失败测试**：`GET /api/v1/modules` 仅返回 public_analysis、internal_workbench、professional_governance 及可见状态，不返回旧双轨为当前模块。
- [ ] **Step 2: 创建三个非空 facade 包和 ownership manifest，把现有 routes、statements、operations、workbench、publishing、intake、metrics、investigation 等相关包恰好归入 public/internal/shared/governance。**
- [ ] **Step 3: 测试要求 manifest 模块集合非空、所有纳管文件恰好归属一次、文件存在；AST 检查对每个 import 的源文件与目标模块都通过 ownership manifest 求 owner，再禁止 public↔internal、允许 shared。加入一个位于原路径的跨 owner 导入 fixture，证明不是只扫描 facade 包。**
- [ ] **Step 4: 实现只读 registry；不从路线图读取运行状态。**
- [ ] **Step 5: 保留现有 statements/operations/workbench 等路由；新前缀先提供能力发现，不搬迁业务数据。**
- [ ] **Step 6: 运行目标测试和 `tests/api` 全量回归。**
- [ ] **Step 7: 提交并推送 `refactor(api): expose explicit product module boundaries`；远端 CI 绿后进入下一任务。**

### Task 8：建立两模块前端入口并替换旧导航语义

**Files:**
- Create: `apps/web/app/public/page.tsx`
- Create: `apps/web/app/internal/page.tsx`
- Create: `apps/web/components/modules/module-landing.tsx`
- Modify: `apps/web/components/dashboard/workflow-nav.tsx`
- Modify: `apps/web/e2e/navigation.spec.ts`
- Test: `apps/web/tests/components/workflow-nav.test.tsx`
- Test: `apps/web/e2e/module-boundaries.spec.ts`

- [ ] **Step 1: 写失败测试**：导航出现企业内部分析工作台、公开财报分析、专业治理，不再把旧双轨当当前结构。
- [ ] **Step 2: 将 `/public`、`/internal` 加入导航守护清单；两页必须包裹 AppShell，登录页仍是唯一例外。**
- [ ] **Step 3: 入口页只显示职责、implemented 与 designed/gated；不得用可操作按钮暗示未实现能力。**
- [ ] **Step 4: 旧页面归入兼容分组，不删除任何既有路由。**
- [ ] **Step 5: 运行 web test、typecheck、lint 及两个 Playwright 规格。**
- [ ] **Step 6: 提交并推送 `feat(web): add explicit public and internal module entrypoints`；远端 CI 绿后进入下一任务。**

### Task 9：生成契约并执行全链回归

**Files:**
- Modify (generated): `packages/contracts/openapi.json`
- Modify (generated): `packages/contracts/src/schema.d.ts`
- Modify: `docs/architecture/flow-v1-domain-objects.md`
- Create: `docs/60_delivery/YYYY-MM-DD-post-u8-boundary-gate-verification.md`

- [ ] **Step 1: 运行 `make contracts && make contracts-check`，禁止手改生成文件。**
- [ ] **Step 2: 运行 `make infra-up`，再运行 `make test-api && make test-web && make lint && make typecheck`；数据库集成测试与迁移检查复用该显式基础设施。**
- [ ] **Step 3: 运行 `make test-user-closure-e2e && make test-statements-e2e`，证明旧入口无回归。**
- [ ] **Step 4: 在已启动 PostgreSQL 上运行 `cd services/api && uv run python ../../scripts/check_migrations.py && uv run pytest tests/integration/test_enterprise_cycle_schema.py tests/integration/test_security_schema.py tests/integration/test_migrations.py -v`，确认唯一 head 为 0026 且迁移往返测试通过。**
- [ ] **Step 5: 在隔离环境严格执行“恢复旧基线→验证→升级→再验证”**：先运行 `FLOW_U8_BASE_URL=https://<验收域名> FLOW_U8_BACKUP_PATH=<冻结备份> FLOW_U8_RESTORE_DATABASE_URL=<隔离库> bash scripts/accept_u8_production.sh restore-u8-baseline`，确认 0024、关键表和旧 frozen payload 哈希；再运行 `cd services/api && DATABASE_URL=<隔离库> uv run alembic upgrade head`，最后重跑 enterprise/cycle/security schema、AuditEvent UPDATE/DELETE trigger 和 HTTPS 健康测试。两段证据分别记录，任何 skip/不一致均失败。**
- [ ] **Step 6: 更新领域对象和交付记录，只登记已验证能力。**
- [ ] **Step 7: 提交 `docs(delivery): verify post-U8 boundary foundation` 并推送。**

### Task 10：裁决旧工作包并关闭阶段 1

**Files:**
- Modify: `docs/50_plans/work_items/U09-O05--authorized-internal-pilot.md`
- Modify: `docs/50_plans/work_items/U10--v1-1-evidence-decision.md`
- Modify: `docs/50_plans/work_items/S01--post-u8-boundary-contract-security.md`
- Modify: `docs/50_plans/CURRENT_ROADMAP.md`
- Modify: `docs/00_start_here/PROJECT_STATE.md`
- Modify: `docs/20_product/CAPABILITY_MAP.md`
- Modify: `docs/50_plans/views/active.md`
- Modify: `docs/50_plans/views/blocked.md`
- Modify: `docs/50_plans/views/completed.md`
- Create: `docs/50_plans/views/public-c-exit-backlog.md`
- Create: `docs/50_plans/views/internal-workbench-backlog.md`

- [ ] **Step 1: 将旧 U9/O5、U10 每项分类为保留重命名、拆入公开 C、拆入内部工作台或取消，并记录证据继承与失效假设。**
- [ ] **Step 2: 只创建两个不可领取的 backlog placeholder**：记录后续须另行批准的规格任务、依赖和 §14 验收引用；状态均为 gated，不创建 active 代码任务，不在本阶段撰写实现规格。
- [ ] **Step 3: 使用 Task 1 已纳入文档门禁的计划视图生成器；本 Task 的每次状态变更都必须同批运行 `python3 scripts/documentation/plan_views.py --write && python3 scripts/documentation/plan_views.py --check`。**
- [ ] **Step 4: 核验退出清单**：U8 可恢复；三规格 approved；V1/V2 通过；企业周期可持久化；拒绝矩阵/不可自批/AI 无发布权通过；审计追加不改；模块入口明确；旧任务已裁决；无第二路线图。
- [ ] **Step 5: 只有全部有证据时把 S01 改 completed；公开 C 与内部工作台均继续 gated，待各自规格和实施计划另行批准后，才可在 CURRENT_ROADMAP 中改变状态。**
- [ ] **Step 6: 运行视图生成器，再运行 `python3 scripts/documentation/kb_manifest.py --write && make docs-check && git diff --check`。**
- [ ] **Step 7: 提交 `docs(roadmap): close post-U8 strategic boundary gate` 并推送。**

## 完成定义

完成本计划只证明 U8 基线已冻结、三层两模块边界可执行、V2 事实上下文和安全治理底座已建立。它不证明公开模块达到 C 级、双 AI 报告达到质量门槛、内部工作台可用，或真实企业三周期/20% 工时门槛通过。后续计划必须分别引用战略设计 §14.1/§14.2。
