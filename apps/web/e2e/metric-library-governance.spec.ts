import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const ENTRY_ID = "entry-roe-1";
const LIBRARY = {
  dictionary_id: "flow.metric_dictionary.v1",
  status: "effective",
  decision_ref: "D047",
  created: "2026-09-06",
  standards_scope: ["CAS", "IFRS"],
  domains: { profitability: "盈利能力" },
  report_items: [],
  metrics: [
    {
      metric_code: "roe",
      name: "净资产收益率",
      entry_id: ENTRY_ID,
      status: "effective",
      execution_kind: "facts",
      collection: "general",
      domain: "profitability",
      definition: "净利润与平均净资产之比。",
      formula_text: "净利润 ÷ 平均净资产 × 100%",
      mpm: false,
      aliases: [],
      depends_on: [],
      source_cas: [],
      decompositions: [],
      alternative_calibers: [],
    },
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

test("普通用户无需改 YAML 完成一次合规修订（草稿→事件留痕）", async ({ page }) => {
  const posted: { url: string; body: Record<string, unknown> }[] = [];
  await page.route("**/api/v1/metric-library", (route) => route.fulfill({ json: LIBRARY }));
  await page.route("**/api/v1/metric-library/events*", (route) =>
    route.fulfill({
      json: {
        events: [
          {
            id: "evt-draft-1",
            metric_code: "roe",
            version: 2,
            action: "draft",
            operator: "finance-bp",
            reason: "更新基准值来源",
            created_at: "2026-09-07T08:00:00+00:00",
          },
        ],
      },
    }),
  );
  await page.route("**/api/v1/metric-library/entries/*/drafts", (route) => {
    return route.request().method() === "POST"
      ? route.fulfill({ json: { ok: true } })
      : route.fulfill({ status: 404, json: { detail: { code: "not_found", message: "?" } } });
  });

  await page.goto("/metric-library");
  await expect(page.getByText("净资产收益率")).toBeVisible();
  await page.getByRole("button", { name: "治理记录" }).click();

  await page.getByLabel("操作者").fill("finance-bp");
  await page.getByLabel("理由").fill("更新基准值来源");
  await page.getByLabel("变更内容 JSON").fill('{"benchmark": "国资委 2025"}');
  page.on("request", (request) => {
    if (request.url().includes("/drafts") && request.method() === "POST") {
      posted.push({ url: request.url(), body: request.postDataJSON() as Record<string, unknown> });
    }
  });
  await page.getByRole("button", { name: "创建草稿" }).click();

  await expect(page.getByText(/已创建草稿：roe/)).toBeVisible();
  await expect(posted).toHaveLength(1);
  expect(posted[0].body).toMatchObject({
    operator: "finance-bp",
    reason: "更新基准值来源",
    changes: { benchmark: "国资委 2025" },
  });
  // 事件流呈现草稿审计行
  await expect(page.getByText("finance-bp").first()).toBeVisible();

  const results = await new AxeBuilder({ page }).analyze();
  expect(
    results.violations.filter(
      (violation) => violation.impact === "serious" || violation.impact === "critical",
    ),
  ).toEqual([]);
});

test("必填缺失时行内报错且不发请求", async ({ page }) => {
  let drafted = 0;
  await page.route("**/api/v1/metric-library", (route) => route.fulfill({ json: LIBRARY }));
  await page.route("**/api/v1/metric-library/events*", (route) => route.fulfill({ json: { events: [] } }));
  await page.route("**/api/v1/metric-library/entries/*/drafts", (route) => {
    if (route.request().method() === "POST") drafted += 1;
    return route.fulfill({ json: { ok: true } });
  });

  await page.goto("/metric-library");
  await page.getByRole("button", { name: "治理记录" }).click();
  await page.getByRole("button", { name: "创建草稿" }).click();

  await expect(page.getByRole("alert").first()).toContainText("操作者与理由均为必填");
  expect(drafted).toBe(0);
});
