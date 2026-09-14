---
doc_id: FLOW-REVIEW-SEC-SPEC-V11-GLM-001
title: 安全规格 V1.1 独立复审意见（GLM 5.3）
doc_type: review
status: open
version: 1.0
created_at: 2026-09-13
updated_at: 2026-09-13
last_reviewed_at: 2026-09-13
owner: FLOW
subject_ref: FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053, D054]
applies_to: services/api
supersedes: []
superseded_by: null
source_refs: [docs/40_specs/security/internal-workbench-rbac-audit-v1.md, docs/40_specs/security/route-inventory-v1.tsv]
related_code: [services/api/src/flow_api/api/router.py]
commit_refs: [ed62a74]
evidence_refs: []
findings: []
confidentiality: project-internal
---

# 安全规格 V1.1 独立复审意见（GLM 5.3）

复审对象：集成检查点 `ed62a74` 的 `FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1` V1.1（`review` 状态）与 `route-inventory-v1.tsv`。
复审方法：规格自带验收标准逐条比对 + 程序化双向核验（`app.openapi()` 强制展开实际挂载，规避 `_IncludedRouter` 懒挂载盲区）+ ABI 数据类逐字段比对。

## 一、核验结果（P1/P2：零阻断）

### 1. 路由清单双向核验（§11.3）——PASS

- 实际挂载（`app.openapi()` 展开）：**64**；TSV 行数：**64**；双向差集：**0**。
- 方法论备注：`app.routes` 顶层迭代在新版 FastAPI 下只见 `_IncludedRouter` 懒挂载对象，**路由清单生成与任何核验脚本必须使用 `app.openapi()` 展开**，不得迭代 `app.routes`（本复审初探即因此误报 64 条 GHOST，已更正方法）。
- 隐藏写 GET 抽查全部合格：`GET /statements/{id}/objective-snapshot` 与 `/objective-snapshot/html` 均如实登记为 `database_write:idempotent_*`；download 登记对象读+哈希校验；projection 登记进程内投影。无"以 GET 名义掩写"残留。

### 2. 发布 ABI 四阶段与冻结数据类——PASS

- `AuditContext`（actor_id/role/enterprise_id/correlation_id/action/resource_type/resource_id/model_boundary）与 `PreparedPublication`（publication_id/idempotency_key/resource_type/resource_id/enterprise_id/source_payload_sha256）字段完整、frozen；
- 四签名 `prepare_intent / execute_object / finalize_success / finalize_failure` 齐备；
- §"finalize + caller commit" 时序精确：intent durable 先于 store/renderer、仅全成功置 published、failure outcome durable 后才返回原失败、route 显式 commit——与 §11.6 断言一一对应。

### 3. 范围与验收标准——PASS

- §11 最低断言九项覆盖：角色×动作全笛卡尔积、identity/legacy 截止、隐藏写/ copilot/orchestration 登记、401/403/allow 审计独立 durable、AuditEvent 不可变与 365 天保留、发布时序与故障注入、object if-absent/同 key 异内容、0025→0026 往返、correlation 五处一致；
- §12 批准记录如实反映「review 等待复审 + 用户重新批准」的状态纪律。

## 二、P3 观察（不阻断，供 2B 重做与后续吸收）

1. **owner 命名一致性（P3）**：publishing/operations 六行 `owner=publication-transaction`，与计划文本「登记 owner=Sol」措辞不一致（语义正确：action owner 是发布事务 ABI）。建议 2B 重做时统一为 `sol-pending-serial-wiring` 或增设 `pending_wiring: true` 列，避免合并后归属歧义。
2. **清单生成方法论（P3）**：TSV 头注明"按最终 api_router 实际挂载生成"——落地为脚本时必须走 `app.openapi()`（理由同 §1 方法论备注）；建议把本复审的探针脚本收编为 2B 的红灯测试。

## 三、两项待裁决的答复

1. **`GET /api/v1/modules` 公开豁免——同意公开豁免**（`exemption_reason: read_only_static_approved_module_fixture_no_business_data`）。依据：返回体为设计 §5.4 批准的静态同字节 fixture，无业务数据；前端公开模块落地页必须可用（公开财报分析模块属于公开范围）。附加条件：registry 后续接入运行时状态时须重审该豁免。
2. **`tests/security/` 纳入 ownership manifest——同意纳入**。依据：安全测试是治理资产，无 owner 漂移风险高；owner 镜像实现车道（principal/authorization/audit/models 测试=Sol，route_policy 测试=Kimi）。建议 Task 4 的 ownership 覆盖检查同步扩展到 `tests/security/**`（本车道 Task 4 交付的 `tests/architecture/test_module_imports.py` 已含 manifest 覆盖断言框架，扩展为行级改动）。

## 四、清零结论

- P1：0；P2：0；P3：2（均为命名/方法论观察，不阻断规格转 `approved`）。
- 复审意见已全部给出，无未决问题。规格可提交用户重新批准；批准后 Task 6 门禁恢复。

## 五、复审者声明

本复审为独立只读审查（worktree 检出于 `ed62a74`），未修改集成分支任何文件；双向核验脚本与输出已留存（`/tmp/review_bidir.txt` 摘录于 §1）。
