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

  test("five KPI cards stay readable on a narrow viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.route("**/api/v1/cockpit/modules/expenses", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        module: "expenses",
        title: "费用分析",
        period: "FY2023",
        prior_period: "FY2022",
        snapshot_id: "visual-regression",
        report_ids: [],
        source_notice: "布局回归样例",
        unit: "百万元",
        kpis: ["销售费用", "管理费用", "研发费用", "财务费用", "期间费用"].map((name) => ({
          name,
          status: "available",
          value: "1234.56",
          prior_value: "1200.00",
          unit: "百万元",
          caliber_note: null,
        })),
        charts: {},
        unavailable: [],
      }),
    }));
    await page.goto("/cockpit/expenses");

    await expect(page.locator('.module-page[data-status="ready"]')).toBeVisible();
    const grid = page.locator(".module-kpi-grid[data-count='5']");
    await expect(grid).toBeVisible();
    const layout = await grid.evaluate((element) => ({
      columns: getComputedStyle(element).gridTemplateColumns.split(" ").length,
      cardWidth: element.querySelector(".module-kpi-card")?.getBoundingClientRect().width ?? 0,
      viewportWidth: document.documentElement.clientWidth,
      pageWidth: document.documentElement.scrollWidth,
    }));

    expect(layout.columns).toBe(2);
    expect(layout.cardWidth).toBeGreaterThan(140);
    expect(layout.pageWidth).toBe(layout.viewportWidth);
  });
});
