import { createHash } from "node:crypto";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";
import type {
  DashboardResponse,
  FreezeCandidate,
  MetricCoverage,
  MetricGovernanceEventList,
  MetricLibrary,
  OperationsOverview,
  OperationsSnapshot,
  PublicOperatingPeriodList,
  PublishingAttempt,
  PublishingSnapshot,
  StatementReportDetail,
  StatementReportList,
  WorkbenchResponse,
} from "../lib/api/client";

// 大麦 synthetic 演示全旅程 E2E（Task C2）：
// 真实隔离栈（compose.damai-isolated）+ 真实 seed + 真实浏览器，无 page mock。
// 覆盖八个页面与两条状态变更旅程：
//   /                驾驶舱总览 + 组织/客户群/产品/区域四粒度筛选
//   /operations      经营概览（产品表 + 客户群×产品毛利矩阵）
//   /statements      公开财报列表与大麦详情（DAMAI.SYN）
//   /analysis        四问分析工作台载入大麦财报
//   /metric-library  指标库「大麦演示」覆盖 tab
//   /investigations  收入增长 Finding 复核 → 批准签发
//   /reports         经营报告产物生成 + 下载 SHA-256 对账
//   /data            上传大麦工作簿：映射/校验/警告确认/发布（最后执行，会追加新批次）
// 注意：测试按声明顺序串行执行（workers=1），顺序即语义。

const DAMAI_ORG = "国际供应链事业部";
const DAMAI_SEGMENT = "电商平台客户";
const DAMAI_PRODUCT = "跨境标准包裹";
const DAMAI_REGION = "华东区";

const COVERAGE_COMPANY_NAMES: Record<string, string> = {
  alibaba_9988: "阿里巴巴",
  cainiao: "菜鸟",
  damai_syn: "大麦物流",
  jd_logistics_2618: "京东物流",
  sf_002352: "顺丰控股",
  tencent_0700: "腾讯控股",
};

async function expectMetricCoverageMatchesApi(page: Page, coverage: MetricCoverage) {
  const matrix = page.locator("section[aria-label='指标覆盖矩阵']");
  const synthetic = coverage.synthetic === true;
  await expect(matrix.getByRole("heading", { name: "指标覆盖矩阵" })).toBeVisible();
  await expect(matrix).toContainText(synthetic ? "synthetic 演示 · 大麦物流" : "真实财报 · 反向解析");
  await expect(matrix).toContainText(coverage.title);
  await expect(matrix).toContainText(coverage.dataset_id);
  await expect(matrix).toContainText(coverage.facts_source);
  await expect(matrix).toContainText(coverage.alias_map);
  await expect(matrix).toContainText(coverage.generator);
  await expect(matrix.locator(".ml-coverage__notes li")).toHaveText(coverage.caliber_notes);

  const table = matrix.locator("table.ml-cov");
  const headers = table.locator("thead tr th");
  await expect(headers).toHaveCount(coverage.snapshots.length + 1);
  const totalCells = coverage.snapshots.reduce((sum, snapshot) => sum + snapshot.total, 0);
  const computableCells = coverage.snapshots.reduce((sum, snapshot) => sum + snapshot.computable, 0);
  const companyCount = new Set(coverage.snapshots.map((snapshot) => snapshot.company)).size;
  const kpiCards = matrix.getByRole("list", { name: "覆盖矩阵速览" }).locator(".ml-kpi");
  const kpis = kpiCards.locator(".ml-kpi__value");
  await expect(kpis.nth(0)).toContainText(String(coverage.snapshots.length));
  await expect(kpiCards.nth(0).locator(".ml-kpi__foot")).toContainText(`${companyCount} 家公司`);
  await expect(kpis.nth(1)).toContainText(String(coverage.metrics.length));
  await expect(kpis.nth(2)).toContainText(String(Math.round((computableCells / totalCells) * 100)));
  await expect(kpiCards.nth(2).locator(".ml-kpi__foot")).toContainText(`${computableCells}/${totalCells}`);
  const best = [...coverage.snapshots].sort(
    (left, right) => right.computable / right.total - left.computable / left.total,
  )[0];
  if (best) {
    await expect(kpis.nth(3)).toContainText(`${best.computable}/${best.total}`);
    await expect(kpiCards.nth(3).locator(".ml-kpi__foot")).toContainText(best.period);
    await expect(kpiCards.nth(3).locator(".ml-kpi__foot")).toContainText(
      COVERAGE_COMPANY_NAMES[best.company] ?? best.company,
    );
  }
  await expect(kpis.nth(4)).toContainText(String(totalCells - computableCells));

  for (const [snapshotIndex, snapshot] of coverage.snapshots.entries()) {
    const header = headers.nth(snapshotIndex + 1);
    const companyName = COVERAGE_COMPANY_NAMES[snapshot.company] ?? snapshot.company;
    await expect(header).toContainText(companyName);
    await expect(header).toContainText(snapshot.period);
    await expect(header).toContainText(`${snapshot.computable}/${snapshot.total}`);
    if (snapshot.report_id) {
      await expect(header.getByRole("link")).toHaveAttribute(
        "href",
        `/statements?report=${encodeURIComponent(snapshot.report_id)}`,
      );
    } else {
      await expect(header.getByRole("link")).toHaveCount(0);
    }
  }

  const rows = table.locator("tbody tr");
  await expect(rows).toHaveCount(coverage.metrics.length + 1);
  for (const [metricIndex, metric] of coverage.metrics.entries()) {
    const row = rows.nth(metricIndex);
    await expect(row.locator("th[scope='row']")).toContainText(metric.metric_code);
    await expect(row.locator("th[scope='row']")).toContainText(metric.name);
    if (metric.unit) await expect(row.locator("th[scope='row']")).toContainText(metric.unit);
    for (const [snapshotIndex, snapshot] of coverage.snapshots.entries()) {
      const cell = metric.cells[`${snapshot.company} ${snapshot.period}`];
      const rendered = row.locator("td").nth(snapshotIndex);
      if (!cell || cell.display === null || cell.display === undefined) {
        await expect(rendered).toContainText(`缺 ${cell?.missing ?? "—"}`);
        if (cell?.missing) await expect(rendered).toHaveAttribute("title", `缺口：${cell.missing}`);
      } else {
        await expect(rendered).toHaveText(cell.display);
      }
    }
  }
}

const METRIC_TIME_BEHAVIOR_LABELS: Record<string, string> = {
  period_flow: "期间流量",
  point_balance: "时点余额",
  average_balance: "平均余额",
};

