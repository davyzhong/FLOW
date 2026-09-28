import { expect, test, type Page } from "@playwright/test";

import { dashboardOracle } from "./support";

// 状态门禁（GPT 整改计划 Task 8 Step 3 / FE-11 的状态维切片）：
// 基础合同检查加载/错误/403结构；文件末尾的动态页面矩阵覆盖页面适用态与三档视口——
// - 任何状态下页面 h1 不消失（FE-10 合同的状态维推广）；
// - 加载态 = role=status；错误/403 态 = role=alert，错误文案为中文（STATUS_TEXT）；
// - PageState 标准化页面额外提供「重试」恢复动作。
// 空态是每页各自的引导文案（组件单测覆盖），不进本统一门禁；
// 403 在本系统当前 UI 中以中文错误条呈现（授权拒绝），不裸抛 403 技术码。
// 基础状态合同固定390px；动态页面矩阵另行覆盖390/1024/1440px。
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

test("analysis workbench explains an empty report list and finishes loading", async ({ page }) => {
  await page.route("**/api/v1/statements", (route) => route.fulfill({ json: { reports: [] } }));
  await page.goto("/analysis", { waitUntil: "domcontentloaded" });
  await waitForStyles(page);
  await expect(page.getByRole("heading", { name: "四问分析工作台" })).toBeVisible();
  await expect(page.getByRole("status")).toContainText("尚无可分析的财报");
  await expect(page.getByRole("link", { name: "前往数据接入" })).toHaveAttribute("href", "/data");
});

test("operations page explains when no usable periods are available", async ({ page }) => {
  await page.route("**/api/v1/statements", (route) => route.fulfill({ json: { reports: [] } }));
  await page.route("**/api/v1/operations/public-periods", (route) =>
    route.fulfill({ json: { periods: [] } }),
  );
  await page.goto("/operations", { waitUntil: "domcontentloaded" });
  await waitForStyles(page);
  await expect(page.getByRole("status")).toContainText("暂无可用经营分析数据");
  await expect(page.getByRole("link", { name: "前往数据接入" })).toHaveAttribute("href", "/data");
  await expect(page.getByRole("link", { name: "查看公开经营分析" })).toHaveAttribute("href", "/public");
});

// 剩余四个动态页面的状态 × 视口合同。所有状态由完整 API 响应夹具或明确的
// HTTP 错误在浏览器边界构造；不连接常驻数据库，也不把 mock 存在本身当作断言。
const STATE_VIEWPORTS = [
  { width: 390, height: 844, label: "390" },
  { width: 1024, height: 768, label: "1024" },
  { width: 1440, height: 900, label: "1440" },
] as const;

const REPORT = {
  id: "00000000-0000-4000-8000-000000000001",
  company_name: "测试物流公司",
  stock_code: "TEST.LOGISTICS",
  report_kind: "年度报告",
  period_label: "FY2025",
  version: 1,
  status: "published",
  unit_note: "人民币元",
  source_ref: "fixtures/state-matrix/report.pdf",
  source_sha256: "a".repeat(64),
  source_available: true,
  statement_types: ["利润表"],
  line_item_count: 1,
  created_at: "2026-09-28T00:00:00Z",
};

const BATCH_HISTORY = {
  items: [{
    id: "00000000-0000-4000-8000-000000000002",
    name: "状态矩阵批次",
    status: "published",
    description: "仅供页面状态与视口测试的完整API夹具",
    created_by: "state-matrix-test",
    created_at: "2026-09-28T00:00:00Z",
    version_count: 1,
    latest_version_sequence: 1,
    latest_version_status: "published",
  }],
  limit: 50,
};

const OPERATIONS_OVERVIEW = {
  report_id: REPORT.id,
  catalog_id: "flow.analysis.objective_finance.v1",
  themes: [
    { theme_id: "profit_quality", name: "盈利质量", availability: "financial_report", status: "available", reason: null, metrics: [] },
    { theme_id: "revenue_structure", name: "收入结构", availability: "financial_report", status: "available", reason: null, metrics: [] },
    { theme_id: "users_channels", name: "用户与渠道", availability: "internal_process", status: "not_applicable", reason: "internal_data_required", metrics: [] },
    { theme_id: "capital_efficiency", name: "资本效率", availability: "financial_report", status: "available", reason: null, metrics: [] },
    { theme_id: "cash_flow", name: "现金流质量", availability: "financial_report", status: "available", reason: null, metrics: [] },
    { theme_id: "risk", name: "风险提示", availability: "internal_events", status: "not_applicable", reason: "internal_data_required", metrics: [] },
  ],
  management_watch: [],
};

