---
doc_id: FLOW-NAV-HANDOFF-20260913-S01
title: 会话交接：S01 战略边界/事实合同/安全门禁进度（2026-09-13）
doc_type: navigation
status: current
version: 1.0
created_at: 2026-09-13
updated_at: 2026-09-13
owner: FLOW
applies_to: handoff
---

# FLOW 会话交接：S01 进度（2026-09-13 19:36）

> 接手者请先读 `docs/knowledge-base/README.md`、`docs/00_start_here/AGENT_START_HERE.md`
> 与 `docs/00_start_here/PROJECT_STATE.md`（仓库硬性规则），再读本文件。
> 本文件为 2026-09-13 晚会话的交接；根目录 `HANDOFF.md` 仍是 2026-09-12 战略重构交接（D052–D054 的 source_refs 指向它，勿覆盖）。

## 1. 当前任务定位

正在执行 **S01 工作包：U8 后战略边界、事实合同与安全门禁**。

- 权威计划：`docs/superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md`（Task 1–10）
- 工作包状态文件：`docs/50_plans/work_items/S01--post-u8-boundary-contract-security.md`
- 唯一执行入口：`docs/50_plans/CURRENT_ROADMAP.md`
- 状态纪律：任务领取/状态只写 ROADMAP 和 S01 work-item，不另建状态真相。

## 2. 已完成（本会话）

| 项 | 提交 | 状态 |
|---|---|---|
| U8 冻结门合入 main（GPT 遗留工作收尾） | 914a473 | CI 16/16 绿，标签 `flow-u8-freeze-20260913`；原始锚 `u8-final-baseline`(079d546) 未动 |
| Task 2：三份实施子规格 + approved-spec 门禁 | 0a8ebab（review）→ 4298f7b（用户批准后 approved） | CI 绿 |
| Task 3：Facts V2 纯领域模型（TDD，27 测试） | 28a551c | CI 绿 |
| Task 4：V1/canonical 显式适配器（TDD，14+16 测试） | 2033db4 | CI 绿 |
| Task 5：企业空间/月度周期 + 迁移 0025（TDD，22+1 测试） | 15c57c6 + f366cc2 | CI 绿（20:31 复核 confirmed） |

三份 approved 子规格（Task 3–8 的共同 Step 0 门禁对象）：

- `docs/40_specs/platform/module-boundaries-v1.md`（FLOW-SPEC-MODULE-BOUNDARIES-V1）
- `docs/40_specs/financial-facts/financial-facts-contract-v2.md`（FLOW-SPEC-FINANCIAL-FACTS-V2）
- `docs/40_specs/security/internal-workbench-rbac-audit-v1.md`（FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1）

门禁用法：`python3 scripts/documentation/require_approved_specs.py`（无参默认验三份规格），
测试在 `scripts/tests/test_require_approved_specs.py`（8 个用例，含一个「真实仓库」活文档测试）。

## 3. 卡住/未决事项

1. ~~Task 5 CI 未确认~~ **已闭环（20:31 复核：f366cc2 CI completed/success）**。
   新未决项：三智能体并行计划（`cb99044`，docs-only，推送时 CI 在跑）+ 主协调者 Task 0
   Gate 0 与 Sol Task 1 Bootstrap 未落地前，Kimi K3 的 Task 2B 不得开工（见 §7）。
2. **RBAC 规格有一处待冻结项**：`internal-workbench-rbac-audit-v1.md` §5 第 5 条——
   旧 Bearer 兼容期限留空（`____`），按三智能体计划由主协调者在 Gate 0 Step 3 冻结。
3. **本地全套集成测试 >5 分钟会超时**：跑子集验证，全套交给 CI。

## 7. 三智能体并行计划下的任务分配（2026-09-13 晚 GPT 推送，cb99044）

- 计划：`docs/superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md`；
  手册：`docs/70_operations/three-agent-parallel-execution-runbook.md` §5.2。
- **Kimi K3（本会话角色）= 跨仓路由与证据负责人**：Task 2B 路由盘点与权限接线
  （route_policy + 7 routes + 6 schemas + 4 测试文件，白名单严格）、Task 4 只读审查、
  Task 6B 旧工作包裁决备忘（只读 review 草案）。
- **开工前置**：主协调者 Task 0（Gate 0：安全规格降 review 修订 ABI 并再批准、
  integration 基线、CI 核验器）+ Sol Task 1（安全 ABI Bootstrap）合并公布 base_sha。
- **预热产物**：只读路由盘点草稿在 `work/s01-route-inventory-draft.md`（gitignored，
  53 端点全表、2 个 GET 隐藏写、6 个 schema 的 actor/operator 伪造面、action 建议）。
  正式 inventory 必须在 `codex/s01-route-policy` 分支对最终 api_router 机器重新生成。

## 4. 下一步计划（按序，每任务远端 CI 绿后才进下一个）