async function expectMetricCardsMatchApi(
  page: Page,
  library: MetricLibrary,
  collection: "general" | "logistics",
) {
  const metrics = library.metrics.filter((metric) => metric.collection === collection);
  const cards = page.locator(".ml-metric");
  await expect(cards).toHaveCount(metrics.length);
  for (const [index, metric] of metrics.entries()) {
    const card = cards.nth(index);
    await expect(card.locator(".ml-metric__head strong")).toHaveText(metric.name);
    await expect(card.locator(".ml-metric__head code")).toHaveText(metric.metric_code);
    await expect(card.locator(".ml-metric__head")).toContainText(
      library.domains[metric.domain] ?? metric.domain,
    );
    await expect(card.locator(".ml-metric__head")).toContainText(
      metric.tier === "core" ? "常用" : "专业",
    );
    if (metric.mpm) await expect(card.locator(".ml-chip--mpm")).toHaveText("MPM");
    await expect(card.locator(".ml-metric__definition")).toHaveText(metric.definition);
    const detailRows = card.locator(".ml-metric__grid > div");
    await expect(detailRows.nth(0)).toContainText("公式");
    await expect(detailRows.nth(0)).toContainText(`${metric.formula_text}${metric.unit ? `（${metric.unit}）` : ""}`);
    await expect(detailRows.nth(1)).toContainText(
      metric.time_behavior ? METRIC_TIME_BEHAVIOR_LABELS[metric.time_behavior] ?? metric.time_behavior : "—",
    );
    await expect(detailRows.nth(2)).toContainText(metric.source_cas.length ? metric.source_cas.join("、") : "—");
    await expect(detailRows.nth(3)).toContainText(metric.source_ifrs ?? "—");
    for (const value of [
      metric.caliber,
      metric.benchmark,
      metric.provenance,
      metric.execution_detail,
      ...metric.depends_on,
      ...(metric.analysis_dimensions ?? []),
      ...(metric.decompositions ?? []).map((item) => `${item.name}：${item.formula_text}`),
    ]) {
      if (value) await expect(card).toContainText(value);
    }
    if (metric.mpm && metric.reconciliation) {
      await expect(card).toContainText(`MPM 调节要求：${metric.reconciliation}`);
    }
    if (metric.execution_kind) await expect(card.locator(".ml-metric__foot")).toContainText(metric.execution_kind === "engine" ? "引擎执行" : metric.execution_kind === "facts" ? "事实 AST 执行" : "叙述定义");
    if (metric.migrates_from) await expect(card.locator(".ml-metric__foot")).toContainText(`迁移自 ${metric.migrates_from}`);
    if (metric.entry_id) {
      await expect(card.locator(".ml-metric__foot").getByRole("button", { name: "修订" })).toBeVisible();
    }
  }
}

async function expectSupportingSectionsMatchApi(
  page: Page,
  library: MetricLibrary,
  section: "industry" | "relations" | "mapping" | "accounting",
) {
  if (section === "industry") {
  const packs = page.locator(".ml-pack");
  await expect(packs).toHaveCount(library.industry_reference_packs.length);
  for (const [index, pack] of library.industry_reference_packs.entries()) {
    const card = packs.nth(index);
    await expect(card).toContainText(pack.name);
    await expect(card).toContainText(pack.industry_id);
    await expect(card).toContainText(pack.note);
    await expect(card).toContainText(pack.provenance);
    for (const [code, text] of Object.entries(pack.financial_reference)) {
      await expect(card).toContainText(code);
      await expect(card).toContainText(text);
    }
    for (const indicator of pack.ops_indicators) {
      await expect(card).toContainText(indicator.code);
      await expect(card).toContainText(indicator.name);
      await expect(card).toContainText(indicator.meaning);
    }
  }
  }

  if (section === "relations") {
  const relations = page.locator(".ml-relation");
  await expect(relations).toHaveCount(library.relations.length);
  for (const [index, relation] of library.relations.entries()) {
    const card = relations.nth(index);
    await expect(card).toContainText(relation.name);
    await expect(card).toContainText(relation.relation);
    await expect(card.locator(".ml-relation__expr")).toHaveText(relation.expression);
    await expect(card).toContainText(relation.note);
    if (relation.provenance) await expect(card).toContainText(relation.provenance);
  }
  }

  if (section === "mapping") {
  const mappings = page.locator("table.flow-table tbody tr");
  await expect(mappings).toHaveCount(library.report_items.length);
  for (const [index, item] of library.report_items.entries()) {
    const cells = mappings.nth(index).locator("td");
    await expect(cells).toHaveText([item.item_id, item.cas, item.ifrs]);
  }
  }

  if (section === "accounting") {
  const accounts = library.accounting.accounts;
  const renderedAccounts = page.locator(".ml-account");
  await expect(renderedAccounts).toHaveCount(accounts.length);
  for (const [index, account] of accounts.entries()) {
    const row = renderedAccounts.nth(index);
    await expect(row.locator("code")).toHaveText(account.code);
    await expect(row.locator("strong")).toHaveText(account.name);
    await expect(row.locator(".ml-account__tags")).toContainText(account.category);
    await expect(row.locator(".ml-account__tags")).toContainText(account.balance_side);
    if (account.status !== "current") await expect(row.locator(".ml-account__tags")).toContainText(account.status);
  }

  const standards = page.locator(".ml-standards li");
  await expect(standards).toHaveCount(library.accounting.standards.length);
  for (const [index, standard] of library.accounting.standards.entries()) {
    const row = standards.nth(index);
    await expect(row).toContainText(standard.id);
    await expect(row).toContainText(standard.name);
    if (standard.issuer) await expect(row).toContainText(standard.issuer);
    if (standard.note) await expect(row).toContainText(standard.note);
  }

  const templates = page.locator("details.ml-entry");
  await expect(templates).toHaveCount(library.accounting.entry_templates.length);
  for (const [index, template] of library.accounting.entry_templates.entries()) {
    const disclosure = templates.nth(index);
    await disclosure.locator("summary").click();
    await expect(disclosure).toContainText(template.scenario);
    await expect(disclosure).toContainText(template.template_id);
    if (template.business_context) await expect(disclosure).toContainText(template.business_context);
    const lines = disclosure.locator("table tbody tr");
    await expect(lines).toHaveCount(template.lines.length);
    for (const [lineIndex, line] of template.lines.entries()) {
      await expect(lines.nth(lineIndex).locator("td")).toHaveText([line.direction, line.account, line.amount_rule]);
    }
    if (template.standard_ref) await expect(disclosure).toContainText(template.standard_ref);
    for (const code of template.related_metrics) await expect(disclosure).toContainText(code);
  }
  }
}

async function expectDashboardCardsMatch(page: Page, response: DashboardResponse) {
  const cards = page.getByTestId("metric-card");
  await expect(cards).toHaveCount(response.metric_cards.length);
  for (const metric of response.metric_cards) {
    const uiCard = cards.filter({ hasText: metric.title });
    await expect(uiCard).toHaveCount(1);
    await expect(uiCard.locator(".metric-card__value")).toHaveText(metric.primary.display_value);
    const expectedComparisons = [metric.budget, metric.yoy, metric.ytd_budget];
    const uiComparisons = uiCard.locator(".metric-comparison");
    await expect(uiComparisons).toHaveCount(expectedComparisons.length);
    for (const [index, expected] of expectedComparisons.entries()) {
      const actual = uiComparisons.nth(index);
      await expect(actual).toHaveAttribute("data-status", expected.status);
      await expect(actual.locator(".metric-comparison__value")).toContainText(expected.display_value);
    }
  }
}

