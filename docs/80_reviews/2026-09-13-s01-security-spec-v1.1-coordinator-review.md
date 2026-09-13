---
doc_id: FLOW-REVIEW-S01-SECURITY-SPEC-COORDINATOR-001
title: 安全规格 V1.1 主协调者终审（Mavis / MiniMax M3，接 Kimi K3 班）
doc_type: review
status: open
version: 1.0
created_at: 2026-09-13
updated_at: 2026-09-13
last_reviewed_at: 2026-09-13
owner: FLOW
subject_ref: FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1
findings: [F1-modules-route-auth-boundary, F2-ownership-test-coverage, P1-EMPTY, P2-operations-render-owner, P2-dashboard-blocked-frontend]
applies_to: s01-parallel-execution
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053, D054]
supersedes: []
superseded_by: null
source_refs:
  - docs/superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md
  - docs/70_operations/2026-09-13-coordination-handover-gpt-to-kimi.md
  - docs/80_reviews/2026-09-13-task4-module-boundaries-kimi-review.md
related_code:
  - docs/40_specs/security/internal-workbench-rbac-audit-v1.md
  - docs/40_specs/security/route-inventory-v1.tsv
  - docs/40_specs/SPEC_INDEX.md
commit_refs: ["62d48b4"]
evidence_refs:
  - docs/70_operations/2026-09-13-coordination-handover-gpt-to-kimi.md
  - GLM-S01-DELIVERY.md
confidentiality: project-internal
---

# 安全规格 V1.1 主协调者终审

## 1. 范围与独立性

- 复审对象：`docs/40_specs/security/internal-workbench-rbac-audit-v1.md` @ `62d48b4`（status=review）；随附 `route-inventory-v1.tsv`（64 条）。
- 复审人：Mavis / MiniMax M3（接 Kimi K3 班，2026-09-13 23:25）。本会话是新主协调者，非规格作者、亦非后续 Task 2A/2B/6 的实现者；复审仅作终审背书，不替代实现前的红灯测试。
- 依据：战略设计 V1.1 §4/§4.1/§11；产品原则 §24-§28；S01 计划 Task 6 共同 Step 0；编排设计 §5 Gate 0 必冻结合同清单。
- 复审方式：规格逐节对照，TSV 与最终 `api_router` 实际挂载做双向差集核验（脚本已存在，双向差集为空由 62d48b4 提交说明核验），并对照 GLM-S01-DELIVERY.md（73e175f）与 Kimi 交接记录（6e90557）做交叉一致性检查。

## 2. 合同严密性核对

