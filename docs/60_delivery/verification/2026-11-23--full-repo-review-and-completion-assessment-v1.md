---
doc_id: FLOW-VERIFY-FULL-REVIEW-20261123-001
title: 全仓 code review 与完成度评估（2026-11-23）
doc_type: verification
status: draft
version: 1.0
created_at: 2026-11-23
updated_at: 2026-11-23
owner: FLOW
applies_to: repository
commit_refs: "[f22cb93a]"
evidence_refs: "[ruff-src-tests, mypy-227-files, scripts-unittest-171, check-docs-m6, plan-views-check, links-check, verify-workflow-jobs-26, unit-39of43, tests-security-59of60, five-lane-review]"
---

# 全仓 code review 与完成度评估（2026-11-23）

## 结论摘要

基线 `f22cb93a`（较上次同步前进 840 个提交，1471 文件、+43 万行）。工程主体已成型且证据纪律高于均值，但**当前 HEAD 在今天的日历下门禁不再全绿**，且新交付的「真实数据导入」子系统整体游离在 RBAC 与审计合同之外。

静态质量与文档合同可本地复现且全绿；单元与鉴权一致性两处红灯；数据库型集成/E2E/前端构建因本机无 Docker、无 Postgres、无 `node_modules` 而无法复现，48 个 CI run 编号因 `gh` 未认证也无法独立核验——所以「CI 全绿」在本报告中始终是转述，不是证据。

## 我实际跑过的验证

| 命令 | 结果 |
|---|---|
| `ruff check src tests` | PASS |
| `mypy src` | PASS（227 文件） |
| `python -m unittest discover -s scripts/tests` | PASS 171/171 |
| `pytest scripts/tests/test_verify_workflow_jobs.py` | PASS 26/26 |
| `make docs-check`（`check_docs.py --phase m6`） | PASS（358 docs，0 errors） |
| `plan_views.py --check` / `links.py --check` | PASS |
| CI `unit` job 选择集（同 CI 的 no-DB `DATABASE_URL`） | **3 failed / 39 passed / 1 skipped** |
| `pytest tests/security` | **1 failed / 59 passed** |
| `make contracts-check`、`pnpm -r lint/typecheck`、web e2e、integration/e2e/smoke | 未能执行（缺依赖与运行时，非代码结论） |

---

## 发现清单

### P0（阻断，需立即处置）

**1. 时间依赖型门禁已静默失效：`unit` job 今天必红** — 我已直接复现
- 位置：`services/api/tests/api/test_auth_boundary.py:73,77` → `services/api/src/flow_api/main.py:51-58`
- 事实：默认 `flow_legacy_bearer_cutoff = 2026-10-31T15:59:59+00:00`（`settings.py:26`）已过 23 天。测试只要注入 `AUTH_TOKEN` 再 `create_app()` 就触发 `SystemExit(2)`，3 条 legacy 边界测试失败。
- 为什么没人发现：`ci.yml` 只在 `push`/`pull_request` 触发，**没有 `schedule`**（`screenshot.yml` 反而有每日 cron）。2026-11-01 起无任何提交重跑，所以仓库处于「提交时刻绿、当前红」。
- 附带后果：任何按 `.env.example:10` 配了 `AUTH_TOKEN` 的真实部署今天启动即失败。单机默认路径（无 token）只 WARN，不受影响。
- 建议：① 测试显式注入远未来 cutoff（同目录 `tests/security/test_principal_resolution.py:37-38` 已是这个写法，照抄即可）；② 给 `ci.yml` 加每日 `schedule`；③ 把 cutoff 默认值三处重复（`settings.py:26`、`main.py:127`、`security/principal.py:106`）收敛成单一常量。

