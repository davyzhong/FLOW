import { expect, test } from "@playwright/test";

import { dashboardOracle } from "./support";

// 深链接收端 e2e 断言（批次一 §5.3）：带参打开页面能定位目标实体、
// 参数非法/对象不存在时显式提示、驾驶舱深链不被 replaceState 抹掉。
// 全部 API 走 page.route 拦截，无需数据库。

const REGION_ID = "158e0a75-4853-5f1a-94b1-da561ccdd70a";

const METRIC = {
  metric_code: "roe",
  name: "净资产收益率",
  entry_id: "entry-roe",
  status: "effective",
  execution_kind: "facts",
  collection: "general",
  domain: "profitability",
  definition: "净利润与平均净资产之比。",
  formula_text: "净利润 ÷ 平均净资产",
  mpm: false,
  aliases: [],
  depends_on: [],
  source_cas: [],
  decompositions: [],
  alternative_calibers: [],
};

const LIBRARY = {
  dictionary_id: "flow.metric_dictionary.v1",
  status: "effective",
  decision_ref: "D047",
  created: "2026-09-06",
  standards_scope: ["CAS", "IFRS"],
  domains: { profitability: "盈利能力" },
  report_items: [],
  metrics: [
    METRIC,
    { ...METRIC, metric_code: "on_time_rate", name: "准时交付率", entry_id: "entry-otr", collection: "logistics" },
  ],
  relations: [],
  accounting: {
    dataset_id: "flow.accounting_foundation.v1",
    status: "effective",
    known_gaps: [],
    categories: [],
    accounts: [],
    superseded_notes: [],
    standards: [],
    entry_templates: [],
  },
};

const REPORT_A = {
  id: "0f1e2d3c-4b5a-6978-8a9b-0c1d2e3f4a5b",
  company_name: "顺丰控股",
  stock_code: "002352.SZ",
  report_kind: "一季报",
  period_label: "2026Q1",
  unit_note: "人民币千元",
  source_ref: "p5_samples/sf.pdf",
  source_sha256: "a".repeat(64),
  statement_types: ["合并利润表"],
  line_item_count: 1,
  created_at: "2026-09-06T08:00:00+00:00",
};
const REPORT_B = { ...REPORT_A, id: "2b3c4d5e-6f70-8192-a3b4-c5d6e7f8091a", company_name: "圆通速递" };

const SNAPSHOT_1 = {
  id: "snap-1",
  metric_snapshot_id: "ms-1",
  version: 1,
  title: "2026-08 经营月报",
  created_at: "2026-09-03T09:00:00+08:00",
};
const SNAPSHOT_2 = { ...SNAPSHOT_1, id: "snap-2", metric_snapshot_id: "ms-2", version: 2, title: "2026-07 经营月报" };