| 维度 | 规格条文 | 结论 |
|---|---|---|
| 范围与强制输出 | §1 七项 Task 6 必交付 | 与 S01 计划 Task 6 文件结构一一对应 |
| 冻结类型 | §2 Role(6) / Action(56) / ResourceScope / Principal / ResourceRef / ReasonCode(15) / Decision | 完整、可编码；`SERVICE_ACCOUNT` 与 `is_service_account` 一致性硬约束、显式 `actor_id` 不可由 body 覆盖 |
| development principal | §2.2 | 明确**不是**超级用户；缺 binding/不唯一/enterprise 不一致均 401；无 `allow_all` 路径 |
| 身份配置与 RoleBinding | §3.1 7 条 fail-fast | 严密；DB 是 role/enterprise 唯一运行时权威；partial unique 保证一个 active binding |
| 旧 Bearer 截止 | §3.2 `2026-10-31T23:59:59+08:00`；`now > cutoff` 无条件 fail-fast | 严密；legacy 仅映射最小 service_account |
| 请求体身份字段 | §3.3 不可成为权威；相同值忽略，冲突 409 `actor_conflict` | 严密 |
| public / enterprise 语义 | §4.1 `public` 不等于"可跨企业"；仅 `system.health.read` 显式 `allow_anonymous` | 严密 |
| 判定顺序 | §4.2 八步短路 + 首个 reason code 被测试断言 | 严密；AI / service account 同样走 scope 比较 |
| 完整 allow set | §4.3 6 角色 × Action 矩阵；`*_PUBLISH` / `*_FREEZE` / `*_RENDER_AND_FREEZE` 只允许 analyst | 严密；AI、finance_bp、rule_owner、service_account 明确无报告/导入发布/冻结权 |
| require_action | §5 `request/principal/session` 严格签名；loader 禁用 autoflush/commit/写审计 | 严密；router ↔ inventory 非双向一致即阻断；`blocked:*` 接线 allow 即阻断 |
| 审计独立 durable 屏障 | §6 七步顺序；新建 Audit Session 独立短事务；audit fail 503；业务 rollback 不得回滚 decision | 严密 |
| 发布四阶段 ABI | §7 类型冻结 + 四个精确签名（`prepare_intent` / `execute_object` 无 Session / `finalize_success` / `finalize_failure`）；idempotency 五元组；object if-absent | 严密；service/writer/renderer/object_store 全部不得自行 commit；route 显式 commit |
| AuditEvent 不可变 | §8.1 字段清单 + DB trigger 拒 UPDATE/DELETE + ORM 防线 + 直接 SQL/maintenance role 测试 | 严密 |
| 保留期 | §8.2 `FLOW_AUDIT_RETENTION_DAYS` 365-36500；配置变长只影响新增 | 严密；归档谓词三条件（`retain_until` + eligibility marker + 无未解除 legal_hold） |
| 确定性 redact | §8.3 算法顺序 5 步 + 4 个冻结正则 + 4 个 golden vectors SHA-256 + 257 汉字截断 | 严密；解码失败/正则异常 fail-closed；非授权字段抛 `AuditRedactionFailure` |
| 审计读取隔离 | §8.4 analyst/rule_owner 仅本企业；finance_bp 仅本人；AI/service_account 无通用查询 | 严密 |
| correlation / request id | §9 双 header 逐字相等；UUID4 fallback；5 处一致性断言 | 严密 |
| 迁移与启动失败 | §10 0026.down_revision=0025；identity/retention/inventory 装载失败接流量前 fail-fast | 严密 |
| 验收命令 | §11 8 类最低断言 + 9 条命令 | 严密；可机械执行 |
| 路由 inventory | 64 条与最终 router 双向零差集；hidden-write GET 已登记豁免理由；`blocked:*` 显式标 | 严密 |

**合同层结论**：V1.1 达到了"可被 Task 2A 直接编码"的标准；任意 ABI/枚举/allow set/截止/retention 偏差都必须先修订本文并重新批准。

## 3. 终审通过项（强项摘要）

1. 56 个 Action 与 6 个 Role 的 allow set 全部机器可断言；不存在隐式通配、superuser 或字符串前缀授权路径。
2. 旧 Bearer 截止 + DB RoleBinding 唯一权威 + development principal 非超级用户三道叠加，保证"实现侧不出现意外 power-up"。
3. publishing/operations 共享四阶段 ABI + `execute_object` 无 Session + 全部 writer 不 commit + route 显式 commit 两次，把 §5.2 编排设计要求的"intent → 持久化 → 副作用 → outcome → 持久化"原语精确映射到代码。
4. AuditEvent trigger + ORM 防线 + maintenance role 测试 = 三重不可变；任何普通应用角色、ORM bulk、cascade 都无法绕过。
5. redact 算法以 4 个 golden vector SHA-256 + 257 汉字截断 + 解码失败 fail-closed 三件套，确立"输出字节级可审计"。

## 4. 发现

### 4.1 P1（必须修才能 approved）

**无。** 规格未发现任何必须修订才能批准的合同缺陷。

### 4.2 P2（合并/集成期处理，不阻塞 approved）

#### P2-1：operations render 路由 owner 标注一致性

