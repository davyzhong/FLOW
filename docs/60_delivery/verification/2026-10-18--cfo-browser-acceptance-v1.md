---
doc_id: FLOW-VER-CFO-BROWSER-ACCEPTANCE-20261018
title: CFO 驾驶舱真实数据浏览器验收
doc_type: verification
status: current
version: 1.0
created_at: 2026-10-18
updated_at: 2026-10-18
owner: FLOW
commit_refs: [65a08706]
applies_to: cockpit
---

# CFO 驾驶舱真实数据浏览器验收

## 结论

工作包 7a 第 4 阶段子步 4.7 的浏览器验收在隔离环境完成。真实大麦双财年数据下，9 个 CFO/数据页面在桌面和手机视口呈现图表，图表值与 API 逐项一致；无横向溢出。浏览器回归 165/165 通过。代码基线为 `65a087063ad67702172430702590083f8991a884`。准确 SHA 对应 GitHub CI `39139310634` 在本记录编写时仍排队，故工作包最终结案仍以该 CI 及路线图规定的最终集成门禁为准。

## 环境与数据

- 一次性隔离 Compose 项目：`flow-cockpit-acceptance-manual`，独立端口 35432/36379/39000/39001；API 和临时 Web 服务仅在验收期间运行，已停止。
- 使用大麦发行包隔离种子，包含 FY2022/FY2023、workflow 数据、Objective 快照与行动项。发行验证 19/19 通过。
- 未连接、停止、重置或修改其他项目使用的 `cockpit-plan-run-20261017`，未触碰常驻 `work/damai-demo` 数据。
- Playwright screenshot 与 trace 均关闭；没有创建或保存页面截图。

## 结果

- 真实数据 CFO 页面验收：9 个 CFO/数据路由，在 1440px 与 390px 视口渲染通过；图表数据逐项核对 API；无窄屏横向溢出。
- 同一旅程覆盖来源详情键盘展开、财报来源行深链、CFO Action 确认和 403 行为。
- 浏览器回归：165/165 通过，包含 `navigation.spec.ts`、`deep-links.spec.ts`、`frontend-consistency.spec.ts`、`frontend-responsive.spec.ts`、`frontend-states.spec.ts`、`dashboard-states.spec.ts`、`module-boundaries.spec.ts`；视口覆盖 390/1024/1440px，并检查 44px 触控目标。
- 发行包/快照/来源/存储核验：19/19 通过。
- 独立审查未发现影响正确性或验收要求的 P1/P2。

## 结案边界

此记录证明隔离真实数据浏览器验收通过，不替代准确 SHA GitHub Actions CI。CI run `39139310634` 仍排队；状态完成前不得将整个工作包标为最终完成。截图采集与 README 自动截图工作流仍暂停。
