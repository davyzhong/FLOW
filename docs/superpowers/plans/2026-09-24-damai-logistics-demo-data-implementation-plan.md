---
doc_id: FLOW-PLAN-DAMAI-DEMO-20260924
title: 大麦物流全量演示数据发行版实施计划
doc_type: plan
status: active
version: 1.1
created_at: 2026-09-24
updated_at: 2026-09-24
owner: FLOW
depends_on: [FLOW-SPEC-DAMAI-DEMO-001]
acceptance_refs: [FLOW-SPEC-DAMAI-DEMO-001]
applies_to: repository
---

# Damai Logistics Demo Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建并装载 24 个月“大麦物流”跨域合成数据，使 FLOW 当前所有主要页面具备可验证内容。

**Architecture:** 用独立确定性生成包产生 canonical、workbook、statement 和 manifest；复用现有 Intake、Metrics、Analysis、Investigation、Publishing 服务装载派生对象；用静态不变量、数据库 receipt 和 API 页面覆盖三层验证。全程不新增数据库迁移。

**Tech Stack:** Python 3.13、Pydantic、Decimal、openpyxl、SQLAlchemy、FastAPI、pytest、Make、PostgreSQL/MinIO。

---

### Task 1: 冻结大麦公司画像和生成器接口

**Files:**
- Create: `services/api/src/flow_api/fixtures/damai/__init__.py`
- Create: `services/api/src/flow_api/fixtures/damai/profile.py`
- Test: `services/api/tests/fixtures/test_damai_profile.py`

- [ ] 先写失败测试：断言 24 个连续期间、目标规模、业务族权重合计 1、所有实体为 synthetic。
- [ ] 运行 `cd services/api && uv run pytest tests/fixtures/test_damai_profile.py -q`，确认因模块缺失失败。
- [ ] 实现 frozen profile models 和 `DAMAI_PROFILE_V1`，金额及权重只用 Decimal。
- [ ] 重跑测试确认通过，并运行 Ruff/MyPy 定向检查。
- [ ] 提交 `feat(fixtures): define damai logistics demo profile` 并立即 push。

### Task 2: 生成 24 个月 canonical 数据

**Files:**
- Create: `services/api/src/flow_api/fixtures/damai/generator.py`
- Create: `services/api/src/flow_api/fixtures/damai/validation.py`
- Test: `services/api/tests/fixtures/test_damai_generator.py`

- [ ] 先写失败测试覆盖行数、收入区间、业务占比、季节性、经营/财务对账、预算场景、AR 风险事件和确定性。
- [ ] 验证测试因 `build_damai_package` 缺失而失败。
- [ ] 实现主数据与事实生成；使用稳定 UUID5、Decimal 和显式舍入；工作簿只包含 actual/budget。
- [ ] 单独生成 `forecast/rolling_forecast.jsonl`，断言其带版本和 SHA，且 manifest 明确标记
  `persistence: static-only` 和 `page_coverage: excluded`。
- [ ] 实现 `validate_damai_package`，失败返回具体 invariant code。
- [ ] 重跑定向测试、既有 `tests/data_contract tests/fixtures tests/metrics`。
- [ ] 提交 `feat(fixtures): generate damai canonical dataset` 并立即 push。

### Task 3: 生成闭合财务报告

**Files:**
- Create: `services/api/src/flow_api/fixtures/damai/statements.py`
- Test: `services/api/tests/fixtures/test_damai_statements.py`

- [ ] 先写失败测试：FY2025/FY2026 两份报告、收入与 canonical 年度汇总一致、资产恒等式、毛利、净利润归属、现金桥和权益 roll-forward。
- [ ] 验证测试因 `build_damai_statement_payloads` 缺失而失败。
- [ ] 实现四表、权益变动表和附注索引 payload；金额单位统一为人民币千元。
- [ ] 用现有 statement importer/normalization 投影跑兼容性测试，缺失指标保持 unavailable。
- [ ] 断言权益变动表期末权益=资产负债表权益，现金流量表期末现金=资产负债表现金。
- [ ] 重跑定向及 statement tests。
- [ ] 提交 `feat(statements): add damai synthetic financial reports` 并立即 push。

### Task 4: 构建静态发行版

**Files:**
- Create: `services/api/src/flow_api/fixtures/damai/manifest.py`
- Create: `scripts/build_damai_demo.py`
- Create: `scripts/tests/test_build_damai_demo.py`
- Create: `fixtures/damai/README.md`
- Generate: `fixtures/damai/canonical/*.jsonl`
- Generate: `fixtures/damai/workbooks/damai_logistics_full_v1.xlsx`
- Generate: `fixtures/damai/statements/*.yaml`
- Generate: `fixtures/damai/manifest.json`

- [ ] 先写失败测试：临时目录构建两次时 SHA/文本字节一致，manifest 计数和汇总匹配，XLSX 语义指纹一致。
- [ ] 验证测试因构建入口缺失而失败。
- [ ] 实现 build 脚本，复用 `write_canonical_package`、`render_workbook` 和 YAML safe dump。
- [ ] 运行构建，提交生成产物；再次构建后执行 `git diff --exit-code fixtures/damai`。
- [ ] 运行 manifest 验证与 `git diff --check`。
- [ ] 提交 `feat(fixtures): publish damai demo data release` 并立即 push。

### Task 5: 实现幂等数据库装载器

**Files:**
- Create: `services/api/src/flow_api/fixtures/damai/loader.py`
- Create: `scripts/seed_damai_demo.py`
- Test: `services/api/tests/fixtures/test_damai_loader.py`