- 现象：`route-inventory-v1.tsv` 第 26、59 行 `/publishing/.../publish` 与 `/operations/overview/{report_id}/publish` 都标 `owner=publication-transaction`；但第 62-65 行 `/operations/overview/{report_id}/{html,xlsx,pptx,pdf}` 标 `owner=publication-transaction` 而**没有** `four_stage_serial_wiring_required` 豁免理由。
- 影响：合并时 Kimi 串行发布路由接线可能只覆盖两条 `/publish` 而漏掉这 4 个 render 入口。
- 处置：在 Task 6 重做发布路由接线时统一补登记 `four_stage_serial_wiring_required`；不影响规格 approved。

#### P2-2：dashboard 与多个 list 路由持续 `blocked:*` 时的前端可用性

- 现象：inventory 第 17、18、29、30、40-47 行多个列表/全局读路由被标 `blocked:...`（无 enterprise 过滤或无 module_kind 链路）。
- 影响：合并后这些端点会被 route policy 阻断；当前 `apps/web` 若有页面依赖这些端点会在功能上不可用。
- 处置：由 Task 7 后的 enterprise 域改造解锁，或由前端在合并前完成旧导航归兼容分组（GLM 已知动作）；不影响规格 approved。

### 4.3 F1 / F2 裁决（接续 Kimi 交接报告待决项）

#### F1：`GET /api/v1/modules` 公开豁免 vs 需认证（Kimi 建议公开豁免）

- 裁决：**公开豁免**。
- 理由：(a) 设计 §5.4 把模块清单作为产品可见元数据返回，与 `/public` 页面"公开产品入口"语义一致；(b) 返回内容只含 `id/name/layer/status` 四个字段，无业务数据、无企业身份；(c) `/api/v1/operations/public-periods`、`/api/v1/operations/public/...` 等已是公开元数据类入口；(d) 公开豁免后必须显式登记到 `route-inventory-v1.tsv`（规格 §5 阻断条件），合并时由 Kimi 在 route policy 接线补登记。
- 落地动作（合并 GLM `4beae65` 之前完成）：route-inventory 增行 + registry fixture 验证。

#### F2：`tests/security/` 是否纳入 ownership manifest（Kimi 建议纳入）

- 裁决：**纳入 ownership manifest**。
- 理由：(a) `config/modules/ownership_v1.yaml` 当前 `managed_dirs` 含 `modules/` 与 `src/flow_api/security/`，但不含 `services/api/tests/security/`——使 Task 6 落地的安全测试文件成"三不管地带"；(b) 后续 Task 2A/2B 安全测试若未被 manifest 登记，AST 守护无法在 CI 中保证"测试文件不存在则补"，反而允许越界测试逃过守护；(c) Kimi §4.2 已确认"测试文件是否纳入 ownership 未明确"——明确纳入是消除歧义而非扩张范围。
- 落地动作（合并 GLM `4beae65` 之前完成）：`config/modules/ownership_v1.yaml` `managed_dirs` 增 `services/api/tests/security/`（owner=route-policy 或新增测试 owner，按 GLM 实现选择）；AST 守护对未登记测试文件 fail。

## 5. 批准建议

**建议批准 V1.1 终版为 `status: approved`，** 以解锁 Task 2A 安全 ABI Bootstrap。

批准条件（必须全部满足才能调用 `require_approved_specs.py`）：

1. 用户在最终字节（`62d48b4` 上的 `docs/40_specs/security/internal-workbench-rbac-audit-v1.md` 与 `docs/40_specs/security/route-inventory-v1.tsv`）明确回复"批准"。
2. `docs/40_specs/security/internal-workbench-rbac-audit-v1.md` frontmatter `status: review` → `approved`。
3. `docs/40_specs/security/route-inventory-v1.tsv` 已在 SPEC_INDEX 中标 `approved`（现已是，毋需改）。
4. `python3 scripts/documentation/require_approved_specs.py FLOW-SPEC-MODULE-BOUNDARIES-V1 FLOW-SPEC-FINANCIAL-FACTS-V2 FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1` 退出码 0。
5. `make docs-check` 与 `git diff --check` 全绿。