function formatStatementValue(value: string, unitNote: string): string {
  const scale = unitNote.includes("千元") ? 1e5 : unitNote.includes("百万") ? 1e2 : 1;
  return (Number(value) / scale)
    .toFixed(2)
    .replace(/\.00$/, "")
    .replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

const OPERATIONS_PERCENT_METRICS = new Set([
  "gross_margin",
  "net_margin",
  "debt_asset_ratio",
  "revenue_growth",
  "net_profit_growth",
  "operating_profit_growth",
  "revenue_yoy",
  "net_profit_yoy",
  "segment_revenue_yoy",
  "adjusted_net_profit_margin",
  "adjusted_ebitda_margin",
  "business_line_share.china_logistics",
  "business_line_share.international_logistics",
  "business_line_share.technology_and_other_services",
  "dupont_three_factor",
]);

const OPERATIONS_MULTIPLE_METRICS = new Set([
  "current_ratio",
  "ocf_to_net_profit",
  "inventory_turnover",
  "ar_turnover",
  "ap_turnover",
  "current_asset_turnover",
]);

const OPERATIONS_EXACT_PRECISION_METRICS = new Set([
  "international_parcels",
  "china_orders_fulfilled",
  "adjusted_net_profit",
  "adjusted_ebitda",
]);

function formatOperationsMetric(entryId: string, value: string): string {
  if (OPERATIONS_EXACT_PRECISION_METRICS.has(entryId)) return value;
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) return value;
  const isRatio =
    OPERATIONS_PERCENT_METRICS.has(entryId) ||
    OPERATIONS_MULTIPLE_METRICS.has(entryId) ||
    entryId === "dso_days";
  const formatted = new Intl.NumberFormat("zh-CN", {
    minimumFractionDigits: isRatio ? 2 : 0,
    maximumFractionDigits: 2,
  }).format(OPERATIONS_PERCENT_METRICS.has(entryId) ? numericValue * 100 : numericValue);
  if (OPERATIONS_PERCENT_METRICS.has(entryId)) return `${formatted}%`;
  if (OPERATIONS_MULTIPLE_METRICS.has(entryId)) {
    return `${formatted}${entryId === "current_ratio" || entryId === "ocf_to_net_profit" ? " 倍" : " 次"}`;
  }
  if (entryId === "dso_days") return `${formatted} 天`;
  return formatted;
}

async function expectOperationsOverviewMatchesApi(
  page: Page,
  overview: OperationsOverview,
) {
  await expect(page.getByRole("heading", { name: "六主题概览" })).toBeVisible();
  await expect(page.locator(".ops-overview__theme")).toHaveCount(overview.themes.length);
  for (const theme of overview.themes) {
    const section = page.locator(`[aria-labelledby="ops-theme-${theme.theme_id}"]`);
    await expect(section.locator("h3")).toHaveText(theme.name);
    await expect(section).toHaveAttribute("data-status", theme.status);
    if (theme.status === "not_applicable") {
      expect(theme.reason).toBeTruthy();
      await expect(section).toContainText(theme.reason!);
      continue;
    }

    for (const metric of theme.metrics) {
      const metricLink = section.getByRole("link", { name: metric.name, exact: true });
      await expect(metricLink).toHaveAttribute(
        "href",
        `/metric-library?entry=${encodeURIComponent(metric.entry_id)}`,
      );
      const row = metricLink.locator("xpath=..");
      if (metric.status === "computed") {
        expect(metric.value).not.toBeNull();
        const exactValue = row.locator(`strong[title="精确值：${metric.value}"]`);
        await expect(exactValue).toHaveText(formatOperationsMetric(metric.entry_id, metric.value!));
        if (metric.source === "operating_fact") {
          await expect(row).toContainText(metric.period_label);
          await expect(row).toContainText(metric.source_ref);
          if (metric.source_page) await expect(row).toContainText(`第 ${metric.source_page} 页`);
          if (metric.source_sha256) await expect(row).toContainText(`${metric.source_sha256.slice(0, 16)}…`);
        }
      } else {
        expect(metric.reason).toBeTruthy();
        await expect(row).toContainText(`暂不可算（${metric.reason}）`);
      }
    }
  }

  expect(overview.management_watch.length).toBeLessThanOrEqual(3);
  for (const watch of overview.management_watch) {
    const row = page.locator(".ops-overview__watch li").filter({ hasText: watch.message });
    await expect(row).toHaveAttribute("data-direction", watch.direction);
    if (watch.metric_code) {
      await expect(row.getByRole("link")).toHaveAttribute(
        "href",
        `/metric-library?focus=${encodeURIComponent(watch.metric_code)}`,
      );
    }
  }
}

test("dashboard renders damai overview with four grain filters", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Finance BP 经营驾驶舱" }),
  ).toBeVisible();
  const cards = page.getByTestId("metric-card");
  await expect(cards.first()).toBeVisible({ timeout: 30_000 });
  expect(await cards.count()).toBeGreaterThan(0);

  // 四粒度筛选器全部来自大麦维度表（combobox 角色避免与毛利矩阵表同名冲突）
  await expect(
    page.getByRole("combobox", { name: "组织" }).locator("option", { hasText: DAMAI_ORG }),
  ).toHaveCount(1);
  await expect(
    page.getByRole("combobox", { name: "客户群" }).locator("option", { hasText: DAMAI_SEGMENT }),
  ).toHaveCount(1);
  await expect(
    page.getByRole("combobox", { name: "物流产品" }).locator("option", { hasText: DAMAI_PRODUCT }),
  ).toHaveCount(1);
  await expect(
    page.getByRole("combobox", { name: "区域" }).locator("option", { hasText: DAMAI_REGION }),
  ).toHaveCount(1);

  // 真实操作本月/YTD和四类筛选器，逐次检查控件状态及URL；最后对账组合参数 API/UI。
  const period = page.getByRole("combobox", { name: "期间" });
  await period.selectOption("ytd");
  await expect(period).toHaveValue("ytd");
  await expect(page).toHaveURL(/period_view=ytd/);
  const dimensionParams = [
    ["组织", "organization_id"],
    ["客户群", "customer_segment_id"],
    ["物流产品", "logistics_product_id"],
    ["区域", "region_id"],
  ] as const;
  for (const [label, param] of dimensionParams) {
    const control = page.getByRole("combobox", { name: label });
    const firstOption = control.locator("option").nth(1);
    const value = await firstOption.getAttribute("value");
    expect(value, `${label}至少有一个实际选项`).toBeTruthy();
    await control.selectOption(value!);
    await expect(control).toHaveValue(value!);
    await expect(page).toHaveURL(new RegExp(`${param}=`));
    const query = new URL(page.url()).searchParams.toString();
    const filteredResponse = await page.request.get(`/api/v1/dashboard/overview?${query}`);
    expect(filteredResponse.ok()).toBeTruthy();
    const filtered = (await filteredResponse.json()) as DashboardResponse;
    expect(filtered.active_filters[param]).toBe(value);
    expect(filtered.active_filters.period_view).toBe("ytd");
    await expectDashboardCardsMatch(page, filtered);
    await control.selectOption("");
    await expect(control).toHaveValue("");
  }
});

