import { expect, test } from "@playwright/test";

// 状态门禁（GPT 整改计划 Task 8 Step 3 / FE-11 的状态维切片）：
// 五态合同中可被路由拦截确定性构造的三态（加载 / 错误 / 403）做结构断言——
// - 任何状态下页面 h1 不消失（FE-10 合同的状态维推广）；
// - 加载态 = role=status；错误/403 态 = role=alert，错误文案为中文（STATUS_TEXT）；
// - PageState 标准化页面额外提供「重试」恢复动作。
// 空态是每页各自的引导文案（组件单测覆盖），不进本统一门禁；
// 403 在本系统当前 UI 中以中文错误条呈现（授权拒绝），不裸抛 403 技术码。
// 视口固定 390px：状态是结构合同而非宽度合同（宽度由 frontend-responsive 覆盖）。
// 注意：Next.js RouteAnnouncer（#__next-route-announcer__）本身是 role=alert，
// alert 断言必须收窄到 main 区域，否则 strict mode 双元素冲突。

const API_GLOB = "**/api/v1/**";
const MAIN_ALERT = "main [role=alert]";

const PAGESTATE_ROUTES = ["/operations", "/metric-library"] as const;

const ALERT_ROUTES = [
  "/operations",
  "/metric-library",
  "/statements",
  "/reports",
  "/investigations",
  "/analysis",
] as const;

async function waitForStyles(page: import("@playwright/test").Page) {
  await page.waitForFunction(
    () => getComputedStyle(document.documentElement).getPropertyValue("--flow-radius-s").trim() !== "",
    undefined,
    { timeout: 30_000 },
  );
}

test.describe("state matrix: loading", () => {
  for (const route of PAGESTATE_ROUTES) {
    test(`${route} keeps h1 and shows status role while loading`, async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      // 挂起所有 API：loading 态稳定可断言（goto 用 domcontentloaded，不等 networkidle）
      await page.route(API_GLOB, async () => {
        await new Promise(() => undefined);
      });
      await page.goto(route, { waitUntil: "domcontentloaded" });
      await waitForStyles(page);
      await expect(page.locator("main [role=status]")).toBeVisible({ timeout: 15_000 });
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    });
  }
});

test.describe("state matrix: error", () => {
  for (const route of ALERT_ROUTES) {
    test(`${route} keeps h1, shows alert on 503`, async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.route(API_GLOB, (route) =>
        route.fulfill({
          status: 503,
          contentType: "application/json",
          body: JSON.stringify({ detail: { code: "unavailable", message: "service unavailable" } }),
        }),
      );
      await page.goto(route, { waitUntil: "domcontentloaded" });
      await waitForStyles(page);
      await expect(page.locator(MAIN_ALERT)).toBeVisible({ timeout: 15_000 });
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    });
  }

  test("metric-library offers a retry action on PageState error", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.route(API_GLOB, (route) =>
      route.fulfill({ status: 503, contentType: "application/json", body: "{}" }),
    );
    await page.goto("/metric-library", { waitUntil: "domcontentloaded" });
    await waitForStyles(page);
    await expect(page.getByRole("button", { name: "重试" })).toBeVisible({ timeout: 15_000 });
  });
});

test.describe("state matrix: forbidden", () => {
  for (const route of ALERT_ROUTES) {
    test(`${route} renders a Chinese alert on 403`, async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.route(API_GLOB, (route) =>
        route.fulfill({
          status: 403,
          contentType: "application/json",
          body: JSON.stringify({
            detail: { code: "role_forbidden", message: "授权拒绝：role_forbidden" },
          }),
        }),
      );
      await page.goto(route, { waitUntil: "domcontentloaded" });
      await waitForStyles(page);
      const alert = page.locator(MAIN_ALERT);
      await expect(alert).toBeVisible({ timeout: 15_000 });
      // 403 文案有两套既定措辞：标准 STATUS_TEXT（授权拒绝：…）与
      // operations-overview 的角色指引版（没有访问权限：…）；两者皆中文、不裸抛技术码。
      await expect(alert).toContainText(/授权拒绝|没有访问权限/);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    });
  }
});

test.describe("state matrix: data workbench history", () => {
  test("announces the loading history without hiding the upload workbench", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.route("**/api/v1/intake/batches", async () => {
      await new Promise(() => undefined);
    });
    await page.goto("/data", { waitUntil: "domcontentloaded" });
    await waitForStyles(page);
    await expect(page.getByRole("heading", { name: "数据工作台" })).toBeVisible();
    await expect(page.getByRole("status")).toContainText("正在读取历史批次");
    await expect(page.getByLabel("选择文件")).toBeVisible();
  });

  test("explains 403 history access while leaving permitted upload actions visible", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.route("**/api/v1/intake/batches", (route) =>
      route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: { code: "role_forbidden", message: "forbidden" } }),
      }),
    );
    await page.goto("/data", { waitUntil: "domcontentloaded" });
    await waitForStyles(page);
    await expect(page.getByRole("status")).toContainText("无权读取当前企业的批次历史");
    await expect(page.getByLabel("选择文件")).toBeVisible();
  });
});

test("analysis workbench announces a pending report response", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/api/v1/statements", (route) =>
    route.fulfill({
      json: {
        reports: [{
          id: "report-1",
          company_name: "测试公司",
          period_label: "FY2025",
          unit_note: "CNY",
          stock_code: "TEST",
          report_kind: "annual",
          statement_types: [],
          line_item_count: 0,
          created_at: "2026-01-01T00:00:00Z",
          source_ref: "test.pdf",
          source_sha256: "a".repeat(64),
        }],
      },
    }),
  );
  await page.route("**/api/v1/analysis/workbench/report-1", async () => {
    await new Promise(() => undefined);
  });
  await page.goto("/analysis", { waitUntil: "domcontentloaded" });
  await waitForStyles(page);
  await expect(page.getByRole("heading", { name: "四问分析工作台" })).toBeVisible();
  await expect(page.getByRole("status")).toContainText("加载中");
});