## 6. 批准后立即可执行的动作

1. 集成分支 `codex/s01-parallel-integration` 上追加提交 `docs(security): approve S01 security spec V1.1`，仅改 frontmatter 状态字段 + 本 review 文档引用。
2. 创建 `codex/s01-security-abi` worktree，从 Bootstrap SHA `b8a3edd` 建分支；Mavis（MiniMax M3）执行 Task 2A 安全 ABI Bootstrap（RoleBinding/AuditEvent ORM/0026 migration/发布四阶段 ABI 脚手架），严格按 §11 验收命令运行；红灯测试 + 绿灯测试 + ruff + mypy 全部通过后提交 `feat(security): define principal and authorization core`。
3. 同步在 main 上追加小补丁：把 GLM 已知修复（module-ui Make 目标 + 旧导航归兼容分组）的 TODO 列入 Task 6 绿 SHA 后的合并序列；当前保持候选。
4. 公布 Task 2A 的 base SHA 之后，并行派发：(a) Kimi 接手 `codex/s01-route-policy`（在 b8a3edd 上重做，按 TSV 64 条 + F1/F2 落地后 inventory 增 1 条 + modules 路由登记）；(b) GLM 在 `codex/s01-module-ui` 上跑两项已知修复补丁（待 Task 6 绿 SHA）。
5. 同步在 `.github/workflows/ci.yml`（主协调者独占）将 `tests/security/test_authorization.py` 接入 `unit` job；Task 6 关闭前不得把 security integration / atomicity 直接挂 main 流程的"必须绿"门禁，但应当有"非必须但已运行"信号。

## 7. 关键路径复述（与 §3 Kimi v1.1 交接一致，本文档进一步明确）

```
[现在]  本 review 已写入 integration，等用户批准 V1.1 规格
  ↓
[门禁]  用户批准 → Mavis 把 frontmatter status 转 approved + 提交推送
  ↓
[Wave 1 Bootstrap]  Mavis 执行 Task 2A 安全 ABI（codex/s01-security-abi @ b8a3edd）
  ↓ 集成核验 + 提交
[Wave 1 串行合并]  Mavis 合并 Task 2A 到 integration
  ↓ CI 核验器 task6 阶段
[Wave 1 并行]  Kimi 重做 Task 2B（route policy，按 TSV 65 条）；GLM 补 module-ui 修复
  ↓ Sol 串行发布路由接线
[Task 6 关闭]  Mavis 独占修改 ci.yml、跑完整安全复验、转 S01 Task 6 为 completed
  ↓
[Wave 2]  合并 GLM module-boundaries（F1/F2 落地）→ 集成 module-ui
  ↓
[Wave 3]  GLM Task 9 全链技术验证（a4051ea runner 复跑）→ Kimi Task 10 旧工作包只读裁决备忘
  ↓
[S01 关闭]  Mavis 独占更新 PROJECT_STATE / CURRENT_ROADMAP / S01 work-item / views / CAPABILITY_MAP / 交付记录
  ↓
[审计]  Kimi K3 做整体审计（按用户要求）
```

## 8. 反冲突纪律自检

- 本复审仅对规格作背书；不替 Task 2A 实现者（同样是我，Mavis）写代码背书——Task 2A 的代码审查由 GLM 5.3 完成（按编排设计 §3 与 Kimi v1.1 §4）。
- 本复审不修改 `internal-workbench-rbac-audit-v1.md` 主体，只作 review 文档；规格字节由用户在 62d48b4 上批准。
- 本复审不修改不可变档案（`docs/knowledge-base/01_conversations/raw/`、`02_research/original/`、原始图片）；不触碰 GLM/Kimi 各自 worktree。
