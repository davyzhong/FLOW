import { expect, test } from "@playwright/test";

// 指标库治理旅程（C06）：普通用户不改 YAML 完成一次合规修订，并查看治理记录。

const ENTRY_ID = "3f4b9a2c-0000-7000-8000-000000000001";

const LIBRARY = {
  dictionary_id: "flow.metric_dictionary.v1",
  status: "effective",
  decision_ref: "D047",
  created: "2026-09-06",
  standards_scope: ["CAS", "IFRS"],
  domains: { solvency: "偿债能力" },
  report_items: [],
  metrics: [
    {
      metric_code: "current_ratio",
      name: "流动比率",
      domain: "solvency",
      definition: "流动资产对流动负债的保障程度。",
      formula_text: "流动资产 ÷ 流动负债",
      formula: { op: "div", args: ["bs.current_assets", "bs.current_liab"] },
      unit: "倍",
      time_behavior: "point_balance",
      caliber: "教科书标准口径。",
      source_cas: ["流动资产合计", "流动负债合计"],
      source_ifrs: "total current assets / total current liabilities",
      depends_on: [],
      benchmark: "经验参考约 2",
      mpm: false,
      provenance: "research/08 §1",
      collection: "general",
      execution_kind: "facts",
      execution_detail: "报表事实 AST 求值器",
      entry_id: ENTRY_ID,
      status: "effective",
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

test("指标库治理：执行绑定可见、合规修订、治理记录可查", async ({ page }) => {
  const events: unknown[] = [];
  await page.route("**/api/v1/metric-library", (route) =>
    route.fulfill({ json: LIBRARY }),
  );
  await page.route(`**/api/v1/metric-library/entries/${ENTRY_ID}/drafts`, (route) =>
    route.fulfill({
      status: 201,
      json: { id: "d1", metric_code: "current_ratio", version: 2, status: "draft" },
    }),
  );
  await page.route(`**/api/v1/metric-library/entries/d1/activate`, (route) =>
    route.fulfill({ json: { id: "d1", metric_code: "current_ratio", version: 2, status: "effective" } }),
  );
  await page.route("**/api/v1/metric-library/events**", (route) =>
    route.fulfill({
      json: {
        events: events.length
          ? events
          : [
              {
                id: "e1", metric_code: "current_ratio", version: 2, action: "activate",
                operator: "finance.bp", reason: "基准校准", diff: { benchmark: "约 2.2" },
                created_at: "2026-09-07T01:00:00+00:00",
              },
            ],
      },
    }),
  );

  await page.goto("/metric-library");
  await expect(page.getByText("流动比率")).toBeVisible();
  await expect(page.getByText("事实 AST 执行")).toBeVisible();

  await page.getByRole("button", { name: "修订" }).click();
  await page.getByLabel("修订字段").selectOption("benchmark");
  await page.getByLabel("修订内容").fill("约 2.2");
  await page.getByLabel("修订理由").fill("基准校准");
  await page.getByRole("button", { name: "提交修订" }).click();
  await expect(page.getByText(/已合规修订为 v2/)).toBeVisible();

  await page.getByRole("button", { name: "治理记录" }).click();
  await expect(page.getByText("current_ratio", { exact: true })).toBeVisible();
  await expect(page.getByText("基准校准")).toBeVisible();
});