const WORKBENCH = {
  workbench_id: "flow.analysis.objective_topics.v1",
  report: {
    report_id: REPORT.id,
    company_name: REPORT.company_name,
    period_label: REPORT.period_label,
    unit_note: REPORT.unit_note,
  },
  questions: [
    { key: "growth", name: "增长", metrics: [{ metric_code: "revenue", available: true, value: "500.0000" }], related_metrics: [], note: null },
    { key: "profit", name: "盈利", metrics: [{ metric_code: "net_margin", available: true, value: "0.0320" }], related_metrics: [], note: null },
    { key: "capital", name: "资本", metrics: [], related_metrics: [], note: null },
    { key: "cash", name: "现金", metrics: [], related_metrics: [], note: null },
  ],
  management_watch: [],
  facts_available: ["is.revenue"],
};

type MatrixPage = "dashboard" | "data" | "operations" | "analysis";
type MatrixState = "loaded" | "empty" | "loading" | "error" | "forbidden" | "degraded" | "stale";

const MATRIX_CASES: { page: MatrixPage; route: string; states: MatrixState[] }[] = [
  { page: "dashboard", route: "/", states: ["loaded", "empty", "loading", "error", "degraded", "stale"] },
  { page: "data", route: "/data", states: ["loaded", "empty", "loading", "error", "forbidden"] },
  { page: "operations", route: "/operations", states: ["loaded", "empty", "loading", "error", "forbidden"] },
  { page: "analysis", route: "/analysis", states: ["loaded", "empty", "loading", "error", "forbidden"] },
];

async function installMatrixState(page: Page, surface: MatrixPage, state: MatrixState) {
  if (surface === "dashboard") {
    const body = dashboardOracle();
    if (["loaded", "empty", "degraded", "stale"].includes(state)) {
      await page.route("**/api/v1/dashboard/overview*", (route) =>
        route.fulfill({ json: { ...body, state: state === "loaded" ? "ready" : state } }),
      );
    } else if (state === "loading") {
      await page.route("**/api/v1/dashboard/overview*", async () => new Promise(() => undefined));
    } else {
      await page.route("**/api/v1/dashboard/overview*", (route) =>
        route.fulfill({ status: 503, json: { detail: { code: "unavailable", message: "service unavailable" } } }),
      );
    }
    return;
  }

  if (surface === "data") {
    if (state === "loaded" || state === "empty") {
      await page.route("**/api/v1/intake/batches", (route) =>
        route.fulfill({ json: state === "loaded" ? BATCH_HISTORY : { items: [], limit: 50 } }),
      );
    } else if (state === "loading") {
      await page.route("**/api/v1/intake/batches", async () => new Promise(() => undefined));
    } else {
      await page.route("**/api/v1/intake/batches", (route) =>
        route.fulfill({ status: state === "forbidden" ? 403 : 503, json: { detail: { code: state === "forbidden" ? "role_forbidden" : "unavailable", message: "request failed" } } }),
      );
    }
    return;
  }

  if (surface === "operations") {
    const hasReport = state === "loaded" || state === "loading";
    await page.route("**/api/v1/statements", (route) => {
      if (state === "error" || state === "forbidden") {
        return route.fulfill({
          status: state === "forbidden" ? 403 : 503,
          json: { detail: { code: state === "forbidden" ? "role_forbidden" : "unavailable", message: "request failed" } },
        });
      }
      return route.fulfill({ json: { reports: hasReport ? [REPORT] : [] } });
    });
    await page.route("**/api/v1/operations/public-periods", (route) =>
      route.fulfill({ json: { periods: [] } }),
    );
    if (state === "loaded") {
      await page.route(`**/api/v1/operations/overview/${REPORT.id}`, (route) =>
        route.fulfill({ json: OPERATIONS_OVERVIEW }),
      );
    } else if (state === "loading") {
      await page.route(`**/api/v1/operations/overview/${REPORT.id}`, async () => new Promise(() => undefined));
    }
    return;
  }

  if (state === "loaded" || state === "loading") {
    await page.route("**/api/v1/statements", (route) => route.fulfill({ json: { reports: [REPORT] } }));
    if (state === "loaded") {
      await page.route(`**/api/v1/analysis/workbench/${REPORT.id}`, (route) =>
        route.fulfill({ json: WORKBENCH }),
      );
    } else {
      await page.route(`**/api/v1/analysis/workbench/${REPORT.id}`, async () => new Promise(() => undefined));
    }
  } else if (state === "empty") {
    await page.route("**/api/v1/statements", (route) => route.fulfill({ json: { reports: [] } }));
  } else {
    await page.route("**/api/v1/statements", (route) =>
      route.fulfill({
        status: state === "forbidden" ? 403 : 503,
        json: { detail: { code: state === "forbidden" ? "role_forbidden" : "unavailable", message: "request failed" } },
      }),
    );
  }
}