**2. `importer` 子系统 10 条路由无授权、无审计、无登记** — 我已直接确认
- 位置：`services/api/src/flow_api/api/routes/importer.py:38-176`、`api/router.py:26`、`docs/40_specs/security/route-inventory-v1.tsv`
- 事实：`/api/v1/importer/*` 共 10 条端点，router 级只挂 `Depends(require_bearer_auth)`；handler 签名里**完全没有 Principal**，`flow_api/importer/` 整个模块对 `principal/role/audit` 零引用；TSV 中 `importer` 关键字命中 0 行。
- 后果：任何认证主体（含 `ai_analyst`）都能 `POST /dataset/{id}/publish` 发布治理快照、`DELETE /dataset/{id}` 删数据，且不产生 `authorization_decision` 审计行。S01 退出条件里的「AI 无发布权」只在四阶段 ABI 那条门上成立，导入链是另一扇门。
- 证据：守卫测试本身已经判红——`tests/security/test_route_policy.py:151-159` 断言 96 条挂载 vs 86 条登记；`PENDING_MOUNT_ROUTES` 白名单测试（:162-168）为空，说明这 10 条未走「登记先行」过渡。
- 建议：登记 TSV + 接 `require_action`（发布动作应复用四阶段 ABI 而不是自己 `session.commit()`），并把 `tests/security/` 纳入 CI（见 P1-4）。

### P1（高）

**3. 生产报告 HTML 里归母→总额口径静默回退，标签不变** — 我已直接读码确认
- 位置：`services/api/src/flow_api/statements/objective_report_html.py:271-276`
- 事实：`net_profit = attr_current if attr_current is not None else raw("is.net_profit", ...)`，而标签在 `:317`、`:390`、`:418`、`:485`、`:593` 硬编码「归母净利润」；`:296` 的 `roe = net_profit / bs.equity` 更叠加了「分子随回退漂移、分母恒为含少数股东权益」的口径错配。
- 影响：同一页面在不同报告上，同名标签对应不同口径的实际数值，违反「口径必须显式标注」红线。这是产品链路（发布报告），不只是资料库。
- 建议：回退触发时标签随值切换为「净利润（总额）」，或 payload 带 typed `caliber` 字段供渲染；禁止固定文案。

**4. 最关键的一致性守卫不在任何 CI job 里** — 我已核对 CI 配置
- 位置：`.github/workflows/ci.yml:72`（unit 只跑 `tests/security/test_authorization.py`）、`scripts/integration_test_shards.py:16`（分片 ROOTS 仅 `integration/investigation/copilot/api`）
- 事实：`tests/security/` 其余文件与 `test_route_policy.py` 双向漂移守卫从不被 CI 执行；同目录 `test_principal_resolution.py` 同样不在任何 job 内。
- 影响：P2 的脱钩能长期存在正是因为这条探针不跑。
- 建议：把 `tests/security/`（除需 DB 者）并入 unit job；修红后设为 required check。

**5. 静态资料库把混口径自算均值包装成「行业」结论** — 前一轮已向用户提示，本轮复核扩展
- 位置：`scripts/build_static_library_site.py:1162-1168`（`??` 跨口径回退）、`:1108`、`:1140`（同类回退）、`:1336`（行业领先/平均/末位）、`:1371`、`:1395-1396`（ROE 行业均值）
- 另一生成器：`scripts/rich_report.py:231` `m["roe"] = ratio(m["attr_net_profit"], m["equity"])` —— 分子归母、分母总权益，天然混口径。我已读码确认。
- 影响：5 家异行业样本自算均值称「行业均值」并给出领先/末位判定，同时两类口径公司进同一张 ROE 降序榜。
- 建议：改「样本均值」、删判定措辞、缺归母项返回 null 而非回退；口径标签写进渲染文本。