- [ ] 先写数据库集成失败测试：首次 seed 产生企业/周期/导入/12 快照/分析运行/两个 StatementReport，再次 seed 不重复。
- [ ] 先写授权契约测试：seed 后 `analysis_cycle` 仅有一个 enterprise_id，通过真实 API 依赖调用 dashboard/investigation/publishing 为 200，不触发 `enterprise_scope_missing`。
- [ ] 验证测试因 loader 缺失而失败。
- [ ] 复用固定 bootstrap enterprise UUID，幂等更新为大麦物流；复用 IntakeService 和现有领域服务实现事务化 seed，不得绕过质量/对账。
- [ ] 通过状态机为证据、结论和 Finding 建立混合状态，至少一个 approved Finding 可冻结报告。
- [ ] 每份财报保留非空 source SHA，顺序调用 `normalize_report`、`ReviewService.publish`，验证存储的 normalized rows 和 published 状态后才允许 freeze。
- [ ] 冻结内部报告、客观财报快照和经营概览，输出 JSON receipt。
- [ ] 注入不变量失败、第二份财报失败和 freeze 失败，分别断言事务全回滚；重复 seed 后快照、ReviewEvent、freeze version、source object 数量不增长。
- [ ] 重跑 loader、investigation、publishing、statements 相关测试。
- [ ] 提交 `feat(demo): seed damai cross-domain workflow` 并立即 push。

### Task 6: 生成大麦指标覆盖数据集并接入展示

**Files:**
- Create: `config/metrics/damai_demo_metric_coverage_v1.yaml`
- Modify: `services/api/src/flow_api/api/schemas/metric_library.py`
- Modify: `services/api/src/flow_api/api/routes/metric_library.py`
- Modify: `apps/web/components/metric-library/metric-coverage-section.tsx`
- Test: `services/api/tests/api/test_metric_library.py`
- Test: `apps/web/components/metric-library/metric-coverage-section.test.tsx`

- [ ] 先写失败测试：API 默认继续返回 public，`dataset=damai` 返回独立 synthetic 数据集，非法 dataset 返回类型化 422。
- [ ] 先写前端失败测试：可切换真实/大麦数据集，大麦视图显示“合成演示数据”而不冒充真实披露。
- [ ] 从 statement normalized facts 生成大麦覆盖 YAML，缺失项保留结构化 missing reason。
- [ ] 实现受控 dataset 选择器和前端切换；不改变现有默认响应语义。
- [ ] 运行 API 与 Web 定向测试，提交 `feat(metrics): expose damai synthetic coverage dataset` 并立即 push。

### Task 7: 增加 Make 入口和覆盖验证器

**Files:**
- Create: `scripts/verify_damai_demo.py`
- Create: `scripts/tests/test_verify_damai_demo.py`
- Modify: `Makefile`

- [ ] 先写失败测试：验证器能识别缺批次、缺快照、缺 Finding、缺报告和汇总不符，并返回非零。
- [ ] 验证测试因验证器缺失而失败。
- [ ] 实现 `damai-demo-build/seed/verify/up` 目标；`stack-up` 语义保持不变。
- [ ] 在已启动的隔离数据库执行 seed 两次与 verify，保存 receipt 到 `work/damai-demo/`（不入 git）。
- [ ] 运行相关 shell contract tests 与 `make damai-demo-verify`。
- [ ] 提交 `feat(demo): add damai startup and verification commands` 并立即 push。

### Task 8: 页面级全链验收

**Files:**
- Create: `apps/web/e2e/damai-demo.spec.ts`
- Create: `scripts/test_damai_demo_e2e.sh`
- Modify: `Makefile`

- [ ] 先写 E2E：八个主要页面不处于空数据态，并验证大麦公司名、期间、KPI、Finding、财报、快照与 synthetic 指标覆盖。
- [ ] `/data` 必须从页面上传生成 XLSX，完成映射、校验、warning 确认和发布，断言质量/对账；不得以 seed 后非空代替该旅程。
- [ ] 在未 seed 环境运行，确认测试按预期失败。
- [ ] 接入动态端口、owned supervisor 和 cleanup trap，调用大麦 seed 后运行生产构建 E2E。
- [ ] 修复发现的数据装载或页面契约问题；不得弱化断言或写页面 mock。
- [ ] 运行大麦 E2E、现有 86 个 Web 单测、lint、typecheck。
- [ ] 提交 `test(e2e): verify damai demo across product pages` 并立即 push。

### Task 9: 全量回归、文档刷新与交付

**Files:**
- Modify: `docs/00_start_here/PROJECT_STATE.md`
- Modify: `docs/50_plans/CURRENT_ROADMAP.md`
- Modify: `README.md`
- Modify: `HANDOFF.md`
- Modify: `docs/README.md`
- Modify: `docs/80_reviews/2026-09-24-project-completion-and-damai-data-readiness-review.md`

- [ ] 执行 baseline repair 计划 Task 2，用实测结果更新权威文档。
- [ ] 运行 API unit/integration、Web unit/E2E、contracts、lint、typecheck、docs m6、fixture 零漂移和 U8 相关非破坏回归。
- [ ] 以 `git merge-base origin/main HEAD` 为 base，核对 `git diff --name-only <base>..HEAD`，确认无迁移、`.env`、CI 配置和范围外文件，并断言 Alembic head 与基线一致。
- [ ] 提交 `docs: close damai demo data release` 并立即 push。
- [ ] 先保持工作包 active 并验证实现 head；随后用最终状态提交把工作包改为 completed、push，再验证该最终精确 SHA 的 required jobs。
- [ ] 若最终 SHA 的 CI 失败，以新提交把状态恢复为 active/阻塞，修复并重新验证；不允许用旧 SHA 的绿色结果宣称完成。