test("dashboard API serves customer-grain overview", async ({ page }) => {
  await page.goto("/");
  const cards = page.getByTestId("metric-card");
  await expect(cards.first()).toBeVisible({ timeout: 30_000 });

  const overview = await page.request.get("/api/v1/dashboard/overview");
  expect(overview.ok()).toBeTruthy();
  const body = (await overview.json()) as DashboardResponse;
  // OCF actual 已进入财务事实与指标快照，应返回真实可用值。
  expect(["ready", "degraded"]).toContain(body.state);
  const ocfCard = body.metric_cards.find((card) => card.metric_code === "operating_cash_flow");
  expect(ocfCard?.primary.status).toBe("available");
  expect(ocfCard?.primary.exact_value).not.toBeNull();
  expect(body.trends.status).toBe("complete");
  expect(body.trends.coverage_count).toBe(12);
  expect(body.trends.points).toHaveLength(12);
  for (const point of body.trends.points) {
    expect(point.operating_cash_flow.status).toBe("available");
    expect(point.operating_cash_flow.exact_value).not.toBeNull();
  }

  // 展开趋势明细，将12个月×4列页面值逐项对齐到同一 API 响应。
  const trendDetails = page.locator(".trend-details");
  await trendDetails.locator("summary").click();
  const trendRows = trendDetails.locator("tbody tr");
  await expect(trendRows).toHaveCount(body.trends.points.length);
  for (const [index, point] of body.trends.points.entries()) {
    const cells = trendRows.nth(index).locator("th, td");
    await expect(cells).toHaveCount(5);
    await expect(cells.nth(0)).toHaveText(point.month);
    await expect(cells.nth(1)).toHaveText(point.revenue.display_value);
    await expect(cells.nth(2)).toHaveText(point.operating_profit.display_value);
    await expect(cells.nth(3)).toHaveText(point.operating_cash_flow.display_value);
    await expect(cells.nth(4)).toHaveText(point.gross_margin.display_value);
  }

  // 源事实只覆盖10种客群×产品组合；不补零，并优先展示覆盖更高的预算比较。
  expect(body.margin_matrix.cells).toHaveLength(32);
  expect(body.margin_matrix.status).toBe("degraded");
  expect(body.margin_matrix.comparison_label).toBe("预算");
  expect(body.margin_matrix.cells.filter((cell) => cell.actual_margin.status === "available")).toHaveLength(10);
  expect(body.margin_matrix.cells.filter((cell) => cell.comparison.status === "available")).toHaveLength(10);
  for (const cell of body.margin_matrix.cells) {
    if (cell.actual_margin.status !== "available") {
      expect(cell.actual_margin.exact_value).toBeNull();
    }
  }

  // API→UI 逐卡对账：不仅确认数据存在，还保证页面没有漏卡、错值或状态漂移。
  await expectDashboardCardsMatch(page, body);

  // 矩阵全部行列和格值都与同一响应对账。不可用的实际值必须仍显示破折号，不能补成0。
  const matrixUi = page.getByRole("table", { name: "客户群与产品毛利矩阵" });
  await expect(matrixUi).toBeVisible();
  const matrixRows = matrixUi.locator("tbody tr");
  await expect(matrixRows).toHaveCount(body.margin_matrix.rows.length);
  for (const [rowIndex, row] of body.margin_matrix.rows.entries()) {
    const uiRow = matrixRows.nth(rowIndex);
    await expect(uiRow.locator("th").first()).toHaveText(row.name);
    const uiCells = uiRow.locator("td");
    await expect(uiCells).toHaveCount(body.margin_matrix.columns.length);
    for (const [columnIndex, column] of body.margin_matrix.columns.entries()) {
      const expected = body.margin_matrix.cells.find(
        (cell) =>
          cell.customer_segment_id === row.id &&
          cell.logistics_product_id === column.id,
      );
      const uiCell = uiCells.nth(columnIndex);
      await expect(uiCell.locator("strong")).toHaveText(
        expected?.actual_margin.display_value ?? "—",
      );
      await expect(uiCell.locator("small")).toHaveText(
        expected?.comparison.display_value ?? "—",
      );
    }
  }

  // 产品经营表现表的八列数据同样必须逐产品对应 API，避免只校验标题/行数。
  const productsTable = page.getByRole("table", { name: "产品经营表现" });
  await expect(productsTable).toBeVisible();
  const productRows = productsTable.locator("tbody tr");
  await expect(productRows).toHaveCount(body.product_table.rows.length);
  for (const [rowIndex, product] of body.product_table.rows.entries()) {
    const cells = productRows.nth(rowIndex).locator("th, td");
    await expect(cells).toHaveCount(8);
    await expect(cells.nth(0).locator("span")).toHaveText(product.name);
    const expectedValues = [
      product.revenue.display_value,
      product.revenue_comparison.display_value,
      product.orders.display_value,
      product.orders_comparison.display_value,
      product.gross_margin.display_value,
      product.gross_margin_comparison.display_value,
      product.fulfillment_cost_rate.display_value,
    ];
    for (const [index, expected] of expectedValues.entries()) {
      await expect(cells.nth(index + 1)).toHaveText(expected);
    }
  }

  const dims = Object.fromEntries(
    body.filter_options.dimensions.map((d) => [d.dimension, d.options]),
  );
  for (const dim of ["organization", "customer_segment", "logistics_product", "region"]) {
    expect(dims[dim]?.length ?? 0, `维度 ${dim} 应有选项`).toBeGreaterThan(0);
  }

  // customer 粒度：只通过 metric API 验证，不宣称 UI 具备不存在的下钻
  const segment = dims.customer_segment[0];
  const filtered = await page.request.get(
    `/api/v1/dashboard/overview?customer_segment_id=${segment.id}`,
  );
  expect(filtered.ok()).toBeTruthy();
  const filteredBody = (await filtered.json()) as {
    state: string;
    active_filters: { customer_segment_id: string | null };
    context: { batch_id: string };
    metric_cards: { metric_code: string; primary: { status: string; exact_value: string | null } }[];
  };
  // 客户群粒度下部分指标（利润/OCF）按合同不可用，状态允许 degraded
  expect(["ready", "degraded"]).toContain(filteredBody.state);
  expect(filteredBody.active_filters.customer_segment_id).toBe(segment.id);
  expect(filteredBody.context.batch_id).toBe(body.context.batch_id);

  // 同一快照下，客户群粒度收入必为全集的真子集
  const totalRevenue = body.metric_cards.find((card) => card.metric_code === "revenue");
  const segmentRevenue = filteredBody.metric_cards.find((card) => card.metric_code === "revenue");
  expect(totalRevenue?.primary.status).toBe("available");
  expect(segmentRevenue?.primary.status).toBe("available");
  const totalValue = Number(totalRevenue?.primary.exact_value);
  const segmentValue = Number(segmentRevenue?.primary.exact_value);
  expect(segmentValue).toBeGreaterThan(0);
  expect(segmentValue).toBeLessThan(totalValue);
});

test("operations overview renders damai six-theme analysis", async ({ page }) => {
  test.setTimeout(120_000);
  const initialOverviewResponse = page.waitForResponse((response) => {
    const path = new URL(response.url()).pathname;
    return /^\/api\/v1\/operations\/(overview\/[^/]+|public\/[^/]+\/[^/]+)$/.test(path);
  });
  await page.goto("/operations");
  const initialResponse = await initialOverviewResponse;
  expect(initialResponse.ok()).toBeTruthy();
  const initialOverview = (await initialResponse.json()) as OperationsOverview;
  const initialPath = new URL(initialResponse.url()).pathname;
  // next dev 冷编译路由需要时间，首个断言放宽
  await expect(page.getByRole("heading", { name: "经营分析概览" })).toBeVisible({ timeout: 60_000 });
  const select = page.locator("#operations-context");
  const reportsResponse = await page.request.get("/api/v1/statements");
  expect(reportsResponse.ok()).toBeTruthy();
  const reportList = (await reportsResponse.json()) as StatementReportList;
  const damaiReports = reportList.reports.filter((report) => report.stock_code === "DAMAI.SYN");
  expect(damaiReports.map((report) => report.period_label).sort()).toEqual(["FY2025", "FY2026"]);

  const periodsResponse = await page.request.get("/api/v1/operations/public-periods");
  expect(periodsResponse.ok()).toBeTruthy();
  const publicPeriodList = (await periodsResponse.json()) as PublicOperatingPeriodList;
  expect(publicPeriodList.periods).toHaveLength(7);
  const contexts = [
    ...damaiReports.map((report) => ({
      selectorValue: `report:${report.id}`,
      endpoint: `/api/v1/operations/overview/${report.id}`,
      label: `${report.company_name} ${report.period_label}`,
    })),
    ...publicPeriodList.periods.map((period) => ({
      selectorValue: `public:${period.stock_code}:${period.period_label}`,
      endpoint: `/api/v1/operations/public/${period.stock_code}/${period.period_label}`,
      label: `${period.company_name} ${period.period_label}`,
    })),
  ];
  expect(contexts).toHaveLength(9);
  await expect(select.locator("option")).toHaveCount(9, { timeout: 15_000 });

  for (const context of contexts) {
    const response = await page.request.get(context.endpoint);
    expect(response.ok(), `${context.label} API 返回成功`).toBeTruthy();
    const overview = (await response.json()) as OperationsOverview;
    expect(overview.themes, `${context.label} 恰有六主题`).toHaveLength(6);

    let renderedOverview: OperationsOverview;
    if (initialPath === context.endpoint) {
      // 保留初始请求对应的 UI 状态；重复选择当前值会触发 change 并清空视图，
      // 但 React 不会因 selectedContext 未变化而重新发起加载。
      renderedOverview = initialOverview;
    } else {
      const rendered = page.waitForResponse(
        (candidate) =>
          new URL(candidate.url()).pathname === context.endpoint &&
          candidate.request().method() === "GET",
      );
      await select.selectOption(context.selectorValue);
      const renderedResponse = await rendered;
      expect(renderedResponse.ok(), `${context.label} 页面请求返回成功`).toBeTruthy();
      renderedOverview = (await renderedResponse.json()) as OperationsOverview;
    }
    expect(renderedOverview).toEqual(overview);

    await expect(page.locator(".ops-overview__theme")).toHaveCount(overview.themes.length);
    await expectOperationsOverviewMatchesApi(page, overview);
  }
});

