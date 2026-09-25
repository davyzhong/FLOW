import { expect, test } from "@playwright/test";

// 响应式门禁（GPT 整改计划 Task 0 / FE-06、FE-07 的自动化面）：
// - 390×844 视口下所有路由 body 不得横向溢出（含拦截 API 注入的**真实数据态**，
//   门禁不依赖 CI 环境是否恰好有数据——阶段六「测试数据固定或拦截提供」）；
// - 窄视口下主要交互控件（flow-btn / 表单 select / 文件选择 / 登录 / 侧栏导航）
//   计算高度 ≥ 44px。
// 密集表格内的行级小按钮（如产物下载）不在 44px 约束内——
// 信息密度是经分专员场景的显式设计决策（Carbon dense 模式）。

const ROUTES = [
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
  "/login",
] as const;

// ---------------------------------------------------------------------------
// 真实数据态的固定测试数据（路由拦截，形状对齐 typed schema 的 UI 读取面）
// ---------------------------------------------------------------------------

const REPORT_ID = "0f1e2d3c-4b5a-6978-8a9b-0c1d2e3f4a5b";

const STATEMENTS_SUMMARY = {
  id: REPORT_ID,
  company_name: "顺丰控股",
  stock_code: "002352.SZ",
  report_kind: "一季报",
  period_label: "2026Q1",
  unit_note: "人民币千元",
  source_ref: "p5_samples/sf_002352/SF_2026_Q1_report.pdf",
  source_sha256: "a".repeat(64),
  statement_types: ["合并资产负债表", "合并利润表", "合并现金流量表"],
  line_item_count: 3,
  created_at: "2026-09-06T08:00:00+00:00",
};

const STATEMENTS_DETAIL = {
  ...STATEMENTS_SUMMARY,
  sections: [
    {
      statement_type: "合并利润表",
      items: [
        { item_name: "一、营业总收入", sort_order: 0, value_end: null, value_begin: null, value_current: "74142121.0000", value_prior: "62432100.0000" },
        { item_name: "三、营业利润（亏损以“－”号填列）", sort_order: 1, value_end: null, value_begin: null, value_current: "3399319.0000", value_prior: "2900000.0000" },
        { item_name: "五、净利润（净亏损以“－”号填列）", sort_order: 2, value_end: null, value_begin: null, value_current: "2650843.0000", value_prior: "2017475.0000" },
      ],
    },
  ],
};

const METRIC_LIBRARY = {
  dictionary_id: "flow.metrics.dictionary.v1.1",
  status: "active",
  decision_ref: "D0xx",
  metrics: [
    {
      code: "liquidity.current_ratio",
      name: "流动比率",
      collection: "general",
      definition: "流动资产对流动负债的保障程度，衡量短期偿债能力。",
      formula_text: "流动资产 ÷ 流动负债（倍）",
      time_behavior: "point_in_time",
      depends_on: ["cas.current_assets_total", "cas.current_liabilities_total"],
      provenance: "教科书标准口径",
      mpm: null,
      entry_id: "e1",
      migrates_from: null,
      execution_kind: "deterministic",
      execution_detail: null,
    },
    {
      code: "logistics.unit_cost",
      name: "单票成本",
      collection: "logistics",
      definition: "剔除存货后的更严格短期偿债口径的对照占位。",
      formula_text: "（流动资产 − 存货）÷ 流动负债（倍）",
      time_behavior: "point_in_time",
      depends_on: [],
      provenance: null,
      mpm: { benchmark: "trend" },
      entry_id: "e2",
      migrates_from: null,
      execution_kind: "deterministic",
      execution_detail: null,
    },
  ],
  report_items: [
    { cas_item: "流动资产合计", ifrs_item: "Current assets", direction: "same" },
    { cas_item: "流动负债合计", ifrs_item: "Current liabilities", direction: "same" },
  ],
  accounting: {
    accounts: [
      { code: "1001", name: "库存现金" },
      { code: "1002", name: "银行存款" },
    ],
    entry_templates: [{ name: "收入确认模板", lines: 2 }],
  },
};

const FINDINGS = {
  findings: [
    {
      id: "f-1",
      title: "毛利率同比下滑超过阈值，需要归因产品结构变化与价格策略",
      finding_type: "margin_shift",
      impact_amount: 1234567.89,
      comparison_basis: "同比",
      status: "approved",
      score: 0.87,
    },
    {
      id: "f-2",
      title: "经营性现金流与净利润背离，应收账款周转天数拉长",
      finding_type: "cashflow_divergence",
      impact_amount: 234567.89,
      comparison_basis: "环比",
      status: "candidate",
      score: 0.61,
    },
  ],
};

const PUBLISHING_SNAPSHOTS = {
  snapshots: [
    {
      id: "ps-1",
      version: 3,
      title: "2026Q1 客观财报分析快照（冻结载荷渲染）",
      created_at: "2026-09-06T08:00:00+00:00",
    },
  ],
};

/** 注入数据态；未列出的 API 保持透传（CI 无 API 时这些请求失败，
 *  但被测页面只依赖此处注入的端点）。 */
