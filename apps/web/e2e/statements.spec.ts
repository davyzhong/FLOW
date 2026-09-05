import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const REPORT_ID = "0f1e2d3c-4b5a-6978-8a9b-0c1d2e3f4a5b";

const SUMMARY = {
  id: REPORT_ID,
  company_name: "顺丰控股",
  stock_code: "002352.SZ",
  report_kind: "一季报",
  period_label: "2026Q1",
  unit_note: "人民币千元",
  source_ref: "p5_samples/sf_002352/SF_2026_Q1_report.pdf",
  source_sha256: "a".repeat(64),
  statement_types: ["合并资产负债表", "合并利润表", "合并现金流量表"],
  line_item_count: 2,
  created_at: "2026-09-06T08:00:00+00:00",
};

const DETAIL = {
  ...SUMMARY,
  sections: [
    {
      statement_type: "合并利润表",
      items: [
        { item_name: "一、营业总收入", sort_order: 0, value_end: null, value_begin: null, value_current: "74142121.0000", value_prior: "62432100.0000" },
        { item_name: "其中：营业成本", sort_order: 1, value_end: null, value_begin: null, value_current: "63956760.0000", value_prior: "54012300.0000" },
        { item_name: "三、营业利润（亏损以“－”号填列）", sort_order: 2, value_end: null, value_begin: null, value_current: "3399319.0000", value_prior: "2900000.0000" },
        { item_name: "四、利润总额（亏损总额以“－”号填列）", sort_order: 3, value_end: null, value_begin: null, value_current: "3473111.0000", value_prior: "2950000.0000" },
        { item_name: "减：所得税费用", sort_order: 4, value_end: null, value_begin: null, value_current: "822268.0000", value_prior: "700000.0000" },
        { item_name: "五、净利润（净亏损以“－”号填列）", sort_order: 5, value_end: null, value_begin: null, value_current: "2650843.0000", value_prior: "2017475.0000" },
      ],
    },
  ],
};

test("报表分析在真实系统内渲染图形与表格（P5 顺丰数据）", async ({ page }) => {
  await page.route("**/api/v1/statements", (route) => route.fulfill({ json: { reports: [SUMMARY] } }));
  await page.route(`**/api/v1/statements/${REPORT_ID}`, (route) => route.fulfill({ json: DETAIL }));
  await page.goto("/statements");
  await expect(page.getByRole("heading", { name: "报表分析" })).toBeVisible();
  await expect(page.getByText("顺丰控股").first()).toBeVisible();
  await expect(page.getByRole("img", { name: /利润形成瀑布图/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: /四表原文/ })).toBeVisible();
  await expect(page.getByTitle("74142121.0000").first()).toBeVisible();
  const results = await new AxeBuilder({ page }).analyze();
  expect(
    results.violations.filter(
      (violation) => violation.impact === "serious" || violation.impact === "critical",
    ),
  ).toEqual([]);
});

test("报表列表失败可重试", async ({ page }) => {
  let shouldSucceed = false;
  await page.route("**/api/v1/statements", (route) =>
    shouldSucceed
      ? route.fulfill({ json: { reports: [SUMMARY] } })
      : route.fulfill({ status: 503, json: { detail: { code: "temporary", message: "临时不可用" } } }),
  );
  await page.route(`**/api/v1/statements/${REPORT_ID}`, (route) => route.fulfill({ json: DETAIL }));
  await page.goto("/statements");
  await expect(page.getByRole("alert")).toBeVisible();
  shouldSucceed = true;
  await page.getByRole("button", { name: "重试" }).click();
  await expect(page.getByText("顺丰控股").first()).toBeVisible();
});

test("空态引导先运行抽取与导入", async ({ page }) => {
  await page.route("**/api/v1/statements", (route) => route.fulfill({ json: { reports: [] } }));
  await page.goto("/statements");
  await expect(page.getByText(/尚无已导入的财报/)).toBeVisible();
});