test("statements page lists damai synthetic reports", async ({ page }) => {
  test.setTimeout(90_000);
  await page.goto("/statements");
  await expect(
    page.getByRole("heading", { name: /公开财报.*分析/ }),
  ).toBeVisible();
  const tabs = page.locator("nav[aria-label='财报选择']");
  const fy2026 = tabs.getByRole("button", { name: /FY2026/ });
  await expect(fy2026).toBeVisible({ timeout: 15_000 });
  await expect(fy2026).toContainText("大麦物流");

  const listResponse = await page.request.get("/api/v1/statements");
  expect(listResponse.ok()).toBeTruthy();
  const reportList = (await listResponse.json()) as StatementReportList;
  const summary = reportList.reports.find(
    (report) => report.company_name === "大麦物流" && report.period_label === "FY2026",
  );
  expect(summary, "FY2026 报表必须来自真实隔离 API 列表").toBeDefined();

  const detailResponse = await page.request.get(`/api/v1/statements/${summary!.id}`);
  expect(detailResponse.ok()).toBeTruthy();
  const detail = (await detailResponse.json()) as StatementReportDetail;
  expect(detail.company_name).toBe(summary!.company_name);
  expect(detail.period_label).toBe(summary!.period_label);
  expect(detail.stock_code).toBe("DAMAI.SYN");
  expect(detail.source_ref).toContain("fixtures/damai/statements/");

  await fy2026.click();
  await expect(page.getByText("大麦物流", { exact: true }).first()).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText(/DAMAI\.SYN/).first()).toBeVisible();
  await expect(page.locator(".stmt-section")).toHaveCount(detail.sections.length);

  // 逐个 section、披露行、非空数值列对账：精确原值保存在 tooltip，页面值仅做合同单位缩放。
  for (const [sectionIndex, section] of detail.sections.entries()) {
    const uiSection = page.locator(".stmt-section").nth(sectionIndex);
    await expect(uiSection.locator("summary")).toContainText(section.statement_type);
    const uiRows = uiSection.locator("tbody tr");
    await expect(uiRows).toHaveCount(section.items.length);
    for (const [itemIndex, item] of section.items.entries()) {
      const uiRow = uiRows.nth(itemIndex);
      await expect(uiRow.locator("td").first()).toHaveText(item.item_name);
      for (const key of ["value_end", "value_begin", "value_current", "value_prior"] as const) {
        const exactValue = item[key];
        if (exactValue == null) continue;
        const uiCell = uiRow.locator(`[title="${exactValue}"]`);
        await expect(uiCell, `${section.statement_type}/${item.item_name}/${key}`).not.toHaveCount(0);
        await expect(uiCell.first()).toHaveText(formatStatementValue(exactValue, detail.unit_note));
      }
    }
  }
});

