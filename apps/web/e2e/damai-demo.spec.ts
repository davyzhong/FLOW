import { createHash } from "node:crypto";
import path from "node:path";

import { expect, test } from "@playwright/test";

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

  // 选中客户群粒度后驾驶舱按筛选重载
  await page.getByRole("combobox", { name: "客户群" }).selectOption({ label: DAMAI_SEGMENT });
  await expect(page).toHaveURL(/customer_segment_id=/);
  await expect(cards.first()).toBeVisible({ timeout: 30_000 });
});

test("dashboard API serves customer-grain overview", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("metric-card").first()).toBeVisible({ timeout: 30_000 });

  const overview = await page.request.get("/api/v1/dashboard/overview");
  expect(overview.ok()).toBeTruthy();
  const body = (await overview.json()) as {
    state: string;
    context: { batch_id: string };
    metric_cards: { metric_code: string; primary: { status: string; exact_value: string | null } }[];
    trends: {
      status: string;
      coverage_count: number;
      points: { operating_cash_flow: { status: string; exact_value: string | null } }[];
    };
    margin_matrix: {
      status: string;
      comparison_label: string;
      cells: {
        actual_margin: { status: string; exact_value: string | null };
        comparison: { status: string; exact_value: string | null };
      }[];
    };
    filter_options: {
      dimensions: { dimension: string; options: { id: string; name: string }[] }[];
    };
  };
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
  await page.goto("/operations");
  // next dev 冷编译路由需要时间，首个断言放宽
  await expect(page.getByRole("heading", { name: "经营分析概览" })).toBeVisible({ timeout: 60_000 });
  const select = page.locator("#operations-context");
  // FY2026 同时有「完整财报」与「公开经营披露」两个选项，选完整财报口径
  const fy2026 = select.locator("option", { hasText: "大麦物流 · FY2026 · 完整财报" });
  await expect(fy2026).toHaveCount(1, { timeout: 15_000 });
  await expect(fy2026).toContainText("大麦物流");
  const value = await fy2026.getAttribute("value");
  expect(value).toBeTruthy();
  await select.selectOption(value!);
  // 六主题概览载入大麦财报事实（缺失主题如实标注，不补造）
  await expect(page.getByRole("heading", { name: "六主题概览" })).toBeVisible({ timeout: 30_000 });
  expect(await page.locator("[aria-labelledby^='ops-theme-']").count()).toBe(6);
});

test("statements page lists damai synthetic reports", async ({ page }) => {
  await page.goto("/statements");
  await expect(
    page.getByRole("heading", { name: /公开财报.*分析/ }),
  ).toBeVisible();
  const tabs = page.locator("nav[aria-label='财报选择']");
  const fy2026 = tabs.getByRole("button", { name: /FY2026/ });
  await expect(fy2026).toBeVisible({ timeout: 15_000 });
  await expect(fy2026).toContainText("大麦物流");
  await fy2026.click();
  await expect(page.getByText(/DAMAI\.SYN/).first()).toBeVisible({ timeout: 15_000 });
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
  expect(await page.locator(".workbench__question").count()).toBe(4);
});

test("metric library switches to damai synthetic coverage", async ({ page }) => {
  await page.goto("/metric-library");
  // 覆盖矩阵在「真实财报覆盖」分区之下；next dev 冷编译路由需要时间，首个断言放宽
  const nav = page.locator("nav[aria-label='指标库分区']");
  await expect(nav.getByRole("button", { name: "真实财报覆盖" })).toBeVisible({ timeout: 60_000 });
  await nav.getByRole("button", { name: "真实财报覆盖" }).click();
  await expect(page.getByRole("tab", { name: "真实财报" })).toBeVisible({ timeout: 15_000 });
  await page.getByRole("tab", { name: "大麦演示" }).click();
  await expect(page.getByText("synthetic 演示 · 大麦物流")).toBeVisible({ timeout: 15_000 });
  const matrix = page.locator("section[aria-label='指标覆盖矩阵']");
  await expect(matrix).toContainText("FY2026");
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
