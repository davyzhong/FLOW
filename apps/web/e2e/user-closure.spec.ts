import { expect, test } from "@playwright/test";
import path from "node:path";

// Pilot Readiness Phase 1 — 用户闭环浏览器冒烟：
// 1) /data 工作台可加载并下载治理化模板；
// 2) /reports 报告中心可加载；
// 3) 仪表盘工作流导航指向真实路由。
// 完整上传→发布旅程由 make test-user-closure-e2e 中的 API 契约测试与组件测试共同覆盖。

test("data workbench loads and offers the governed template", async ({ page }) => {
    console.log("SPEC ENV:", JSON.stringify({ b: process.env.PLAYWRIGHT_BASE_URL ?? null }));
  await page.goto("/data");
  await expect(page.getByRole("heading", { name: "数据工作台" })).toBeVisible();
  await expect(page.getByText(/准备/)).toBeVisible();

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "下载 FLOW 标准模板" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("flow.excel.v1.template.xlsx");
});

test("reports center loads with freeze form", async ({ page }) => {
  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: "报告中心" })).toBeVisible();
  await expect(page.getByText("冻结新报告快照")).toBeVisible();
});

test("dashboard workflow nav links to the workbench and report center", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("link", { name: /数据接入/ })).toHaveAttribute("href", "/data");
  await expect(page.getByRole("link", { name: /报告与导出/ })).toHaveAttribute("href", "/reports");
});

test("uploads the standard workbook through the workbench happy path", async ({ page }) => {
  await page.goto("/data");
  const fixture = path.resolve(
    __dirname,
    "../../../fixtures/workbooks/flow_standard_v1.xlsx",
  );
  // 历史批次区仅在客户端水合并完成身份拉取后渲染（dev 模式水合较慢），
  // 以它的出现作为水合证据，避免 change 事件早于 React 挂载而丢失。
  await expect(page.getByRole("region", { name: "最近的数据批次" })).toBeVisible({
    timeout: 30_000,
  });
  await page.getByLabel("选择文件").setInputFiles(fixture);
  // 映射阶段以确认按钮出现为准（getByRole("table") 会误匹配历史批次表），
  // 上传/建批/映射提议是三次串行请求，给足超时。
  const confirmButton = page.getByRole("button", { name: "确认映射并校验" });
  await expect(confirmButton).toBeVisible({ timeout: 60_000 });
  await confirmButton.click();
  await expect(page.getByText(/清洗与校验结果/)).toBeVisible({ timeout: 30000 });
});
