---
doc_id: FLOW-VER-CFO-METRIC-DISPLAY-20261018
title: CFO 模块指标展示与追溯验收
doc_type: verification
status: current
version: 1.0
created_at: 2026-10-18
updated_at: 2026-10-18
owner: FLOW
commit_refs: [65a08706]
evidence_refs: [cockpit-module-page-vitest-5, cockpit-number-format-vitest-6, cfo-cockpit-browser-9-routes, cfo-ui-regression-playwright-165]
applies_to: cockpit
---

# CFO 模块指标展示与追溯验收

## 结论

工作包 7a 第 4 阶段子步 4.6 的实现与本地验收通过，代码提交 `65a087063ad67702172430702590083f8991a884` 已推送。指标对比明确显示前期期间；持平值不再被误标为上升；公式链接仅对已核准映射生成；当前/前期来源链接分别指向对应财报。独立审查未发现影响正确性或既定需求的 P1/P2。GitHub run `39139310634` 对应准确 SHA，报告编写时仍在排队，不能描述为远端 CI 全绿。

## 修复内容

- 模块 KPI 显示前期标签及期间，例如“前期 FY2022”，并分别链接当期与前期来源财报。
- 方向属性区分上升、下降、持平、不可比；移除仅凭数值方向套用红绿语义的样式，避免将“上升”等同于经营改善。
- 仅为核实过的指标名称生成指标库深链。未知名称不再模糊匹配到订单指标；直接报表项目仍保留来源财报链接。
- 修正“净现比”口径映射为 `ocf_net_profit_ratio`；将其与 `debt_ebitda` 按指标字典显示为“倍”，不误显示为百分比。
- 补充 DSO、DIO、DPO、CCC 指标定义深链及同比期间、来源财报与不猜测映射的回归测试。

## 验收证据

- `pnpm --filter @flow/web test`：36 个测试文件、192 项通过。
- `pnpm --filter @flow/web typecheck`：通过。
- `pnpm --filter @flow/web lint`：0 错误；保留 3 条既有警告（`action-panel.tsx` 两条 hook 警告、`flow-data-table.tsx` 一条 TanStack Table 与 React Compiler 兼容性警告）。
- `pnpm --filter @flow/web build`：生产构建通过，CFO 页面路由均生成。
- 定向真实数据 Playwright：9 个 CFO/数据页面在 1440px、390px 视口通过，图表值与 API 数据逐项一致，无横向溢出；包含来源行链接、键盘展开来源、Action 确认交互。
- 浏览器路由、深链、页面状态和响应式回归：165/165 通过，覆盖 390/1024/1440px 视口与 44px 触控目标。
- 测试使用独立 Compose 数据库和对象存储；19/19 大麦发行包/快照/来源/存储核验通过。测试截图和 trace 已关闭；标准 `work/damai-demo` 原有回执与素材未改动。
- 独立审查：无影响正确性或既定需求的 P1/P2。可选观察：费用率卡片显示当期费率，百分点变化可在两期趋势图读取；当前不构成验收缺口。
- 准确 SHA 的 GitHub CI run `39139310634` 尚在排队；未宣称远端 CI 全绿。

## 边界

本验收没有改变财务事实、计算口径或数据库；不把数值上升直接判作经营改善。公开财报来源与 synthetic 演示事实保持分层。README 截图采集流程仍暂停。
