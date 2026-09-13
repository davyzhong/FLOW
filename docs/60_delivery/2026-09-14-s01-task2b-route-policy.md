---
doc_id: FLOW-DELIVERY-S01-TASK2B-ROUTE-POLICY-001
title: S01 Task 2B 路由策略（route policy）交付记录
doc_type: delivery
status: verified
version: 1.0
created_at: 2026-09-14
updated_at: 2026-09-14
last_reviewed_at: 2026-09-14
owner: FLOW
applies_to: services/api
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: []
supersedes: []
superseded_by: null
source_refs: [docs/40_specs/security/internal-workbench-rbac-audit-v1.md, docs/40_specs/security/route-inventory-v1.tsv, docs/80_reviews/2026-09-13-security-spec-v11-glm-review.md]
related_code: [services/api/src/flow_api/security/route_policy.py, services/api/tests/security/test_route_policy.py]
commit_refs: [997c1ab]
evidence_refs: []
confidentiality: project-internal
---

# S01 Task 2B 路由策略交付记录

## 结论

Task 2B（route policy）按已批准的安全规格 V1.1 重做完成：分支 `codex/s01-route-policy-v2`，提交 `997c1ab`，已推送待 GLM 5.3 复审。`tests/security` 40 项全绿，`ruff` 与 `mypy --strict` 零告警。

## 交付物

| 交付物 | 路径 | 说明 |
|---|---|---|
| 策略注册表与执行依赖 | `services/api/src/flow_api/security/route_policy.py`（约 760 行） | TSV 装载 + fail-fast 校验、28 个 resource loader、`require_action` 依赖、openapi 双向扫描 |
| 安全测试 | `services/api/tests/security/test_route_policy.py` | 40 项：校验阻断、双向扫描、审计 durable、blocked、精确组合、跨企业拒绝 |
| 清单补行 | `docs/40_specs/security/route-inventory-v1.tsv` | 第 65 行 `GET /api/v1/modules`（公开豁免裁决落账） |

## 关键机制与规格条款对应

- **装载校验（§5 合并阻断项）**：重复 method/path、未知 Action/loader、写副作用缺 action、写副作用被标只读豁免、只读入口缺豁免理由、blocked 缺 action——任一命中即 `PolicyValidationError` fail-fast。
- **exemption_reason 双义性修正**：规格阻断条件是「副作用被标只读豁免」。TSV 中写入口携带的 `request_*_untrusted` / `hard_coded_*` / `four_stage_serial_wiring_required` 是偏差注记而非只读豁免；校验只拒绝 `read_only_` / `anonymous_public_` 前缀家族出现在写入口（`public_module_*` 等是作用域注记，允许）。这是相对初版实现的语义修正，已用全量 TSV 回归验证。
- **require_action 短路序**：未登记 / blocked / action 不符 → 403 且 handler 永不执行（测试用 `handler_called` 探针断言）；loader 抛 `ResourceScopeUnresolved` → 403 `resource_scope_unresolved`；审计写失败 → 503 `audit_unavailable`；allow 路径审计 durable 先于 handler（`_FakeAuditWriter` 时序断言）。
- **审计先于 handler**：body loader 的 body 由 `require_action` 预读进 `request.state.policy_body`，保证 §6「durable 前不 mutation」；loader 保持同步签名（§5）。
- **openapi() 探针（GLM P3 ①已吸收）**：双向扫描走 `app.openapi()` 强制展开 `_IncludedRouter` 懒挂载，收编为常驻红灯测试 `test_openapi_probe_matches_tsv_two_way`（当前 64 挂载 = 64 已登记挂载 + 1 条 PENDING_MOUNT）。
- **`/api/v1/modules` 行（GLM 指令）**：TSV 第 65 行已补（`load_public_module_catalog`，公开豁免 `read_only_static_module_catalog_fixture_no_business_data`，owner=module-boundaries）。因该路由随 `codex/s01-module-boundaries` 合并才挂载，引入 `PENDING_MOUNT_ROUTES` 白名单使双向核验在合并前保持绿色；`test_pending_mount_is_exactly_modules_route` 防漂移——挂载落地后必须移除白名单条目，否则测试变红。
- **GLM P3 ②（owner 措辞）**：TSV owner 列维持原值未动，待 GLM 在 2B 合并时统一为 `sol-pending-serial-wiring`（避免我在执行分支上单方面改写他人车道登记）。

## 依赖注入边界（单符号点）

- `PRINCIPAL_DEP`：当前指向 `_principal_unwired`（503 `principal_resolution_unavailable`），等 Task 2A 后半段 `auth.resolve_principal` + RoleBinding 接线，集成时只换这一个符号。
- `get_readonly_session`：autoflush 关闭的只读会话工厂。
- `get_audit_writer`：默认 `_UnwiredAuditWriter`（抛 `AuditUnavailable`），0026 车道经 `register_audit_writer` 注册真实实现。
- 测试全部经 `app.dependency_overrides` 覆盖上述三点，不触碰全局状态。

## 范围检查

- 本分支**未接线任何路由文件**：现有 `tests/api` 套件在 blocked 路由 + principal 未接线状态下会大面积变红，接线留到 0026 落地后的集成期（与合并顺序 2A→2B→发布接线一致）。
- 规格 §11 验收命令中的 `test_principal_resolution.py`、`test_audit_atomicity.py` 属 Task 2A 后半段（Mavis 车道），不在本交付范围。
- 改动文件恰为 3 个（route_policy.py、test_route_policy.py、TSV +1 行），无范围外文件。

## 残余风险（需复审者知悉）

1. **`load_finding_evidence_batch_scope_or_deny_legacy` 映射到按 finding_id 解析**：evidence decision 路由同时携带 `finding_id` 与 `evidence_id`，scope 解析走 finding 血缘（finding → metric_snapshot → batch → enterprise）；evidence 与 finding 的从属一致性由 handler 既有 409 identity-mismatch 逻辑保证。若复审认为需要在 loader 层校验 evidence→finding 归属，是行级增强。
2. **body loader 字段名已核对真实 schema**：`explain-mapping` 用 `import_version_id`（`MappingExplanationRequest`）、`report-outline` 用 `batch_id`（`ReportOutlineRequest`）、publishing freeze 用 `metric_snapshot_id`（`api/schemas/publishing.py:38`）——与 TSV loader 名推断一致，无偏差。
3. **`PENDING_MOUNT_ROUTES` 是规格外的执行期机制**：双向零差集在合并窗口内对单条已裁决路由豁免。若协调者不接受该机制，备选方案是把第 65 行移到 module-boundaries 合并提交里（但那样 task6 双向核验在窗口期变红）。

## 给协调者的验收路径

```bash
git fetch origin codex/s01-route-policy-v2
git worktree add .worktrees/review-task2b codex/s01-route-policy-v2
cd .worktrees/review-task2b/services/api
ln -sfn /Users/qiming/workspace/FLOW/services/api/.venv .venv
uv run pytest tests/security -q        # 期望 40 passed
uv run ruff check src/flow_api/security tests/security
uv run mypy src/flow_api/security
```

合并前请确认：① module-boundaries 与本分支的合并顺序（影响 `PENDING_MOUNT_ROUTES` 移除时点）；② TSV owner 措辞统一（P3 ②）是否在本次合并一并处理。