**6. 多数 e2e/验收脚本默认打到常驻开发库，护栏未泛化** — 我已抽查确认
- 位置：`scripts/test_analysis_invariants.sh:6` + `:14`（`alembic upgrade head`）、`scripts/test_statements_e2e.sh:5` + `:35-36`（迁移 + 写种子）；另 `acceptance.sh:7`、`test_publishing_golden.sh:7`、`test_investigation_e2e.sh:4`、`render_golden.py:39`、`generate_objective_report_pdfs.py:23` 默认库名均为 `/flow`。
- 事实：带常驻库 fail-closed 拦截的只有 `test_user_closure_e2e.sh`、`u8d_acceptance.sh`、`verify_s01_upgrade_from_u8.sh`（加 `test_dashboard.sh`）；CI 全局 env 也写 `/flow`，本地跑即等同操作真实开发库。
- 影响：与 2026-09-27 误写常驻库事故同模式，教训未被泛化为统一守护。
- 建议：抽一个公共 guard（非 CI 且库名为 `flow` 时拒绝执行，显式逃逸变量），或统一默认 `flow_test`。

**7. legacy 冻结身份未按配置生效** — 转述 lane 结论，方向与我读到的代码一致
- 位置：`services/api/src/flow_api/api/auth.py:333-339`
- 事实：legacy token 命中后查询「任意一条」active `service_account` binding，未按 `FLOW_LEGACY_ACTOR_ID/ENTERPRISE_ID` 过滤；这两个字段全仓仅在 `main.py:66` 做存在性检查。多条 binding 时 `session.scalar` 无 `ORDER BY`，返回不确定行。
- 影响：违反规格 §3.2「完全匹配 binding」。仅在启用 legacy token 时暴露，单机默认路径不触发。

### P2（中）

8. **审计写失败的运维可观测性缺口**（`security/audit_writer.py:33-53`、`api/auth.py:59-67`）：fail-closed 语义本身正确（未注册/commit 失败一律 `AuditUnavailable`→503，且有通过的测试），但 `main.py:137-139` 注册时不传 `on_write_failure`，生产 DB 抖动只留 error 日志、计数为零，运维无告警面。
9. **`flow_env` 默认 `development` 是 fail-open 默认值**（`settings.py:14`）：忘设生产环境变量会跳过 identity bindings 启动校验；缓解是 dev principal 还需 `FLOW_DEV_ACTOR_ID` 且该值无默认。建议默认值必填。
10. **append-only 只在 PostgreSQL 成立**（`migrations/versions/0026_security_audit.py:130-154`）：无 `DATABASE_URL` 时回退 SQLite，而单机原型正是 SQLite 栈，因此「审计不可改」在默认交付形态下不成立，需文档明确或加拦截。
11. **前端 DELETE 链路 405**（`apps/web/app/api/v1/[...path]/route.ts:73-83` 只导出 GET/POST/PUT）：我已确认 `lib/api/client.ts:280` 发 DELETE、后端 `importer.py:162` 有 DELETE、UI 上 `components/data/import-wizard.tsx:242` 有可见「删除」按钮、且 `remove()` 无 try/catch。vitest 把 api client 整体 mock 掉，所以单测全绿也发现不了。
12. **详情页 `/investigations/[findingId]` 不在 `navigation.spec.ts` 守护清单**（该页确实包裹了 AppShell）。
13. **视觉统一只达成于 token/JS 层**：`components/cockpit/cockpit.css` 仍有 132 处硬编码 hex、`investigation.css` 52 处，且 `.kpi__sparkline`、`--dupont` 存在重复选择器块（补丁式追加未清理）。
14. **数值格式化三套并存**：共享 `cockpit/number-format.ts` 之外，`investigations-index.tsx:29-35`、`statement-view.ts:39-43`、`kpi-card.tsx:89` 各有本地舍入路径，同一金额跨页可能显示不一致；共享 formatter 归属也错位（放在 `components/cockpit/` 却被 statements 反向 import）。
15. **`holdout_runs/2026-09-29-adapter-v3` 与 `...first-run-v3` 是零引用孤儿产物**。
16. **7 个重要生成器无 CI 覆盖**（含 `build_static_library_site.py`、`rich_report.py`），且 `docs/library/index.html` 已入库但生成器无 `--check` 模式——资料库与代码可静默漂移，杜邦问题正是这样长期潜伏。
17. **治理文档「唯一真相」机制逼近重构阈值**：`PROJECT_STATE.md` 104 行内堆叠约 20 个日期段，其中 `:29`、`:35`、`:47` 仍以现在时写「唯一执行项/唯一队首」，与顶部 `:15` 互斥且未逐段标注失效；`HANDOFF.md:78` 的「队列 18 行 / 暂停 2」与路线图 17 项 / 暂停 1 不一致。派生 `views/` 与登记表状态核对无冲突，所以机制未失效，但可读性已在恶化。

