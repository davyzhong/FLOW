import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

// Task 9 证据归档：五态 × 三视口 状态矩阵截图（非门禁，按需生成）。
// 运行：FLOW_STATE_MATRIX_ARCHIVE=1 pnpm exec playwright test e2e/state-matrix-archive.spec.ts
// 产出：docs/assets/screenshots/state-matrix/<route-slug>/<state>-<viewport>.png
// 与索引册 README.md。已由 frontend-states.spec.ts / frontend-responsive.spec.ts
// 门禁覆盖结构合同；本文件只产出人审证据。

const OUT_DIR = path.resolve(__dirname, "../../../docs/assets/screenshots/state-matrix");
const VIEWPORTS = [
  { w: 390, h: 844, label: "390" },
  { w: 1024, h: 768, label: "1024" },
  { w: 1440, h: 900, label: "1440" },
] as const;

const REPORT_ID = "0f1e2d3c-4b5a-6978-8a9b-0c1d2e3f4a5b";

// 数据态夹具与 frontend-responsive.spec.ts 同形（保持单一事实形状，改动须两侧同步）
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
  ],
  report_items: [
    { cas_item: "流动资产合计", ifrs_item: "Current assets", direction: "same" },
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

const DATA_ROUTES = [
  { slug: "statements", route: "/statements", loaded: { statements: { reports: [STATEMENTS_SUMMARY] }, detail: STATEMENTS_DETAIL }, empty: { statements: { reports: [] } } },
  { slug: "reports", route: "/reports", loaded: { publishing: PUBLISHING_SNAPSHOTS }, empty: { publishing: { snapshots: [] } } },
  { slug: "metric-library", route: "/metric-library", loaded: { library: METRIC_LIBRARY }, empty: { library: { ...METRIC_LIBRARY, metrics: [] } } },
  { slug: "investigations", route: "/investigations", loaded: { investigations: FINDINGS }, empty: { investigations: { findings: [] } } },
] as const;

type Json = Record<string, unknown>;

function applyFixtures(page: import("@playwright/test").Page, fixtures: Json) {
  if (fixtures.statements) {
    void page.route("**/api/v1/statements", (r) => r.fulfill({ json: fixtures.statements }));
  }
  if (fixtures.detail) {
    void page.route(`**/api/v1/statements/${REPORT_ID}`, (r) => r.fulfill({ json: fixtures.detail }));
  }
  if (fixtures.publishing) {
    void page.route("**/api/v1/publishing/snapshots", (r) => r.fulfill({ json: fixtures.publishing }));
  }
  if (fixtures.library) {
    void page.route("**/api/v1/metric-library", (r) => r.fulfill({ json: fixtures.library }));
  }
  if (fixtures.investigations) {
    void page.route("**/api/v1/investigations", (r) => r.fulfill({ json: fixtures.investigations }));
  }
}

const API_GLOB = "**/api/v1/**";

async function shoot(
  page: import("@playwright/test").Page,
  slug: string,
  state: string,
  viewport: string,
) {
  const dir = path.join(OUT_DIR, slug);
  fs.mkdirSync(dir, { recursive: true });
  await page.waitForTimeout(350);
  await page.screenshot({
    path: path.join(dir, `${state}-${viewport}.png`),
    fullPage: true,
  });
}

test.describe("state matrix archive", () => {
  test.describe.configure({ mode: "serial" });
  // 双保险：门禁脚本均为显式 spec 清单不会带上本文件；再加环境变量开关防手滑。
  test.skip(!process.env.FLOW_STATE_MATRIX_ARCHIVE, "archive runs on demand only (FLOW_STATE_MATRIX_ARCHIVE=1)");

  for (const vp of VIEWPORTS) {
    for (const entry of DATA_ROUTES) {
      test(`${entry.route} loaded @${vp.label}`, async ({ page }) => {
        await page.setViewportSize({ width: vp.w, height: vp.h });
        applyFixtures(page, entry.loaded as Json);
        await page.goto(entry.route, { waitUntil: "networkidle" });
        await shoot(page, entry.slug, "loaded", vp.label);
      });

      test(`${entry.route} empty @${vp.label}`, async ({ page }) => {
        await page.setViewportSize({ width: vp.w, height: vp.h });
        applyFixtures(page, entry.empty as Json);
        await page.goto(entry.route, { waitUntil: "networkidle" });
        await shoot(page, entry.slug, "empty", vp.label);
      });

      test(`${entry.route} loading @${vp.label}`, async ({ page }) => {
        await page.setViewportSize({ width: vp.w, height: vp.h });
        await page.route(API_GLOB, async () => {
          await new Promise(() => undefined);
        });
        await page.goto(entry.route, { waitUntil: "domcontentloaded" });
        await shoot(page, entry.slug, "loading", vp.label);
      });

      test(`${entry.route} error @${vp.label}`, async ({ page }) => {
        await page.setViewportSize({ width: vp.w, height: vp.h });
        await page.route(API_GLOB, (route) =>
          route.fulfill({
            status: 503,
            contentType: "application/json",
            body: JSON.stringify({ detail: { code: "unavailable", message: "service unavailable" } }),
          }),
        );
        await page.goto(entry.route, { waitUntil: "domcontentloaded" });
        await shoot(page, entry.slug, "error", vp.label);
      });

      test(`${entry.route} forbidden @${vp.label}`, async ({ page }) => {
        await page.setViewportSize({ width: vp.w, height: vp.h });
        await page.route(API_GLOB, (route) =>
          route.fulfill({
            status: 403,
            contentType: "application/json",
            body: JSON.stringify({
              detail: { code: "role_forbidden", message: "授权拒绝：role_forbidden" },
            }),
          }),
        );
        await page.goto(entry.route, { waitUntil: "domcontentloaded" });
        await shoot(page, entry.slug, "forbidden", vp.label);
      });
    }
  }

  test("write index", async () => {
    const rows: string[] = [
      "---",
      "doc_id: FLOW-NAV-STATE-MATRIX-001",
      "title: 前端状态矩阵归档索引（Task 9 证据）",
      "doc_type: navigation",
      "status: current",
      "version: 1.0",
      "created_at: 2026-09-18",
      "updated_at: 2026-09-18",
      "owner: FLOW",
      "applies_to: docs",
      "---",
      "",
      "# 前端状态矩阵归档（Task 9 证据）",
      "",
      "> 由 `apps/web/e2e/state-matrix-archive.spec.ts` 按需生成",
      "（`FLOW_STATE_MATRIX_ARCHIVE=1 pnpm exec playwright test e2e/state-matrix-archive.spec.ts`）。",
      "覆盖数据密集四页 × {正常 / 空 / 加载 / 错误 / 403} × {390 / 1024 / 1440}；",
      "结构合同由 `frontend-states.spec.ts` 与 `frontend-responsive.spec.ts` 门禁自动化，本目录为人审证据。",
      "",
      "| 页面 | 截图目录 |",
      "|---|---|",
    ];
    for (const entry of DATA_ROUTES) {
      rows.push(`| \`${entry.route}\` | [${entry.slug}/](${entry.slug}/) |`);
    }
    rows.push("", `生成时间：${new Date().toISOString()}`, "");
    fs.mkdirSync(OUT_DIR, { recursive: true });
    fs.writeFileSync(path.join(OUT_DIR, "README.md"), rows.join("\n") + "\n");
    expect(fs.existsSync(path.join(OUT_DIR, "README.md"))).toBe(true);
  });
});
