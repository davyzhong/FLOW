import { test, expect } from "@playwright/test";

// 导航完整性守护：所有交互页面必须保留左侧工作流导航（用户明确要求）。
// 新增页面时必须在本清单登记路由并包裹 AppShell；login 除外（登录前无导航）。
const INTERACTIVE_ROUTES = [
  "/",
  "/analysis",
  "/cockpit",
  "/cockpit/profitability",
  "/cockpit/balance-sheet",
  "/cockpit/working-capital",
  "/cockpit/expenses",
  "/cockpit/cashflow",
  "/cockpit/risk",
  "/cockpit/consolidation",
  "/data",
  "/investigations",
  "/reports",
  "/statements",
  "/metric-library",
  "/operations",
  "/public",
  "/internal",
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

  test("mobile navigation opens, closes with Escape, and closes after route selection", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/cockpit");
    const toggle = page.getByRole("button", { name: "打开导航菜单" });
    const nav = page.locator('nav[aria-label="FLOW 工作流"]');
    const links = nav.locator(".workflow-rail__links");

    await expect(toggle).toBeVisible();
    await expect(links).toBeHidden();
    await toggle.click();
    await expect(page.getByRole("button", { name: "关闭导航菜单" })).toHaveAttribute("aria-expanded", "true");
    await expect(nav.getByRole("link", { name: /盈利能力与杜邦分析/ })).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(links).toBeHidden();
    await page.getByRole("button", { name: "打开导航菜单" }).click();
    await nav.getByRole("link", { name: /盈利能力与杜邦分析/ }).click();
    await expect(page).toHaveURL(/\/cockpit\/profitability$/);
    await expect(links).toBeHidden();
  });
});