### P3（低 / INFO）

18. 鉴权每请求占 2 条连接（auth session + policy 只读 session）；CI 侧 uvicorn 多 worker 时逼近默认 QueuePool 上限，值得压测。
19. `apps/web/lib/api/session.ts:6` 的会话签名密钥默认字面量 `flow-dev-session-key-1` 兜底，生产忘配即「可伪造已鉴权会话」（单机默认 `AUTH_TOKEN=""` 时不构成漏洞）。
20. 401 审计存 `sha256(Authorization)[:12]`（`auth.py:380`），低熵 token 可离线验证摘要。
21. `redaction.py:24-29` 只脱敏 `authorization/cookie/password/token` 四个键，同语义变体（`accessToken`、`x-api-key`）落原文，建议改子串匹配 + 新增键回归测试。
22. `analysis/objective.py:55-61` 目录经 `Path.cwd()` 上溯解析，工作目录敏感；`analyze()` 不回带 `mapping_version`，事后追溯依赖当前别名表默认值。
23. `dict`/`metric_library` 的 `benchmark` 自由文本（如 quick_ratio「经验参考约 1」）经 `api/routes/metric_library.py:181` 透出，多数无行业绑定，属 C06 边缘。
24. `scripts/audit_visual_language_accessibility.mjs:14` 直接覆写已入库的历史验收工件 `visual-language-20261024/axe-results.json`（HANDOFF ② 已自曝一次还原）。
25. `var/metric_library_audit.jsonl` 于 `5d085b4a` 删除：内容为 189 行 `actor:"seed"` 重复审计噪声，属 gitignore 下的运行时工件、**不在 AGENTS.md 不可变档案路径内**，但提交信息未单列删除理由。
26. 术语订正：本报告早期草稿沿用「C14」指代「无判定措辞」红线，经核 `DECISION_INDEX.md` **无 C14 决策条目**（唯一命中是竞品文件 `docs/knowledge-base/09_competitive/C14-pigment.md`）；该红线应引 D049。

---

## 完成度评估（三把尺子）

| 尺子 | 读数 | 说明 |
|---|---|---|
| 路线图口径 | **12/17 完成 = 71%**（执行中 0、排队 3、暂停 1、外部受限 1） | 逐行数表确认，`CURRENT_ROADMAP.md:20` 宣称与表体一致；队首空转，等用户裁决方向 |
| 战略目标口径 | **3 项里 1 项达成** | G1 单机原型已交付；G3 公开 C 级维持 **No-Go**（完整独立 oracle 0/14、泛化留出全败）；G4 内部月度工作台 gated，未启动 |
| 可复核证据口径 | 12 项完成中我本地硬核到的 **约 8 项**；CI 全绿宣称 **0 项可独立核验** | 抽样 31/31 个被引用 SHA 全部存在且在 main 祖先链上（纪律极好）；但 48 个 CI run 号因 `gh` 未认证无法查证；今天实际复跑结果见上表（unit 与 security 各 1-3 红） |

工程体量快照：20 条 Web 路由、96 条挂载 API 端点（86 条已登记策略）、32 个 PostgreSQL 迁移 + 5 个 SQLite 迁移、182 个 API 测试文件 / 863 个测试函数、20 个 e2e spec / 89 个用例、649 份 Markdown 文档（358 份纳入元合同）、101 份验证工件。

---

## 我剔除的三条「审计发现」（诚实登记）

并行审计给出的结论里有三条我复核后判定不成立，未计入上表：

