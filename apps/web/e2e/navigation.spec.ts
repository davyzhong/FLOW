import { test, expect } from "@playwright/test";

// 导航完整性守护：所有交互页面必须保留左侧工作流导航（用户明确要求）。
// 新增页面时必须在本清单登记路由并包裹 AppShell；login 除外（登录前无导航）。
const INTERACTIVE_ROUTES = [
  "/",
  "/analysis",
  "/data",
  "/investigations",
  "/reports",
  "/statements",
  "/metric-library",
  "/operations",
];

test.describe("navigation integrity", () => {
  for (const route of INTERACTIVE_ROUTES) {
    test(`workflow nav stays visible on ${route}`, async ({ page }) => {
      await page.goto(route);
      const nav = page.locator('nav[aria-label="FLOW 工作流"]');
      await expect(nav).toBeVisible();
      // 导航必须包含指向其他交互页的链接（不只是空壳）
      await expect(nav.locator("a").first()).toBeVisible();
    });
  }

  test("nav links reach every registered route", async ({ page }) => {
    await page.goto("/analysis");
    const nav = page.locator('nav[aria-label="FLOW 工作流"]');
    for (const route of INTERACTIVE_ROUTES) {
      await expect(
        nav.locator(`a[href="${route}"]`),
        `导航缺少指向 ${route} 的入口`,
      ).toHaveCount(1);
    }
  });
});
