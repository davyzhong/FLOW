import { expect, test } from "@playwright/test";

// 前端一致性门禁（GPT 整改计划 Task 0，防「删样式不迁组件」回归的 e2e 面）：
// - 业务路由必须有 AppShell 侧栏与页面 h1（错误态也不许裸奔）；
// - /data、/reports 的基础控件必须走 flow-* 体系（不允许退回浏览器默认样式）；
// - /login 是唯一无 AppShell 路由，且必须使用统一登录卡片。
// 说明：本 spec 在无 API 的纯 web 栈上运行（与 navigation.spec 同栈），
// 数据面断言只看壳层与样式，不依赖接口返回。

const BUSINESS_ROUTES = [
  "/",
  "/data",
  "/reports",
  "/statements",
  "/metric-library",
  "/operations",
  "/public",
  "/internal",
  "/investigations",
  "/analysis",
] as const;

test.describe("frontend consistency", () => {
  for (const route of BUSINESS_ROUTES) {
    test(`${route} renders the app shell and a page heading`, async ({ page }) => {
      await page.goto(route);
      await expect(page.getByRole("navigation", { name: "FLOW 工作流" })).toBeVisible();
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    });
  }

  test("/login stays outside the app shell and uses the unified card", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("navigation", { name: "FLOW 工作流" })).toHaveCount(0);
    await expect(page.locator(".login-card")).toBeVisible();
    await expect(page.getByRole("heading", { name: "登录 FLOW" })).toBeVisible();
  });

  test("/data keeps styled workbench controls (no browser-default regression)", async ({ page }) => {
    await page.goto("/data");
    const download = page.getByRole("button", { name: "下载 FLOW 标准模板" });
    await expect(download).toHaveClass(/flow-btn/);
    const radius = await download.evaluate((el) => getComputedStyle(el).borderRadius);
    expect(parseFloat(radius)).toBeGreaterThan(0);
  });

  test("/reports keeps styled section cards and buttons", async ({ page }) => {
    await page.goto("/reports");
    const card = page.locator(".reports-center__objective").first();
    await expect(card).toBeVisible();
    const radius = await card.evaluate((el) => getComputedStyle(el).borderRadius);
    expect(parseFloat(radius)).toBeGreaterThan(0);
  });
});