test.describe("深链接收端（批次一）", () => {
  test("驾驶舱：URL 筛选参数随请求生效且不被 replaceState 抹掉", async ({ page }) => {
    await page.route("**/api/v1/dashboard/**", (route) =>
      route.fulfill({ json: dashboardOracle() }),
    );
    await page.goto(`/?region_id=${REGION_ID}`);
    await expect(page.getByTestId("metric-card").first()).toBeVisible();
    // 深链保留在地址栏（可分享、可复现）
    await expect(page).toHaveURL(new RegExp(`region_id=${REGION_ID}`));
    // 指标卡链接到指标库 focus 深链
    const cardLink = page.getByTestId("metric-card").first().getByRole("link");
    await expect(cardLink).toHaveAttribute("href", /^\/metric-library\?focus=/);
  });

  test("指标库：?focus= 命中物流指标时切换分区并高亮卡片锚点", async ({ page }) => {
    await page.route("**/api/v1/metric-library", (route) => route.fulfill({ json: LIBRARY }));
    await page.goto("/metric-library?focus=on_time_rate");
    const card = page.locator("article#metric-entry-entry-otr");
    await expect(card).toBeVisible();
    await expect(card).toHaveClass(/ml-metric--focused/);
    await expect(page.getByRole("button", { name: "物流行业指标" })).toHaveClass(/is-active/);
  });

  test("指标库：?focus= 对象不存在时显式提示", async ({ page }) => {
    await page.route("**/api/v1/metric-library", (route) => route.fulfill({ json: LIBRARY }));
    await page.goto("/metric-library?focus=no_such_metric");
    await expect(page.getByText(/未找到指标「no_such_metric」/)).toBeVisible();
    await expect(page.getByText("净资产收益率")).toBeVisible();
  });

  test("报表分析：?report= 初始选中对应财报", async ({ page }) => {
    await page.route("**/api/v1/statements", (route) =>
      route.fulfill({ json: { reports: [REPORT_A, REPORT_B] } }),
    );
    await page.route(`**/api/v1/statements/${REPORT_B.id}`, (route) =>
      route.fulfill({
        json: {
          ...REPORT_B,
          sections: [
            {
              statement_type: "合并利润表",
              items: [
                { item_name: "一、营业总收入", sort_order: 0, value_end: null, value_begin: null, value_current: "74142121.0000", value_prior: null },
              ],
            },
          ],
        },
      }),
    );
    await page.route(`**/api/v1/statements/${REPORT_B.id}/corrections`, (route) =>
      route.fulfill({ json: { corrections: [] } }),
    );
    await page.goto(`/statements?report=${REPORT_B.id}`);
    await expect(page.getByRole("button", { name: /圆通速递/ })).toHaveAttribute("aria-pressed", "true");
    await expect(page.getByText("741.42 亿元").first()).toBeVisible();
  });

  test("报表分析：?report= 不存在时显式提示并回退默认", async ({ page }) => {
    await page.route("**/api/v1/statements", (route) =>
      route.fulfill({ json: { reports: [REPORT_A] } }),
    );
    await page.route(`**/api/v1/statements/${REPORT_A.id}**`, (route) =>
      route.fulfill({
        json: { ...REPORT_A, sections: [] },
      }),
    );
    await page.goto("/statements?report=missing-report-id");
    await expect(page.getByText(/未找到财报「missing-report-id」/)).toBeVisible();
    await expect(page.getByRole("button", { name: /顺丰控股/ })).toHaveAttribute("aria-pressed", "true");
  });

  test("报告中心：?snapshot= 初始选中对应快照", async ({ page }) => {
    await page.route("**/api/v1/publishing/snapshots", (route) =>
      route.fulfill({ json: { snapshots: [SNAPSHOT_1, SNAPSHOT_2] } }),
    );
    await page.route("**/api/v1/publishing/freeze-candidates", (route) =>
      route.fulfill({ json: { candidates: [] } }),
    );
    await page.route("**/api/v1/publishing/snapshots/*/attempts", (route) =>
      route.fulfill({ json: { attempts: [] } }),
    );
    await page.route("**/api/v1/operations/snapshots**", (route) =>
      route.fulfill({ json: { snapshots: [] } }),
    );
    await page.route("**/api/v1/statements", (route) => route.fulfill({ json: { reports: [] } }));
    await page.goto("/reports?snapshot=snap-2");
    await expect(page.getByRole("radio", { name: /2026-07 经营月报/ })).toBeChecked();
  });

  test("报告中心：?snapshot= 不存在时显式提示", async ({ page }) => {
    await page.route("**/api/v1/publishing/snapshots", (route) =>
      route.fulfill({ json: { snapshots: [SNAPSHOT_1] } }),
    );
    await page.route("**/api/v1/publishing/freeze-candidates", (route) =>
      route.fulfill({ json: { candidates: [] } }),
    );
    await page.route("**/api/v1/publishing/snapshots/*/attempts", (route) =>
      route.fulfill({ json: { attempts: [] } }),
    );
    await page.route("**/api/v1/operations/snapshots**", (route) =>
      route.fulfill({ json: { snapshots: [] } }),
    );
    await page.route("**/api/v1/statements", (route) => route.fulfill({ json: { reports: [] } }));
    await page.goto("/reports?snapshot=missing-snapshot");
    await expect(page.getByText(/未找到快照「missing-snapshot」/)).toBeVisible();
  });

  test("数据工作台：?batch= 不在会话中时显式提示", async ({ page }) => {
    await page.goto("/data?batch=batch-not-in-session");
    await expect(page.getByText(/不在当前会话/)).toBeVisible();
    await expect(page.getByText(/batch-not-in-session/)).toBeVisible();
  });
});