1. 「`scripts/seed_p5_statements.py` 直接创建 `super_admin` 角色」——该文件不存在（实为 `.sh`），且全仓 grep `super_admin` **零命中**；`seed_dev_principal.py` 只授 `analyst` 与 `service_account`，`.sh` 里还有注释说明 RoleBinding 已单源化。
2. 「`route_policy.py:326` 对 `audit.read` 特殊放行」——全仓 src 零命中 `audit.read`，引用行号处的代码是 `_public_ref()`。
3. 「durable 审计写失败被吞掉、请求照常放行」——与 `audit_writer.py:42-53` 相反（明确 `raise AuditUnavailable`），且有通过的 fail-closed 测试；真实缺口是「无告警回调」，已降级为 P2-8。

## 强项（值得保留的模式）

- 静态与文档门禁可一键本地全绿；`test_verify_workflow_jobs.py` 26 项把 CI job 清单本身也纳入断言，防「CI 悄悄少跑一件事」。
- 审计链路完整：`AuditEvent` 带 `request_id`、`reason_code`、`policy_ref`；`redaction.py:53` 对原文拒绝路径做了「绝不上抛、绝不回退明文」测试；`test_fail_closed_when_nothing_configured` 实测通过。
- 数值正确性纪律：除零/负分母返回 typed 错误（`decimal_math.py:83-88`、`objective.py:184-199`），无静默填 0；字典与引擎有双实现互检（`test_dictionary_execution_parity.py`）；`MetricDefinition` 同码冲突三层守卫（`metrics/models.py:94-121` → DB 唯一约束 → `persistence.py:64-68`）+ 回归测试。
- 红线有真测试而非只有文档：`tests/analysis/test_threshold_and_caliber.py:21-34` 断言经验阈值对象无 `verdict` 字段、措辞禁词、无适用范围即拒输出；`experience_threshold_hint` 目前**零生产调用方**，弱契约处于潜伏态而非在用风险。
- 前端 AppShell 规范真实达成：19 条交互路由在 page.tsx / `workflow-nav.tsx` / `navigation.spec.ts` 三处完全一致，且有「每路由恰 1 链接」计数断言。
- 文档的自我否定勇气：路线图明确写了某些 run 是 `cancelled/failure`、不得描述为全绿；`715a2d6d` run 被并发取消一事如实自曝；C 级 No-Go 至今未被稀释。
- 原始档案红线：`validation/financial_reports/original/` 8 份 PDF 实测 SHA-256 与登记一致，未发现违反不可变档案保护的行为。

## 建议的下一步（按投入产出排序）

1. **S｜修 P0-1**：测试注入远未来 cutoff + `ci.yml` 加 `schedule`。这两步就能让「提交时刻绿」变成「持续绿」。
2. **M｜修 P0-2**：`importer` 10 条路由登记 TSV 并接 `require_action`，发布改走四阶段 ABI；同时把 `tests/security/` 并入 CI。
3. **M｜修 P1-3/P1-5**：口径回退要么禁止、要么随值改标签；资料库删「行业」措辞、改「样本均值」。
4. **S｜修 P1-11**：代理补导出 DELETE，并把该链路加进 e2e（现在被 mock 掩盖）。
5. **M｜统一 DATABASE_URL 护栏**（P1-6），避免再次误写常驻库。
6. **L｜PROJECT_STATE 重构**：历史段落折叠到 `knowledge-base/` 只读侧车，正文只留当前事实；这是继续用这套状态纪律的前提。
7. 队首仍待你裁决：路线图/`HANDOFF:74` 列的 5 个候选里，② 银行流水与余额表交叉核对最贴合已交付链路，① 科目级映射扩展需要先修订「不双源」规则（即先动合同，再动代码）。

## 未覆盖范围

未连库执行 integration/e2e/smoke/perf/l0-baseline；未复现 web lint/typecheck/vitest/Playwright（依赖未安装，按纪律未擅自安装）；未逐项比对运行时口径与静态页是否同源；GitHub 上 CI 实际红绿状态未查证。
