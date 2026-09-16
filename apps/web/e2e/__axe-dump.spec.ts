import { test } from "@playwright/test";
import { AxeBuilder } from "@axe-core/playwright";

const SUMMARY = {
  id: "01a0a41c-4d83-717a-8180-f0964da5d1d1",
  company_name: "顺丰控股",
  stock_code: "002352.SZ",
  period_label: "2026Q1",
  report_kind: "一季报",
  line_item_count: 163,
};
const REPORT_ID = SUMMARY.id;
const DETAIL = {
  id: REPORT_ID,
  company_name: "顺丰控股",
  stock_code: "002352.SZ",
  period_label: "2026Q1",
  report_kind: "一季报",
  unit_note: "人民币千元",
  source_ref: "docs/knowledge-base/02_research/original/p5_samples/sf_002352/SF_2026_Q1_report.pdf",
  sections: [
    {
      statement_type: "合并利润表",
      items: [
        { item_name: "一、营业总收入", sort_order: 0, value_end: null, value_begin: null, value_current: "74142121.0000", value_prior: "69849924.0000" },
        { item_name: "净利润", sort_order: 1, value_end: null, value_begin: null, value_current: "2650843.0000", value_prior: "2017475.0000" },
      ],
    },
  ],
};

test("dump axe violations on /statements", async ({ page }) => {
  await page.route("**/api/v1/statements", (route) => route.fulfill({ json: { reports: [SUMMARY] } }));
  await page.route(`**/api/v1/statements/${REPORT_ID}`, (route) => route.fulfill({ json: DETAIL }));
  await page.goto("http://127.0.0.1:13100/statements");
  await page.getByText("顺丰控股").first().waitFor({ timeout: 10000 }).catch(() => {});
  const results = await new AxeBuilder({ page }).analyze();
  const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  console.log("SERIOUS/CRITICAL VIOLATIONS:", serious.length, "| total violations:", results.violations.length);
  for (const v of serious.slice(0, 6)) {
    console.log(`- [${v.impact}] ${v.id}: ${v.description} | nodes=${v.nodes.length}`);
    for (const n of v.nodes.slice(0, 2)) console.log("    target:", JSON.stringify(n.target), "| html:", n.html.slice(0, 120));
  }
});
