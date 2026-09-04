# FLOW Review Repairs Implementation Plan

> **适用性说明（2026-09-04，代码基线 `c1a59d1`）**：本计划 R1–R9 已实施；随后追加 N1–N3 亦已修复。正文任务记录保留，不能将已关闭缺陷重新列为待实现范围。
> 当前入口见[文档导航](../../README.md)，后续缺陷修复与验证边界见[2026-09-04 修复验收](../../implementation/2026-09-04-review-repairs.md)。

> **For agentic workers:** Use subagent-driven-development or executing-plans task-by-task; user has authorized implementation of the reviewed fixes.

**Goal:** 修复 R1–R9，先完成三项 P1 再处理六项 P2。
**Architecture:** 持久化冻结报告、受控复核状态机、源身份绑定映射；保留现有分层和财务口径。
**Tech Stack:** FastAPI / SQLAlchemy / PostgreSQL / Next.js / Vitest / pytest。

## Task 1 — P1 发布与复核
- [x] 在 publishing/test_freeze.py 增加冻结内容漂移、版本化、legacy、资格检查失败回归并运行。
- [x] 修改 publishing/service.py、models.py、infrastructure/models/publishing.py，增加 0010 frozen_view migration。
- [x] 在 investigation/test_state_machines.py 增加批准后证据拒绝测试，修复状态机与共享锁。
- [x] 独立DB运行 publishing/investigation 测试；复核错误路径与历史兼容。

## Task 2 — P1 手工映射
- [x] tests/api/test_intake_overrides.py 串联 override→confirm→validate，验证修正后的实际值。
- [x] routes/intake.py 恢复映射并核验源身份，拒绝错源/跨batch；运行 intake 回归。
- [x] 验收全部 P1 后提交阶段结果。

## Task 3 — P2 数据工作台
- [x] 组件测试先验证真实SHA、warning阻断、填写原因后解锁。
- [x] 修改 components/data/data-workbench.tsx 与 lib/api/client.ts，保留问题详情和下一步动作；Vitest及类型检查。

## Task 4 — P2 Copilot
- [x] 成功响应后独立Session可读审计；双batch仍可访问旧批次大纲。
- [x] routes/copilot.py 成功commit；service.py 先过滤batch和published状态；API/评估回归。

## Task 5 — P2 输出
- [x] PPTX 有效尺寸、页面边界与分页测试；修复 renderers.py。
- [x] 代理二进制响应保留文件名、无header按格式fallback测试；修复route.ts/reports-center.tsx。

## Task 6 — 收尾
- [x] Ruff/mypy/TS/Vitest、受影响后端回归、契约一致性和独立审查。
- [x] 更新实现证据与知识库索引/manifest，只提交本任务文件，推送origin。

## 追加任务 — N1/N3（用户继续修复授权）
- [x] 按既有安全计划 Task A/B 补单用户登录、签名会话、来源校验、服务端代理凭据和反代公开 origin。
- [x] 去掉认证单测数据库迁移，修正 CI unit/integration 选择并在不可用 DB 环境验证。
- [x] 认证定向测试、生产构建、真实浏览器及独立复核；更新配置与部署说明。