async function expectMatrixState(page: Page, surface: MatrixPage, state: MatrixState) {
  if (surface === "dashboard") {
    if (state === "loaded" || state === "degraded" || state === "stale") {
      await expect(page.getByRole("region", { name: "经营驾驶舱内容" })).toBeVisible();
      if (state === "degraded") await expect(page.getByText("部分分析面板已降级")).toBeVisible();
      if (state === "stale") await expect(page.getByText("数据已陈旧，请检查最新发布批次")).toBeVisible();
    } else if (state === "empty") {
      await expect(page.getByRole("status")).toContainText("经营总览需要已发布的分析快照");
    } else if (state === "loading") {
      await expect(page.getByRole("status", { name: "正在加载经营驾驶舱" })).toBeVisible();
    } else {
      await expect(page.locator(MAIN_ALERT)).toContainText("经营驾驶舱暂时无法加载");
    }
    return;
  }

  if (surface === "data") {
    await expect(page.getByRole("heading", { name: "数据工作台" })).toBeVisible();
    await expect(page.getByLabel("选择文件")).toBeVisible();
    if (state === "loaded") await expect(page.getByRole("row", { name: /状态矩阵批次/ })).toBeVisible();
    if (state === "empty") await expect(page.getByRole("status")).toContainText("暂无可见批次");
    if (state === "loading") await expect(page.getByRole("status")).toContainText("正在读取历史批次");
    if (state === "error") await expect(page.getByRole("status")).toContainText("批次历史暂时无法加载");
    if (state === "forbidden") await expect(page.getByRole("status")).toContainText("无权读取当前企业的批次历史");
    return;
  }

  if (surface === "operations") {
    await expect(page.getByRole("heading", { name: "经营分析概览" })).toBeVisible();
    if (state === "loaded") await expect(page.getByRole("heading", { name: "六主题概览" })).toBeVisible();
    if (state === "empty") await expect(page.getByRole("status")).toContainText("暂无可用经营分析数据");
    if (state === "loading") await expect(page.getByRole("status")).toContainText("正在读取经营分析概览");
    if (state === "error" || state === "forbidden") await expect(page.locator("main [role=alert]")).toBeVisible();
    return;
  }

  await expect(page.getByRole("heading", { name: "四问分析工作台" })).toBeVisible();
  if (state === "loaded") await expect(page.getByRole("heading", { name: "增长" })).toBeVisible();
  if (state === "empty") await expect(page.getByRole("status")).toContainText("尚无可分析的财报");
  if (state === "loading") await expect(page.getByRole("status")).toContainText("加载中");
  if (state === "error" || state === "forbidden") await expect(page.locator("main [role=alert]")).toBeVisible();
}

async function expectNoHorizontalOverflow(page: Page, route: string, state: MatrixState, width: number) {
  const overflow = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    body: document.body.scrollWidth,
  }));
  expect(overflow.body, `${route} ${state} @${width}px`).toBeLessThanOrEqual(overflow.viewport);
}

test.describe("dynamic page state × viewport matrix", () => {
  for (const entry of MATRIX_CASES) {
    for (const state of entry.states) {
      for (const viewport of STATE_VIEWPORTS) {
        test(`${entry.route} ${state} @${viewport.label}px`, async ({ page }) => {
          await page.setViewportSize({ width: viewport.width, height: viewport.height });
          const pageErrors: string[] = [];
          page.on("pageerror", (error) => pageErrors.push(error.message));
          await installMatrixState(page, entry.page, state);
          const route = entry.page === "operations" && (state === "loaded" || state === "loading")
            ? `/operations?report=${REPORT.id}`
            : entry.route;
          await page.goto(route, { waitUntil: "domcontentloaded" });
          await waitForStyles(page);
          await expectMatrixState(page, entry.page, state);
          await page.waitForTimeout(200);
          await expectNoHorizontalOverflow(page, entry.route, state, viewport.width);
          expect(pageErrors, `${entry.route} ${state} @${viewport.width}px page errors`).toEqual([]);
        });
      }
    }
  }
});
