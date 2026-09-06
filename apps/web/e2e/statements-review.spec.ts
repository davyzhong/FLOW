import { expect, test } from "@playwright/test";

const REPORT_ID = "0f1e2d3c-4b5a-6978-8a9b-0c1d2e3f4a5b";

const SUMMARY = {
  id: REPORT_ID,
  company_name: "顺丰控股",
  stock_code: "002352.SZ",
  report_kind: "一季报",
  period_label: "2026Q1",
  version: 1,
  status: "draft",
  unit_note: "人民币千元",
  source_ref: "p5_samples/sf_002352/SF_2026_Q1_report.pdf",
  source_sha256: "a".repeat(64),
  statement_types: ["合并利润表"],
  line_item_count: 1,
  created_at: "2026-09-06T08:00:00+00:00",
};

const DETAIL = {
  ...SUMMARY,
  sections: [
    {
      statement_type: "合并利润表",
      items: [
        { item_name: "一、营业总收入", sort_order: 0, value_end: null, value_begin: null, value_current: "74142121.0000", value_prior: "62432100.0000" },
      ],
    },
  ],
};

test("报表分析复核：更正留痕、发布门禁反馈", async ({ page }) => {
  const corrections: unknown[] = [];
  await page.route("**/api/v1/statements", (route) =>
    route.fulfill({ json: { reports: [SUMMARY] } }),
  );
  await page.route(`**/api/v1/statements/${REPORT_ID}/corrections`, (route) => {
    if (route.request().method() === "POST") {
      corrections.push(route.request().postDataJSON());
      return route.fulfill({
        status: 201,
        json: {
          id: "c1", report_id: REPORT_ID,
          statement_type: "合并利润表", item_name: "一、营业总收入",
          column_key: "value_current", old_value: "74142121.0000", new_value: "74142122.0000",
          reason: "复核修正", operator: "finance.bp",
          created_at: "2026-09-06T09:00:00+00:00",
        },
      });
    }
    return route.fulfill({
      json: {
        corrections: corrections.map(() => ({
          id: "c1", report_id: REPORT_ID,
          statement_type: "合并利润表", item_name: "一、营业总收入",
          column_key: "value_current", old_value: "74142121.0000", new_value: "74142122.0000",
          reason: "复核修正", operator: "finance.bp",
          created_at: "2026-09-06T09:00:00+00:00",
        })),
      },
    });
  });
  await page.route(`**/api/v1/statements/${REPORT_ID}/publish`, (route) =>
    route.fulfill({
      status: 409,
      json: { detail: { code: "critical_imbalance", message: "存在关键勾稽不平衡，阻断发布：演示" } },
    }),
  );
  await page.route(`**/api/v1/statements/${REPORT_ID}`, (route) =>
    route.fulfill({ json: DETAIL }),
  );

  await page.goto("/statements");
  await expect(page.getByText("草稿（可更正）")).toBeVisible();

  await page.getByLabel("报表").selectOption("合并利润表");
  await page.getByLabel("行项目").selectOption("一、营业总收入");
  await page.getByLabel("列").selectOption("value_current");
  await page.getByLabel("更正值").fill("74142122");
  await page.getByLabel("更正原因").fill("复核修正");
  await page.getByRole("button", { name: "记录更正" }).click();
  await expect(page.getByText("更正已记录")).toBeVisible();
  await expect(page.getByText(/74142121.0000 → 74142122.0000/)).toBeVisible();

  await page.getByRole("button", { name: "复核通过并发布" }).click();
  await expect(page.getByText(/发布被阻断（critical_imbalance）/)).toBeVisible();

  expect(corrections).toHaveLength(1);
});