test("four-question workbench loads damai report", async ({ page }) => {
  await page.goto("/analysis");
  await expect(
    page.getByRole("heading", { name: "四问分析工作台" }),
  ).toBeVisible();
  const select = page.locator("#workbench-report");
  const fy2026Option = select.locator("option", { hasText: "FY2026" });
  await expect(fy2026Option).toHaveCount(1, { timeout: 15_000 });
  await expect(fy2026Option).toContainText("大麦物流");
  const value = await fy2026Option.getAttribute("value");
  expect(value).toBeTruthy();
  await select.selectOption(value!);
  await expect(page.locator(".workbench__identity")).toContainText("大麦物流", {
    timeout: 15_000,
  });
  await expect(page.getByRole("heading", { name: "四问指标" })).toBeVisible();
  const response = await page.request.get(`/api/v1/analysis/workbench/${value}`);
  expect(response.ok()).toBeTruthy();
  const body = (await response.json()) as WorkbenchResponse;
  const statementResponse = await page.request.get(`/api/v1/statements/${value}`);
  expect(statementResponse.ok()).toBeTruthy();
  const statement = (await statementResponse.json()) as StatementReportDetail;

  // 报告身份、四问及指标必须逐项来自本次真实大麦工作台 API，而不只是空壳渲染。
  expect(body.report.report_id).toBe(value);
  expect(body.report.company_name).toBe("大麦物流");
  expect(body.questions).toHaveLength(4);
  const allWorkbenchMetrics = body.questions.flatMap((question) => question.metrics);
  expect(allWorkbenchMetrics).toHaveLength(10);
  expect(
    allWorkbenchMetrics.filter((metric) => metric.available),
    "大麦 FY2026 财报披露了四问十项指标所需事实，十项都应可计算",
  ).toHaveLength(10);

  // 两个平均余额指标按字典口径，以财报原文的期初/期末余额和本期流量独立复算。
  const statementLine = (statementType: string, itemName: string) => {
    const section = statement.sections.find((candidate) => candidate.statement_type === statementType);
    expect(section, `${statementType} 存在`).toBeDefined();
    const line = section?.items.find((candidate) => candidate.item_name === itemName);
    expect(line, `${statementType}/${itemName} 原文行存在`).toBeDefined();
    return line!;
  };
  const requiredValue = (value: string | null | undefined, label: string) => {
    expect(value, `${label} 在大麦 FY2026 披露中存在`).not.toBeNull();
    return Number(value);
  };
  const revenueLine = statementLine("合并利润表", "营业收入");
  const netProfitLine = statementLine(
    "合并利润表",
    "五、净利润（净亏损以“－”号填列）",
  );
  const revenue = requiredValue(revenueLine.value_current, "营业收入");
  const revenuePrior = requiredValue(revenueLine.value_prior, "上期营业收入");
  const netProfit = requiredValue(netProfitLine.value_current, "净利润");
  const netProfitPrior = requiredValue(netProfitLine.value_prior, "上期净利润");
  const grossProfit = requiredValue(statementLine("合并利润表", "毛利").value_current, "毛利");
  const receivables = statementLine("合并资产负债表", "应收账款");
  const totalAssets = statementLine("合并资产负债表", "资产总计");
  const equity = statementLine("合并资产负债表", "所有者权益合计");
  const currentAssets = statementLine("合并资产负债表", "流动资产合计");
  const currentLiabilities = statementLine("合并资产负债表", "流动负债合计");
  const totalLiabilities = statementLine("合并资产负债表", "负债合计");
  const ocf = requiredValue(
    statementLine("合并现金流量表", "经营活动产生的现金流量净额").value_current,
    "经营活动现金流量净额",
  );
  const capex = requiredValue(
    statementLine(
      "合并现金流量表",
      "购建固定资产、无形资产和其他长期资产支付的现金",
    ).value_current,
    "资本开支",
  );
  const expectedDso = (
    (360 *
      ((requiredValue(receivables.value_end, "期末应收账款") +
        requiredValue(receivables.value_begin, "期初应收账款")) /
        2)) /
    revenue
  ).toFixed(4);
  const findMetric = (metricCode: string) =>
    body.questions.flatMap((question) => question.metrics).find((metric) => metric.metric_code === metricCode);
  expect(findMetric("dso_days")?.value, "DSO 要用 360 / 应收账款周转率（平均应收余额）").toBe(
    expectedDso,
  );
  const expectedByMetric: Record<string, string> = {
    revenue_growth: ((revenue - revenuePrior) / Math.abs(revenuePrior)).toFixed(4),
    net_profit_growth: ((netProfit - netProfitPrior) / Math.abs(netProfitPrior)).toFixed(4),
    gross_margin: (grossProfit / revenue).toFixed(4),
    net_margin: (netProfit / revenue).toFixed(4),
    roe: (
      netProfit /
      ((requiredValue(equity.value_end, "期末所有者权益") +
        requiredValue(equity.value_begin, "期初所有者权益")) /
        2)
    ).toFixed(4),
    debt_asset_ratio: (
      requiredValue(totalLiabilities.value_end, "期末负债合计") /
      requiredValue(totalAssets.value_end, "期末资产总计")
    ).toFixed(4),
    current_ratio: (
      requiredValue(currentAssets.value_end, "期末流动资产") /
      requiredValue(currentLiabilities.value_end, "期末流动负债")
    ).toFixed(4),
    dso_days: expectedDso,
    ocf_net_profit_ratio: (ocf / netProfit).toFixed(4),
    free_cash_flow: (ocf - capex).toFixed(4),
  };
  for (const [metricCode, expected] of Object.entries(expectedByMetric)) {
    expect(findMetric(metricCode)?.value, `${metricCode} 与报表披露及指标字典复算值一致`).toBe(
      expected,
    );
  }
  await expect(page.locator(".workbench__identity a")).toHaveAttribute(
    "href",
    `/statements?report=${encodeURIComponent(body.report.report_id)}`,
  );
  await expect(page.locator(".workbench__identity")).toContainText(body.report.period_label);
  await expect(page.locator(".workbench__identity")).toContainText(body.report.unit_note);

  const questionSections = page.locator(".workbench__question");
  await expect(questionSections).toHaveCount(body.questions.length);
  for (const [questionIndex, question] of body.questions.entries()) {
    const section = questionSections.nth(questionIndex);
    await expect(section.locator("h3")).toHaveText(question.name);
    const metricRows = section.locator("li");
    await expect(metricRows).toHaveCount(question.metrics.length);
    for (const [metricIndex, metric] of question.metrics.entries()) {
      const row = metricRows.nth(metricIndex);
      const codeLink = row.locator("a.workbench__metric-code");
      await expect(codeLink).toHaveText(metric.metric_code);
      await expect(codeLink).toHaveAttribute(
        "href",
        `/metric-library?focus=${encodeURIComponent(metric.metric_code)}`,
      );
      if (metric.available) {
        expect(metric.value, `${question.key}/${metric.metric_code} API可用值`).not.toBeNull();
        await expect(row.locator("strong")).toHaveText(metric.value!);
        await expect(row.locator(".workbench__muted")).toHaveCount(0);
      } else {
        expect(metric.value, `${question.key}/${metric.metric_code} 不可用时不得携带数值`).toBeNull();
        expect(metric.unavailable_reason, `${question.key}/${metric.metric_code} 应解释不可用原因`).toBeTruthy();
        await expect(row.locator("strong")).toHaveCount(0);
        await expect(row.locator(".workbench__muted")).toHaveText(
          `暂不可算（${metric.unavailable_reason}）`,
        );
      }
    }
  }

  // 管理关注不超过三条，提示方向、内容和指标定义深链须与同一 API 响应一致。
  expect(body.management_watch.length).toBeLessThanOrEqual(3);
  if (body.management_watch.length === 0) {
    await expect(page.getByText("本期无确定性提示信号。")).toBeVisible();
  } else {
    const watchRows = page.getByRole("list", { name: "管理关注" }).locator("li");
    await expect(watchRows).toHaveCount(body.management_watch.length);
    for (const [watchIndex, watch] of body.management_watch.entries()) {
      const row = watchRows.nth(watchIndex);
      await expect(row).toHaveAttribute("data-direction", watch.direction);
      await expect(row.locator("a")).toContainText(watch.message);
      await expect(row.locator("a")).toHaveAttribute(
        "href",
        `/metric-library?focus=${encodeURIComponent(watch.metric_code)}`,
      );
    }
  }
});

