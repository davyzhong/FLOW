---
doc_id: FLOW-OPS-S01-GLM-CORRECTION-20260914
title: GLM 5.3 模块、验收与协调车道修正说明（2026-09-14）
doc_type: operations
status: active
version: 1.0
created_at: 2026-09-14
updated_at: 2026-09-14
owner: FLOW
applies_to: s01-module-verification-coordination-lane
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053, D054]
supersedes: []
superseded_by: null
source_refs:
  - docs/80_reviews/2026-09-14-s01-multi-agent-overall-review.md
  - docs/40_specs/platform/module-boundaries-v1.md
related_code:
  - services/api/src/flow_api/modules/
  - apps/web/components/modules/
  - scripts/verify_s01_upgrade_from_u8.sh
commit_refs: ["9799485", "4a47917", "a4051ea", "61ed5fc", "df11b44", "9cfec8b"]
evidence_refs: []
confidentiality: project-internal
---

# GLM 5.3 模块、验收与协调车道修正说明

## 当前裁决

- module-ui `9799485` 功能可保留，但已被提前并入 main；不得宣称 Task 8/Wave 2 完成。
- module-boundaries 与 full-verification 同指 `a4051ea` 且基于旧 Gate 0，现已被直接并入 main；视为已继承底稿，不能按完成验收。
- Library、视觉改版、DuPont 与 P5 Statements 均已进入 main；S01 修复期冻结不改，后续分别单列产品工作包。
- 立即停止在现有 module-boundaries/full-verification 分支叠加；当前 main/integration 的既有 CI 虽绿，但门禁不完整，修复期间不再推送业务合并。

## module-boundaries-v2

Task 6 同 SHA 全 CI 绿色后再新建分支：

1. ownership manifest 使用产品模块/path-glob owner；执行者姓名放 maintainer，不作为架构 owner。
2. 覆盖所有纳管原路径，验证声明文件存在、恰好一次、无 duplicate/unowned。
3. AST 对每个 import 解析 source owner 与 target owner，执行跨模块规则；加入真实原路径违规 fixture，不只扫描三个空 facade。
4. 覆盖现有 statements、operations、security、routes 等指定树；测试文件是否纳管需在 manifest 中明确，而非隐含跳过。
5. registry 使用类型化 Pydantic response；`ModuleStatus` 固定 `implemented/designed/gated` 三态，facade 不能只靠空文件假装边界。
6. `/api/v1/modules` 登记 route inventory、action、resource loader 和 owner，并接最终认证/授权；除 health 外不得新增匿名入口。
7. 从最终 FastAPI 重生 OpenAPI 与 schema，不手改生成合同；`.gitignore` 等白名单外工程卫生单独申请工作单。

## module-ui-integration-v2

Task 7 CI 绿色后，从新 SHA 建窄分支。由于 07d82f2/9799485 已是 main 祖先，**不得再次 cherry-pick**；只补以下差异。只有协调者明确选择 9799485 之前的恢复基线时，才另行授权迁移旧提交：

- 补 `/internal#governance` 的真实锚点与测试；
- ModuleDescriptor 支持 `gated`；
- 保留 AppShell、三入口、旧路由兼容分组和无虚假按钮；
- 协调者将导航 Vitest、architecture test、module-boundaries E2E 接入 required CI，再取得 Wave 2 SHA。

## full-verification-v2

只从 Wave 2 green SHA 开始，只修改 Task 9 白名单：

1. 每次运行使用唯一 compose project、volume 和动态 HTTPS 端口；完整 trap 清理并保留原退出码。
2. 使用真实 CA `--cacert`，禁止以 `-k` 充当 HTTPS 验证。
3. 恢复 U8 dump 后先核验旧载荷和恢复库唯一 sentinel，再在同一库升级到最终 head。
4. 运行 0025/0026/后续安全 schema、RoleBinding、AuditEvent UPDATE/DELETE trigger 与迁移往返。
5. 冻结内容完整性与连接绑定分开证明：A）验证 dump SHA，并把恢复出的既有 snapshot `payload_hash` 与基线文档固定期望值逐字节比较；B）在升级前后均可读的明确表/字段注入一次性 marker，升级后由指定 HTTPS 端点返回该 marker，并与同库 SQL 值相等，证明 API 未误连常驻库。
6. 若未来确需“三方 hash”，必须先在规格中固定 canonical payload、API 端点、预期常量和计算算法；不得再用 hash 非空代替相等。
7. 执行计划列出的全链命令，无 skip；从最终 API 重生契约并更新领域对象文档。
8. 测试必须锁定上述语义，不能只检查脚本包含某些字符串。

Task 9 精确 allowlist：`scripts/verify_s01_upgrade_from_u8.sh`、`scripts/tests/test_s01_upgrade_gate.py`、`infra/compose.s01-acceptance.yaml`、`packages/contracts/openapi.json`、`packages/contracts/src/schema.d.ts`、`docs/architecture/flow-v1-domain-objects.md`。其他文件一律停机申请，不得再次把 Task 4 整链带入。

## Library / Statements 独立化

- P5 Statements、Library、视觉改版和 DuPont 已随 main 继承，但在 S01 恢复期冻结不改；后续验证、可复现生成和文案修正建独立工作包。
- GLM/Library owner 只从 `seed_p5_statements.sh` 移除 RoleBinding 副作用；显式 dev identity bootstrap 由 security owner在独立白名单任务实现，GLM 只消费其公开命令。
- 静态站生成使用固定 `SOURCE_DATE_EPOCH`/输入 digest，并加 regenerate-diff 门禁。
- Statements 对 14 份样本做参数化验证；README 将“冻结数据生成、全图表闭合”等超出证据的表述降级。
- Dashboard 外部注册状态必须有仓库可复验证据；仅生成 widget HTML 不等于已注册。

## 协调职责修正

协调者只接受“同一 SHA、规定 job 实际运行且全绿”的 checkpoint。提交标题必须准确反映真实范围；禁止用 delivery/docs 提交夹带大批代码、契约或生成数据。`GLM-S01-DELIVERY.md` 在修复完成前降为 delivery 合法的 `draft`（或由纠正记录取代时标 `superseded`），不能继续充当完成证明。