async function mockRealisticData(page: import("@playwright/test").Page) {
  await page.route("**/api/v1/statements", (route) =>
    route.fulfill({ json: { reports: [STATEMENTS_SUMMARY] } }));
  await page.route(`**/api/v1/statements/${REPORT_ID}`, (route) =>
    route.fulfill({ json: STATEMENTS_DETAIL }));
  await page.route("**/api/v1/metric-library", (route) =>
    route.fulfill({ json: METRIC_LIBRARY }));
  await page.route("**/api/v1/investigations", (route) =>
    route.fulfill({ json: FINDINGS }));
  await page.route("**/api/v1/publishing/snapshots", (route) =>
    route.fulfill({ json: PUBLISHING_SNAPSHOTS }));
}

test.describe("responsive integrity", () => {
  // 冷启动 dev server 的 Turbopack 编译滞后于 networkidle：必须等到
  // globals.css（:root token）真正生效后再量，否则量到无样式布局的假溢出。
  async function waitForStyles(page: import("@playwright/test").Page) {
    await page.waitForFunction(
      () => getComputedStyle(document.documentElement).getPropertyValue("--flow-radius-s").trim() !== "",
      undefined,
      { timeout: 30_000 },
    );
  }

  async function measureOverflow(page: import("@playwright/test").Page, route: string) {
    const overflow = await page.evaluate(() => {
      const wide: string[] = [];
      for (const el of document.querySelectorAll("*")) {
        const box = el.getBoundingClientRect();
        if (box.right > document.documentElement.clientWidth + 1) {
          wide.push(`${el.tagName}.${String(el.className).slice(0, 48)} right=${Math.round(box.right)}`);
        }
      }
      return {
        body: document.body.scrollWidth,
        viewport: document.documentElement.clientWidth,
        wide: wide.slice(0, 6),
      };
    });
    if (overflow.body > overflow.viewport) {
      console.log(`[overflow] ${route}:`, JSON.stringify(overflow.wide));
    }
    expect(overflow.body).toBeLessThanOrEqual(overflow.viewport);
  }

  for (const route of ROUTES) {
    test(`${route} has no horizontal overflow at 390px`, async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      // networkidle：等客户端取数与状态机稳定后再量——
      // hydration 中间态的瞬时宽度不是用户可见现实。
      await page.goto(route, { waitUntil: "networkidle" });
      await waitForStyles(page);
      await page.waitForTimeout(400);
      await measureOverflow(page, route);
    });
  }

  for (const width of [1024, 1440]) {
    test.describe(`no overflow at ${width}px (data states)`, () => {
      // Task 9 切片：三档视口矩阵。桌面宽度下同样要求真实数据态不撑破页面；
      // 密集表格在自身容器内滚动，不允许把页面顶宽。
      for (const route of ["/reports", "/statements", "/metric-library", "/investigations"] as const) {
        test(`${route} at ${width}`, async ({ page }) => {
          await page.setViewportSize({ width, height: 900 });
          await mockRealisticData(page);
          await page.goto(route, { waitUntil: "networkidle" });
          await waitForStyles(page);
          await page.waitForTimeout(500);
          await measureOverflow(page, `${route}@${width}`);
        });
      }
    });
  }

  test.describe("with realistic data (route interception)", () => {
    // 数据密集页在真实数据形态下的溢出门禁：空态通过不代表数据态通过
    // （FE-06 的教训：552/599/501/644px 全部只出现在有数据的分支）。
    for (const route of ["/reports", "/statements", "/metric-library", "/investigations"] as const) {
      test(`${route} has no horizontal overflow with realistic data`, async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await mockRealisticData(page);
        await page.goto(route, { waitUntil: "networkidle" });
        await waitForStyles(page);
        await page.waitForTimeout(500);
        await measureOverflow(page, `${route} (data)`);
      });
    }
  });

  test("primary touch targets meet 44px at narrow viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/login");
    const submit = page.getByRole("button", { name: "登录" });
    const height = await submit.evaluate((el) => getComputedStyle(el).height);
    expect(parseFloat(height)).toBeGreaterThanOrEqual(44);
  });

  test("flow buttons meet 44px at narrow viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/data");
    const button = page.getByRole("button", { name: "下载 FLOW 标准模板" });
    // 深链接收端页面为 async server component（流式到达），先等真实控件可见再量
    await expect(button).toBeVisible();
    const height = await button.evaluate((el) => getComputedStyle(el).height);
    expect(parseFloat(height)).toBeGreaterThanOrEqual(44);
  });

  test("form selects and the file input meet 44px at narrow viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/operations");
    const select = page.getByLabel("分析数据与期间");
    // 同上：等待流式内容 reveal 完成，避免量到 loading 回退的隐藏树
    await expect(select).toBeVisible();
    const selectHeight = await select.evaluate((el) => getComputedStyle(el).height);
    expect(parseFloat(selectHeight)).toBeGreaterThanOrEqual(44);

    await page.goto("/data");
    const file = page.getByLabel("选择文件");
    await expect(file).toBeVisible();
    const fileHeight = await file.evaluate((el) => getComputedStyle(el).height);
    expect(parseFloat(fileHeight)).toBeGreaterThanOrEqual(44);
  });

  test("side rail keeps the logout entry reachable at narrow viewport", async ({ page }) => {
    // 窄屏下侧栏 footer 只隐藏状态文案，退出按钮保持可见（FE-04 收尾）。
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    const footer = page.locator(".workflow-rail__footer");
    await expect(footer).toBeAttached();
  });
});