test("metric library switches to damai synthetic coverage", async ({ page }) => {
  const libraryRenderedResponse = page.waitForResponse(
    (response) => new URL(response.url()).pathname === "/api/v1/metric-library",
  );
  await page.goto("/metric-library");
  const libraryResponse = await libraryRenderedResponse;
  expect(libraryResponse.ok()).toBeTruthy();
  const library = (await libraryResponse.json()) as MetricLibrary;
  const libraryApiResponse = await page.request.get("/api/v1/metric-library");
  expect(libraryApiResponse.ok()).toBeTruthy();
  expect(await libraryApiResponse.json()).toEqual(library);
  // 覆盖矩阵在「真实财报覆盖」分区之下；next dev 冷编译路由需要时间，首个断言放宽
  const nav = page.locator("nav[aria-label='指标库分区']");
  await expect(nav.getByRole("button", { name: "真实财报覆盖" })).toBeVisible({ timeout: 60_000 });
  await expect(page.locator(".ml-hero__lede")).toContainText(library.dictionary_id);
  await expect(page.locator(".ml-hero__lede")).toContainText(`${library.report_items.length} 项 CAS↔IFRS 取数映射`);
  await expect(page.locator(".ml-kpis").locator(".ml-kpi__value").nth(0)).toContainText(
    String(library.metrics.filter((metric) => metric.collection === "general").length),
  );
  await expectMetricCardsMatchApi(page, library, "general");

  await nav.getByRole("button", { name: "物流行业指标" }).click();
  await expectMetricCardsMatchApi(page, library, "logistics");

  await nav.getByRole("button", { name: "行业参考包" }).click();
  await expectSupportingSectionsMatchApi(page, library, "industry");
  await nav.getByRole("button", { name: "勾稽与分解关系" }).click();
  await expectSupportingSectionsMatchApi(page, library, "relations");
  await nav.getByRole("button", { name: "取数映射（CAS↔IFRS）" }).click();
  await expectSupportingSectionsMatchApi(page, library, "mapping");
  await nav.getByRole("button", { name: "会计基础数据" }).click();
  await expectSupportingSectionsMatchApi(page, library, "accounting");

  // 切离并回到治理页，便于明确捕获页面发起的只读事件请求。
  await nav.getByRole("button", { name: "通用指标" }).click();
  const eventsReload = page.waitForResponse(
    (response) => new URL(response.url()).pathname === "/api/v1/metric-library/events",
  );
  await nav.getByRole("button", { name: "治理记录" }).click();
  const eventsResponse = await eventsReload;
  expect(eventsResponse.ok()).toBeTruthy();
  const events = (await eventsResponse.json()) as MetricGovernanceEventList;
  const eventsApiResponse = await page.request.get("/api/v1/metric-library/events");
  expect(eventsApiResponse.ok()).toBeTruthy();
  expect(await eventsApiResponse.json()).toEqual(events);
  const eventRows = page.locator("section[aria-label='指标治理记录'] table tbody tr");
  if (events.events.length === 0) {
    await expect(page.getByText("尚无治理事件。")).toBeVisible();
  } else {
    await expect(eventRows).toHaveCount(events.events.length);
    for (const [index, event] of events.events.entries()) {
      const row = eventRows.nth(index);
      await expect(row).toContainText(event.metric_code);
      await expect(row).toContainText(`v${event.version}`);
      await expect(row).toContainText(event.action);
      await expect(row).toContainText(event.operator);
      await expect(row).toContainText(event.reason);
    }
  }

  const publicRenderedResponse = page.waitForResponse(
    (response) => new URL(response.url()).pathname === "/api/v1/metric-library/coverage",
  );
  await nav.getByRole("button", { name: "真实财报覆盖" }).click();
  const publicResponse = await publicRenderedResponse;
  expect(publicResponse.ok()).toBeTruthy();
  const publicCoverage = (await publicResponse.json()) as MetricCoverage;
  const publicApiResponse = await page.request.get("/api/v1/metric-library/coverage");
  expect(publicApiResponse.ok()).toBeTruthy();
  expect(await publicApiResponse.json()).toEqual(publicCoverage);
  await expectMetricCoverageMatchesApi(page, publicCoverage);

  await expect(page.getByRole("tab", { name: "真实财报" })).toBeVisible({ timeout: 15_000 });
  const damaiRenderedResponse = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return url.pathname === "/api/v1/metric-library/coverage" && url.searchParams.get("dataset") === "damai";
  });
  await page.getByRole("tab", { name: "大麦演示" }).click();
  const damaiResponse = await damaiRenderedResponse;
  expect(damaiResponse.ok()).toBeTruthy();
  const damaiCoverage = (await damaiResponse.json()) as MetricCoverage;
  const damaiApiResponse = await page.request.get("/api/v1/metric-library/coverage?dataset=damai");
  expect(damaiApiResponse.ok()).toBeTruthy();
  expect(await damaiApiResponse.json()).toEqual(damaiCoverage);
  await expect(page.getByText("synthetic 演示 · 大麦物流")).toBeVisible({ timeout: 15_000 });
  await expectMetricCoverageMatchesApi(page, damaiCoverage);
  const matrix = page.locator("section[aria-label='指标覆盖矩阵']");
  await expect(matrix).toContainText("FY2026");
  // 直接核对年度覆盖值真正展示，而非只有年份标签/空壳矩阵。
  await expect(matrix).toContainText("FY2025");
  await expect(matrix).toContainText("37/40");
  await expect(matrix).toContainText("40/40");
});

test("approves the in-review revenue growth finding", async ({ page }) => {
  await page.goto("/investigations");
  await expect(page.getByRole("heading", { name: "分析与归因" })).toBeVisible();
  const row = page
    .getByRole("row")
    .filter({ hasText: "收入增长" })
    .filter({ hasText: "复核中" });
  await expect(row).toHaveCount(1, { timeout: 15_000 });
  await row.getByRole("link", { name: "进入调查" }).click();
  await expect(page).toHaveURL(/\/investigations\/[0-9a-f-]+/);
  await page.getByRole("button", { name: "批准签发" }).click();
  await expect(page.getByText("已签发").first()).toBeVisible({ timeout: 15_000 });
});

test("reports center mirrors api rows and values without mutation", async ({ page }) => {
  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: "报告中心" })).toBeVisible();

  // 客观财报分析报告（四表一注）：逐行对账 /api/v1/statements 的公司/期间/报告类型/行项目数与两条链接。
  const reportsResp = await page.request.get("/api/v1/statements");
  expect(reportsResp.ok()).toBeTruthy();
  const reportList = (await reportsResp.json()) as StatementReportList;
  expect(reportList.reports.length).toBeGreaterThan(0);
  const objectiveSection = page.locator("div.reports-center__objective").first();
  const objectiveRows = objectiveSection.locator("ul.reports-center__objective-list > li");
  await expect(objectiveRows).toHaveCount(reportList.reports.length);
  for (const [index, report] of reportList.reports.entries()) {
    const row = objectiveRows.nth(index);
    await expect(row).toContainText(
      `${report.company_name} · ${report.period_label} ${report.report_kind}（行项目 ${report.line_item_count}）`,
    );
    await expect(
      row.locator(`a[href="/api/v1/statements/${report.id}/objective-snapshot/html"]`),
    ).toHaveCount(1);
    await expect(row.getByRole("link", { name: "查看分析" })).toHaveAttribute(
      "href",
      `/statements?report=${encodeURIComponent(report.id)}`,
    );
  }

  // 经营分析报告（六主题）：逐行对账 /api/v1/operations/snapshots 的公司/期间/版本/指纹与深链。
  const opsResp = await page.request.get("/api/v1/operations/snapshots");
  expect(opsResp.ok()).toBeTruthy();
  const { snapshots: opsSnapshots } = (await opsResp.json()) as {
    snapshots: OperationsSnapshot[];
  };
  const opsRendered = opsSnapshots.filter(
    (row) => row.statement_report_id && row.company_name && row.payload_hash,
  );
  expect(opsRendered.length).toBeGreaterThan(0);
  const opsList = page.getByRole("list", { name: "经营报告快照列表" });
  await expect(opsList.locator("> li")).toHaveCount(opsRendered.length);
  for (const [index, snapshot] of opsRendered.entries()) {
    const row = opsList.locator("> li").nth(index);
    await expect(row).toContainText(
      `${snapshot.company_name} · ${snapshot.period_label} · v${snapshot.version} · 指纹 ${snapshot.payload_hash.slice(0, 12)}…`,
    );
    await expect(row.getByRole("link", { name: "在经营分析中查看" })).toHaveAttribute(
      "href",
      `/operations?report=${encodeURIComponent(snapshot.statement_report_id)}`,
    );
  }

  // 冻结候选：下拉选项逐项对账 /api/v1/publishing/freeze-candidates，含不可冻结禁用态。
  const candidatesResp = await page.request.get("/api/v1/publishing/freeze-candidates");
  expect(candidatesResp.ok()).toBeTruthy();
  const { candidates } = (await candidatesResp.json()) as { candidates: FreezeCandidate[] };
  expect(candidates.length).toBeGreaterThan(0);
  const freezeSelect = page.locator("div.reports-center__freeze select");
  await expect(freezeSelect.locator("option")).toHaveCount(candidates.length + 1);
  for (const [index, candidate] of candidates.entries()) {
    const option = freezeSelect.locator("option").nth(index + 1);
    await expect(option).toHaveText(
      `${candidate.period_label ?? "未知期间"} · 批次 ${candidate.batch_id.slice(0, 8)} · v${candidate.version} · 已批准发现 ${candidate.approved_findings}${candidate.approved_findings === 0 ? "（不可冻结）" : ""}`,
    );
    if (candidate.approved_findings === 0) {
      // 注：Playwright toBeDisabled 辅助器对 <option> 元素误报 enabled（DOM 中 disabled
      // 属性确实存在），故直接断言属性合同本身。
      await expect(option).toHaveAttribute("disabled");
    }
  }

  // 报告快照：逐行对账 /api/v1/publishing/snapshots 的版本/标题/日期。
  const snapshotsResp = await page.request.get("/api/v1/publishing/snapshots");
  expect(snapshotsResp.ok()).toBeTruthy();
  const { snapshots } = (await snapshotsResp.json()) as { snapshots: PublishingSnapshot[] };
  expect(snapshots.length).toBeGreaterThan(0);
  // 注：getByRole name 默认子串匹配，须 exact 才不会同时命中「经营报告快照列表」。
  const snapshotRows = page
    .getByRole("list", { name: "报告快照列表", exact: true })
    .locator("> li");
  await expect(snapshotRows).toHaveCount(snapshots.length);
  for (const [index, snapshot] of snapshots.entries()) {
    await expect(snapshotRows.nth(index)).toContainText(
      `v${snapshot.version} · ${snapshot.title} · ${(snapshot.created_at ?? "").slice(0, 10)}`,
    );
  }

  // 默认选中第一条报告快照：产物历史（append-only）表格与 attempts API 逐行逐格一致。
  const attemptsResp = await page.request.get(
    `/api/v1/publishing/snapshots/${snapshots[0].id}/attempts`,
  );
  expect(attemptsResp.ok()).toBeTruthy();
  const { attempts } = (await attemptsResp.json()) as { attempts: PublishingAttempt[] };
  const publishSection = page
    .locator("div.reports-center__publish")
    .filter({ has: page.getByRole("heading", { name: "生成产物" }) });
  const historyTable = publishSection.locator("table.flow-table");
  await expect(historyTable).toBeVisible();
  const attemptRows = historyTable.locator("tbody tr");
  await expect(attemptRows).toHaveCount(attempts.length);
  for (const [index, attempt] of attempts.entries()) {
    const row = attemptRows.nth(index);
    await expect(row).toContainText(String(attempt.sequence));
    await expect(row).toContainText(attempt.format);
    await expect(row).toContainText(attempt.status);
    await expect(row).toContainText(attempt.size_bytes === null ? "-" : String(attempt.size_bytes));
    if (attempt.download_available) {
      await expect(row.getByRole("button", { name: "下载" })).toHaveCount(1);
    }
  }
});

