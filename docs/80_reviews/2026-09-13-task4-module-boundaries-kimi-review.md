---
doc_id: FLOW-REVIEW-S01-TASK4-KIMI-001
title: Task 4 模块边界后端分支只读审查（Kimi，按计划并行审查职责）
doc_type: review
status: open
version: 1.0
created_at: 2026-09-13
updated_at: 2026-09-13
last_reviewed_at: 2026-09-13
owner: FLOW
subject_ref: FLOW-WI-S01
findings: [F1-modules-route-auth-boundary, F2-ownership-test-coverage, F3-timing-gate]
applies_to: s01-parallel-execution
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053, D054]
supersedes: []
superseded_by: null
source_refs:
  - docs/superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md
related_code:
  - services/api/src/flow_api/modules/registry.py
  - services/api/src/flow_api/api/routes/modules.py
  - config/modules/ownership_v1.yaml
commit_refs: ["4a47917", "4beae65"]
evidence_refs: []
confidentiality: project-internal
---

# Task 4 模块边界后端分支只读审查

审查对象：`codex/s01-module-boundaries` @ `4beae65`（base `b8a3edd`）
审查人：Kimi K3（按三智能体计划 Task 4「并行只读审查：Kimi 复核路由 inventory/ownership 是否漏项」）
审查方式：独立 worktree 只读检出，运行目标测试，逐文件读 diff；不修改 GLM 分支。

## 结论

**通过主体审查，可作为候选持有；三项发现需在合并前处理（F1 需主协调者裁决）。**

## 已验证通过项

1. 目标测试 7/7 绿：`tests/api/test_module_boundaries.py` + `tests/architecture/test_module_imports.py`（独立 worktree 实跑，2026-09-13 22:45）。
2. registry 合同 fixture 与设计 §5.4 一致：三模块（public_analysis=implemented、internal_workbench=designed、professional_governance=governance/designed），shared_core 不出现在产品可见列表。
3. AST 守护三条规则（public↔internal 禁互相导入、产品模块只经 registry 访问 shared_core、shared_core 不导入产品模块）实现正确，且含 ownership 覆盖检查（纳管目录每文件恰好登记一次，未合并文件自动跳过——处理 Task 6 未落地文件的正确方式）。
4. ownership_v1.yaml 预登记 Task 6 安全文件（Sol=security core×5、Kimi=route_policy），与三智能体计划所有权一致。
5. `packages/contracts/openapi.json` 与 `schema.d.ts` 为重新生成（非手改痕迹），改动仅限于新增 /api/v1/modules。
6. 白名单零越界：12 个文件全部在计划 Task 4 清单内（`.gitignore` +1 行 `packages/contracts/node_modules` 属合理工程卫生）。

## 发现

### F1（需裁决）：`GET /api/v1/modules` 未挂认证边界

`router.py` 中 `api_router.include_router(modules_router)` 无 `dependencies=[Depends(require_bearer_auth)]`，是全 API 唯一无认证边界的业务路由。

- 若设计意图是「公开产品模块清单」（与 `/public` 页面公开语义一致）——可接受，但必须在安全规格 V1.1 的 route inventory（`route-inventory-v1.tsv`）中显式登记为公开豁免条目；当前 TSV（64 条，基于 Task 6 前挂载）不含此路由。
- 若非意图——属认证边界漏洞，必须挂 auth。
- 处置建议：合并 GLM 分支时由 route policy 实现者（Kimi，按 ownership）在 TSV 与注册表中补登记；公开/需认证二选一由主协调者裁决。

### F2（低）：ownership manifest 未覆盖 Task 6 测试文件

AST 覆盖检查的 `managed_dirs` 仅含 `modules/` 与 `src/flow_api/security/`，不含 `services/api/tests/security/`。计划 Task 4 Step 4 表述为「覆盖 Task 6 新增 security 文件」，src 文件已预登记，测试文件是否纳入 ownership 未明确。建议：显式声明测试文件豁免，或将 `tests/security/` 加入纳管目录。二选一，不留模糊。

### F3（提示）：交付时序越过波次门禁

计划 Task 4 Step 1 要求「从 Task 6 CI 绿色的 integration SHA 创建分支」，本分支基于 `b8a3edd`（Gate 0 基线，Task 6 未关闭）。GLM 自己的交付清单（GLM-S01-DELIVERY.md §二）曾登记 Task 4 阻塞；22:39 推送说明阻塞被某种方式解除，但仓库中未见解除记录。**请 GLM 或前协调者补充解除依据**；在此之前本分支保持候选状态，不进入合并序列。

### F4（集成提示，非缺陷）

本分支新增 `GET /api/v1/modules` 后，任何 route policy 全路由扫描实现都会因「未登记路由」报红——这是集成期预期红灯，需在 Task 6 重做时同步登记，不作为 GLM 的返工项。

## 行动项

| # | 行动 | 责任方 | 门禁 |
|---|---|---|---|
| 1 | F1 裁决：/api/v1/modules 公开 or 认证 | 主协调者（Kimi 接任后） | 合并前 |
| 2 | F1/F4 落地：TSV + route policy 补登记 modules 路由 | Kimi（Task 6 重做时） | Task 6 |
| 3 | F2 裁决：测试文件是否纳入 ownership | 主协调者 | 合并前 |
| 4 | F3：补充门禁解除依据 | GLM / 前协调者 | 合并前 |
| 5 | module-ui 分支两项已知修复（Make 目标跑错脚本、旧导航归兼容分组） | GLM | Task 5 集成前 |