- **Task 6：deny-by-default RBAC + 追加式审计**（最大的一块）。文件与步骤见计划 Task 6：
  - 新建 `services/api/src/flow_api/security/{principal,authorization,audit,route_policy}.py`；
  - 迁移 `0026_security_audit.py`（角色绑定 + AuditEvent + 拒 UPDATE/DELETE trigger）；
  - 改造 intake/investigations/metric_library/publishing/objective_reports/statements/operations
    七个 routes 文件接入集中 `require_action`；
  - 纯函数 `authorize`；非 development 缺身份配置启动失败；保留 development principal；
  - 逐入口端到端测试（401/跨企业/跨角色 403/合法 allow/审计事件），旧 Bearer 不得绕过发布路径；
  - 先冻结 credential→Principal 解析、route→action 映射、旧 Bearer 兼容期限（规格修订）；
  - 提交信息约定：`feat(security): enforce scoped RBAC and append-only audit`。
- **Task 7**：模块边界 API（`GET /api/v1/modules`）+ ownership manifest
  `config/modules/ownership_v1.yaml` + AST 导入方向守护（禁 public↔internal）。
- **Task 8**：前端 `/public`、`/internal` 入口页 + 导航语义替换。
- **Task 9**：生成契约 + 全链回归。
- **Task 10**：裁决旧工作包（U9/O5、U10），关闭阶段 1。

已勘察的 Task 6 现状（省得重查）：

- 现有认证仅 `services/api/src/flow_api/api/auth.py` 的 `require_bearer_auth`
  （单 token，`auth_token` 未配 = 开发模式不鉴权）；
- `api/router.py` 中所有业务 router 以 `Depends(require_bearer_auth)` 挂在 `/api/v1` 下；
- `settings.py`：`flow_env`（默认 development）、`auth_token` 等字段齐全，新身份配置加在这里；
- 权限矩阵/审计字段/失败行为已完整写在 approved 规格
  `docs/40_specs/security/internal-workbench-rbac-audit-v1.md`，照规格实现即可。

## 5. 踩过的坑（重要）

1. **GitHub 网络间歇性失败**：`git push` 多次报 `Empty reply from server` / 连接超时，但
   `api.github.com` 正常。不要改 remote 或配置，**间隔 10–20 秒重试即可成功**。
2. **CI 的 integration job 耗时约 35 分钟**（其余 15 个 job 很快）。`gh run watch` 会超
   300s 工具上限，用 `gh run view <id> --json status,conclusion` 轮询。
3. **enterprise ORM 循环导入**：`infrastructure/models/__init__.py` 不能用
   `from flow_api.enterprise.models import X`（enterprise.models 依赖本包 base/intake，
   部分初始化时取不到属性）。解法：纯模块导入
   `import flow_api.enterprise.models as _enterprise_models`（ruff 排序会把它移到文件顶部，无害，已验证）。
4. **被 kill 的测试进程会把本地 DB 留在 downgrade 中间态**（test_migrations 跑到一半）。
   症状：后续混合跑大面积 ERROR。自愈：任意模块的 `migrated_database` fixture 会重新
   upgrade 到 head，重跑即恢复。
5. **本地直接 `uv run python` 读库会缺 Settings 环境变量**；测试环境由 conftest 注入，
   调试请走 pytest。
6. **根目录 HANDOFF.md 是 2026-09-12 战略交接**且被 D052/D053/D054 的 source_refs 引用，
   顶层交接文档的归宿是 `docs/knowledge-base/07_handoff/`（文档架构设计 §M5）。本会话一度
   误覆盖根 HANDOFF.md，已恢复（见下）；新交接一律放 07_handoff，且 07_handoff 内旧文件
   是 legacy-exempt 哈希锁，不可修改。
7. **docs/40_specs 不在知识库 manifest 范围内**（kb_manifest.py 只覆盖 docs/knowledge-base），
   新增规格无需动 99_manifest；但 07_handoff 新增文件需要 `--write` 重新生成清单。
8. **TDD 节奏是硬性约定**：每个 Task 先写失败测试并确认红灯（模块不存在即预期红灯）再实现；
   提交信息用计划文件里给定的字符串；规格未 approved 前不写代码，转 approved 需用户明确批准。

## 6. 快速恢复清单（接手后按序执行）

```bash
git pull origin main
gh run list --repo davyzhong/FLOW --limit 2                       # 确认 f366cc2 CI 绿
python3 scripts/documentation/require_approved_specs.py           # 应输出门禁通过
make docs-check                                                   # 应全 PASS
cd services/api && uv run pytest tests/financial_facts_v2 \
  tests/integration/test_enterprise_cycle_schema.py \
  tests/integration/test_migrations.py -q
```

全绿后从 Task 6 开始，严格按计划文件与三份 approved 规格执行。