test("report center publishes operations artifact and download matches stored sha256", async ({
  page,
}) => {
  test.setTimeout(300_000);
  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: "报告中心" })).toBeVisible();
  const opsList = page.getByRole("list", { name: "经营报告快照列表" });
  await expect(opsList).toBeVisible({ timeout: 15_000 });
  await expect(opsList).toContainText("大麦物流");

  // 只生成 XLSX（默认还勾选 PPTX，取消以缩短门禁时长）
  const opsPublish = page
    .locator("div.reports-center__publish")
    .filter({ hasText: "生成经营报告产物" });
  await opsPublish.getByRole("checkbox", { name: "PPTX" }).uncheck();
  await opsPublish.getByRole("button", { name: "生成经营报告产物" }).click();
  await expect(
    opsPublish.getByRole("button", { name: "下载" }).first(),
  ).toBeVisible({ timeout: 180_000 });

  // SHA-256 对账：下载字节必须等于 attempt.stored_sha256
  const snapshotsResp = await page.request.get("/api/v1/operations/snapshots");
  expect(snapshotsResp.ok()).toBeTruthy();
  const { snapshots } = (await snapshotsResp.json()) as {
    snapshots: { id: string; company_name: string }[];
  };
  const damaiSnapshots = snapshots.filter((row) => row.company_name.includes("大麦"));
  expect(damaiSnapshots.length).toBeGreaterThan(0);

  type Attempt = {
    attempt_id: string;
    sequence: number;
    format: string;
    download_available: boolean;
    stored_sha256: string | null;
  };
  const attempts: Attempt[] = [];
  for (const snapshot of damaiSnapshots) {
    const resp = await page.request.get(`/api/v1/operations/snapshots/${snapshot.id}/attempts`);
    expect(resp.ok()).toBeTruthy();
    const body = (await resp.json()) as { attempts?: Attempt[] };
    attempts.push(...(body.attempts ?? []));
  }
  const downloadable = attempts
    .filter((attempt) => attempt.download_available && attempt.stored_sha256)
    .sort((a, b) => b.sequence - a.sequence);
  expect(downloadable.length).toBeGreaterThan(0);

  const attempt = downloadable[0];
  const download = await page.request.get(
    `/api/v1/publishing/attempts/${attempt.attempt_id}/download`,
  );
  expect(download.ok()).toBeTruthy();
  const buffer = await download.body();
  expect(buffer.length).toBeGreaterThan(0);
  const sha = createHash("sha256").update(buffer).digest("hex");
  expect(sha).toBe(attempt.stored_sha256);
});

// 上传旅程放最后：会在隔离库追加一个新批次/导入版本，不影响上述内容断言。
test("data workbench completes damai workbook upload journey", async ({ page }) => {
  test.setTimeout(300_000);
  await page.goto("/data");
  await expect(page.getByRole("heading", { name: "数据工作台" })).toBeVisible();

  // Seed 后不只验证上传：先确认已有批次能从页面发现，并通过链接恢复身份上下文。
  const history = page.getByRole("region", { name: "最近的数据批次" });
  await expect(history.getByRole("row")).toHaveCount(2, { timeout: 15_000 });
  const seededBatchRow = history.getByRole("row").nth(1);
  await expect(seededBatchRow).toContainText("damai-demo-v1");
  const seededBatchLink = seededBatchRow.getByRole("link");
  await expect(seededBatchLink).toHaveAttribute("href", /\/data\?batch=/);
  await seededBatchLink.click();
  await expect(page).toHaveURL(/\/data\?batch=/);
  await expect(history.getByRole("row").nth(1)).toHaveAttribute("data-current", "true");

  const fixture = path.resolve(
    __dirname,
    "../../../fixtures/damai/workbooks/damai_logistics_full_v1.xlsx",
  );
  await page.getByLabel("选择文件").setInputFiles(fixture);
  await expect(page.getByRole("table")).toBeVisible({ timeout: 30_000 });
  await page.getByRole("button", { name: "确认映射并校验" }).click();

  const cleaning = page.locator(".data-workbench__cleaning");
  await expect(
    page.getByRole("heading", { name: "清洗与校验结果" }),
  ).toBeVisible({ timeout: 120_000 });

  // 质量对账：无阻断、对账无失败
  await expect(cleaning).toContainText("阻断 0");
  await expect(cleaning).toContainText("失败 0");

  // 逐条确认警告（如有）：填确认原因 → 确认此警告 → 等该行收敛为“已确认”
  for (let step = 0; step < 30; step += 1) {
    const reasonInput = cleaning.locator("input[aria-label*='确认原因']").first();
    if ((await reasonInput.count()) === 0) break;
    const label = await reasonInput.getAttribute("aria-label");
    const issueId = (label ?? "").replace(/^警告\s*/, "").replace(/\s*确认原因$/, "");
    expect(issueId).not.toBe("");
    await reasonInput.fill("synthetic 演示数据，确认继续发布");
    await cleaning.getByRole("button", { name: `确认警告 ${issueId}` }).click();
    await expect(
      cleaning.getByRole("button", { name: `确认警告 ${issueId}` }),
    ).toHaveCount(0, { timeout: 15_000 });
  }

  const publishButton = page.getByRole("button", { name: "发布此导入版本" });
  await expect(publishButton).toBeEnabled({ timeout: 15_000 });
  await publishButton.click();
  await expect(
    page.getByRole("heading", { name: "导入版本已发布" }),
  ).toBeVisible({ timeout: 120_000 });
});
