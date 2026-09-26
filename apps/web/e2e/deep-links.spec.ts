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
  source_available: false,
  statement_types: ["合并利润表"],
  line_item_count: 1,
  created_at: "2026-09-06T08:00:00+00:00",
};
const REPORT_B = {
  ...REPORT_A,
  id: "2b3c4d5e-6f70-8192-a3b4-c5d6e7f8091a",
  company_name: "圆通速递",
  source_available: true,
};

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
                { item_name: "一、营业总收入", sort_order: 0, value_end: null, value_begin: null, value_current: "74142121.0000", value_prior: null, page_number: 7, page_anchor: "strong" },
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
    await expect(page.getByRole("link", { name: "打开原文 PDF 第 7 页（行名+数值同页）" })).toHaveAttribute(
      "href",
      `/api/v1/statements/sources/${"a".repeat(64)}/content#page=7`,
    );
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
    await expect(page.getByText(/当前账号下没有可查看的批次/)).toBeVisible();
    await expect(page.getByText(/batch-not-in-session/)).toBeVisible();
  });
});

// 批次二 §3：轻后端补充 —— entry 详情定位、snapshot/run 只读详情消费、
// citations 定位、覆盖矩阵列头 report_id 链接。API 全部 page.route 拦截。
test.describe("深链接收端（批次二）", () => {
  const RUN_DETAIL = {
    id: "run-1",
    metric_snapshot_id: "ms-1",
    import_version_id: "iv-1",
    policy_id: "flow.analysis.logistics.v1",
    policy_set_hash: "a".repeat(64),
    engine_version: "flow-analysis/1",
    fingerprint: "b".repeat(64),
    status: "published",
    created_at: "2026-09-03T09:00:00+08:00",
  };

  const SNAPSHOT_DETAIL = {
    id: "ms-unfrozen",
    batch_id: "batch-9",
    import_version_id: "iv-9",
    as_of_period_id: "period-9",
    as_of_month_key: 202608,
    version: 3,
    engine_version: "flow-metrics/1",
    definition_set_id: "flow.metricdefs.v1",
    definition_set_hash: "a".repeat(64),
    fingerprint: "b".repeat(64),
    status: "published",
    created_at: "2026-09-03T09:00:00+08:00",
  };

  test("指标库：?entry= 端到端定位条目卡片并高亮（§3.1）", async ({ page }) => {
    await page.route("**/api/v1/metric-library", (route) => route.fulfill({ json: LIBRARY }));
    await page.goto("/metric-library?entry=entry-otr");
    const card = page.locator("article#metric-entry-entry-otr");
    await expect(card).toBeVisible();
    await expect(card).toHaveClass(/ml-metric--focused/);
    // entry 指向物流分区条目：分区自动切换
    await expect(page.getByRole("button", { name: "物流行业指标" })).toHaveClass(/is-active/);
  });

  test("指标库：?entry= 对象不存在时显式提示（§3.1）", async ({ page }) => {
    await page.route("**/api/v1/metric-library", (route) => route.fulfill({ json: LIBRARY }));
    await page.goto("/metric-library?entry=entry-ghost");
    await expect(page.getByText(/未找到指标「entry-ghost」/)).toBeVisible();
  });

  test("四问工作台：?run_id= 命中时渲染分析运行身份卡（§3.2）", async ({ page }) => {
    await page.route("**/api/v1/statements", (route) => route.fulfill({ json: { reports: [] } }));
    await page.route("**/api/v1/analytics/analysis-runs/run-1", (route) =>
      route.fulfill({ json: RUN_DETAIL }),
    );
    await page.goto("/analysis?run_id=run-1");
    const card = page.getByTestId("analysis-run-detail");
    await expect(card).toBeVisible();
    await expect(card).toContainText("run-1");
    await expect(card).toContainText("flow-analysis/1");
    await expect(card.getByRole("link", { name: "ms-1" })).toHaveAttribute(
      "href",
      "/reports?snapshot=ms-1",
    );
  });

  test("四问工作台：?run_id= 不存在时显式提示（§3.2）", async ({ page }) => {
    await page.route("**/api/v1/statements", (route) => route.fulfill({ json: { reports: [] } }));
    await page.route("**/api/v1/analytics/analysis-runs/ghost-run", (route) =>
      route.fulfill({
        status: 403,
        json: { detail: { code: "resource_scope_unresolved", message: "授权拒绝" } },
      }),
    );
    await page.goto("/analysis?run_id=ghost-run");
    await expect(page.getByText(/未找到分析运行「ghost-run」/)).toBeVisible();
    await expect(page.getByTestId("analysis-run-detail")).toHaveCount(0);
  });

  test("报告中心：?snapshot= 命中未冻结指标快照时渲染身份卡（§3.2 回退）", async ({ page }) => {
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
    await page.route("**/api/v1/analytics/metric-snapshots/ms-unfrozen", (route) =>
      route.fulfill({ json: SNAPSHOT_DETAIL }),
    );
    await page.goto("/reports?snapshot=ms-unfrozen");
    const card = page.getByTestId("metric-snapshot-detail");
    await expect(card).toBeVisible();
    await expect(card).toContainText("ms-unfrozen");
    await expect(card).toContainText("尚未冻结为报告快照");
    await expect(card.getByRole("link", { name: "batch-9" })).toHaveAttribute(
      "href",
      "/data?batch=batch-9",
    );
    await expect(page.getByText(/未找到快照「ms-unfrozen」/)).toHaveCount(0);
  });

  test("覆盖矩阵：列头携带 report_id 时链接 /statements?report=（§3.4）", async ({ page }) => {
    await page.route("**/api/v1/metric-library", (route) => route.fulfill({ json: LIBRARY }));
    await page.route("**/api/v1/metric-library/coverage**", (route) =>
      route.fulfill({
        json: {
          dataset_id: "flow.p5_metric_coverage.v1",
          title: "P5 真实财报指标覆盖矩阵",
          generator: "scripts/p5_query_facts.py",
          generated_at: "2026-09-14T06:50:46",
          facts_source: "docs/implementation/p5/statement_facts.yaml",
          alias_map: "docs/implementation/p5/item_alias_map_v1.yaml",
          caliber_notes: ["单季数据未年化"],
          snapshots: [
            {
              company: "sf_002352",
              period: "2026Q1",
              unit: "千元",
              computable: 40,
              total: 40,
              report_id: REPORT_A.id,
            },
            {
              company: "alibaba_9988",
              period: "FY2026",
              unit: "百万元",
              computable: 22,
              total: 40,
              report_id: null,
            },
          ],
          metrics: [
            {
              metric_code: "current_ratio",
              name: "流动比率",
              unit: "倍",
              cells: {
                "sf_002352 2026Q1": { display: "1.61", missing: null },
                "alibaba_9988 FY2026": { display: "1.28", missing: null },
              },
            },
          ],
        },
      }),
    );
    await page.goto("/metric-library");
    await page.getByRole("button", { name: "真实财报覆盖" }).click();
    const reportLink = page.getByRole("link", { name: /顺丰控股/ });
    await expect(reportLink).toHaveAttribute("href", `/statements?report=${REPORT_A.id}`);
    // 无 report_id 的列头保持纯文本
    await expect(page.getByRole("link", { name: /阿里巴巴/ })).toHaveCount(0);
  });

  test("Copilot citations：evidence 引用点击页内定位到证据区（§3.3）", async ({ page }) => {
    const findingId = "5535b51a-f81f-5e6d-8ef2-fd4d2552f984";
    const context = {
      identity: {
        finding_id: findingId,
        batch_id: "934072b5-8f89-5f96-a498-c88b26483908",
        metric_snapshot_id: "87d9dfbb-0ac7-5dde-9675-537459961f15",
        analysis_run_id: "639f2271-5816-51d4-8f5d-038b6d98e08c",
      },
      finding: {
        finding_id: findingId,
        finding_type: "fulfillment_cost_increase",
        title: "履约成本增速超过收入增速",
        status: "candidate",
        impact_amount: "-11570000.0000",
        unit: "CNY",
        confidence: "0.9000",
        business_meaning: "运输外包涨价推高履约成本。",
        fact_statement: "履约成本率同比上升 1.6ppt。",
        comparison_basis: "prior_year",
        total_score: "87.000000",
        policy_version: "flow.analysis.logistics.v1",
        created_at: "2026-09-02T02:00:00Z",
      },
      result: null,
      metric: {
        metric_code: "direct_cost",
        metric_name: "履约成本",
        business_definition: "仓储、运输与其他直接成本合计",
        formula: "warehousing_cost + transportation_cost",
        unit: "CNY",
        definition_version: 1,
        engine_version: "flow-analysis/1",
        policy_id: "flow.analysis.logistics.v1",
        policy_set_hash: "448b390877b20090af02f6584e79a1c9796fe5ab0a5c7a6",
      },
      drivers: [
        {
          driver_code: "fuel_price",
          calculation_method: "油耗 × 油价",
          contribution_amount: "-3200000.0000",
          contribution_ratio: "0.2766",
        },
      ],
      evidence: [
        {
          evidence_id: "e2",
          status: "pending",
          evidence_type: "business_confirmation",
          object_type: "source_record",
          object_id: "source-record:1950",
          note: null,
          evidence_digest: null,
        },
      ],
      reviews: [],
      quality_issues: [],
      reconciliations: [],
      conclusion: {
        exists: false,
        verified_facts: "",
        analysis_judgment: "",
        open_questions: "",
        recommendation: "",
      },
      source_records: [],
      eligibility_blockers: ["evidence_pending"],
    };
    await page.route(`**/api/v1/investigations/${findingId}**`, (route) =>
      route.fulfill({ json: context }),
    );
    await page.route(`**/api/v1/copilot/investigations/${findingId}/ask`, (route) =>
      route.fulfill({
        json: {
          interaction_id: "ia-1",
          outcome: "answered",
          context_digest: "d",
          provider: "mock",
          model: "mock",
          template_version: "v1",
          answer: {
            facts: [
              {
                text: "履约成本上升主要由油价驱动。",
                citations: ["evidence:e2", "driver:f-1:fuel_price", "metric:direct_cost"],
              },
            ],
            judgments: [],
            hypotheses: [],
            questions: [],
            degradation: "none",
          },
        },
      }),
    );
    await page.goto(`/investigations/${findingId}`);
    await page.getByRole("button", { name: "生成结构化解读" }).click();
    const citation = page.getByRole("link", { name: "evidence:e2" });
    await expect(citation).toHaveAttribute("href", "#evidence-e2");
    // 证据卡片带锚点 id；driver/metric 引用同样链接化
    await expect(page.locator("article#evidence-e2")).toBeVisible();
    await expect(page.getByRole("link", { name: "driver:f-1:fuel_price" })).toHaveAttribute(
      "href",
      "#driver-fuel_price",
    );
    await expect(page.getByRole("link", { name: "metric:direct_cost" })).toHaveAttribute(
      "href",
      "/metric-library?focus=direct_cost",
    );
    await citation.click();
    await expect(page).toHaveURL(/#evidence-e2$/);
  });
});
