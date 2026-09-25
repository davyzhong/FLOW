import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import oracle from "../../../../fixtures/expected/dashboard_overview_v1.json";
import { DashboardApp } from "../../components/dashboard/dashboard-app";
import type { DashboardResponse } from "../../lib/api/client";

// 批次一 §2.1/§2.3：驾驶舱 initialFilters 从 searchParams 初始化且不被 replaceState 抹掉；
// 指标卡 / 趋势点 / bridge driver / 产品行 / 矩阵 / 状态条 / finding 标题全部落链接。

const ready = oracle as DashboardResponse;
const firstFinding = ready.findings[0];
const firstPoint = ready.trends.points[0];
const firstRow = ready.product_table.rows[0];
const matrixRow = ready.margin_matrix.rows[0];
const matrixColumn = ready.margin_matrix.columns[0];

function renderLoaded(initialFilters?: Parameters<typeof DashboardApp>[0]["initialFilters"]) {
  const loadDashboard = vi.fn().mockResolvedValue(ready);
  render(<DashboardApp loadDashboard={loadDashboard} initialFilters={initialFilters} />);
  return loadDashboard;
}

describe("驾驶舱深链", () => {
  it("initialFilters 随首次请求发出，且 URL 深链不被 replaceState 抹掉", async () => {
    window.history.replaceState(null, "", "/?region_id=region-1");
    const loadDashboard = renderLoaded({ region_id: "region-1" });
    expect(await screen.findByText("已发布经营数据")).toBeVisible();
    expect(loadDashboard).toHaveBeenCalledWith(
      expect.objectContaining({ region_id: "region-1" }),
      expect.anything(),
    );
    expect(window.location.search).toContain("region_id=region-1");
    window.history.replaceState(null, "", "/");
  });

  it("加载失败且 URL 带筛选参数时给出针对性提示", async () => {
    const loadDashboard = vi.fn().mockRejectedValue(new Error("boom"));
    render(<DashboardApp loadDashboard={loadDashboard} initialFilters={{ region_id: "bad" }} />);
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("经营驾驶舱暂时无法加载");
    expect(alert).toHaveTextContent(/带有筛选参数/);
  });

  it("指标卡整卡链接到指标库 focus 深链", async () => {
    renderLoaded();
    expect(await screen.findByText("已发布经营数据")).toBeVisible();
    const card = screen.getAllByTestId("metric-card")[0];
    const link = within(card).getByRole("link");
    const code = ready.metric_cards[0].metric_code;
    expect(link).toHaveAttribute("href", `/metric-library?focus=${code}`);
  });

  it("finding 标题包链接到调查页（与「进入调查」同 href）", async () => {
    renderLoaded();
    expect(await screen.findByText("已发布经营数据")).toBeVisible();
    const titleLink = screen.getByRole("link", { name: firstFinding.title });
    expect(titleLink).toHaveAttribute("href", firstFinding.investigation_path);
  });

  it("状态条批次链接 /data?batch=，快照链接 /reports?focus=", async () => {
    renderLoaded();
    expect(await screen.findByText("已发布经营数据")).toBeVisible();
    const bar = screen.getByRole("status", { name: "数据治理状态" });
    const links = within(bar).getAllByRole("link");
    const hrefs = links.map((link) => link.getAttribute("href"));
    expect(hrefs).toContain(`/data?batch=${ready.context.batch_id}`);
    expect(hrefs).toContain(`/reports?focus=${ready.context.metric_snapshot_id}`);
  });

  it("趋势明细月份链接 /reports?focus={metric_snapshot_id}", async () => {
    renderLoaded();
    expect(await screen.findByText("已发布经营数据")).toBeVisible();
    const link = screen.getByRole("link", { name: firstPoint.month });
    expect(link).toHaveAttribute("href", `/reports?focus=${firstPoint.metric_snapshot_id}`);
  });

  it("利润桥 driver 链接到指标库 focus 深链", async () => {
    renderLoaded();
    expect(await screen.findByText("已发布经营数据")).toBeVisible();
    const bridge = screen.getByRole("region", { name: "经营利润变动桥" });
    const link = within(bridge).getAllByRole("link")[0];
    expect(link.getAttribute("href")).toMatch(/^\/metric-library\?focus=/);
  });

  it("产品行名称链接到驾驶舱自身筛选下钻", async () => {
    renderLoaded();
    expect(await screen.findByText("已发布经营数据")).toBeVisible();
    const table = screen.getByRole("table", { name: "产品经营表现" });
    const link = within(table).getByRole("link", { name: new RegExp(firstRow.name) });
    expect(link).toHaveAttribute(
      "href",
      `/?logistics_product_id=${firstRow.logistics_product_id}`,
    );
  });

  it("毛利矩阵单元格与维度头链接到驾驶舱筛选", async () => {
    renderLoaded();
    expect(await screen.findByText("已发布经营数据")).toBeVisible();
    const matrix = screen.getByRole("table", { name: "客户群与产品毛利矩阵" });
    const cellLink = within(matrix).getAllByRole("link").find((link) => {
      const href = link.getAttribute("href") ?? "";
      return href.includes(`customer_segment_id=${matrixRow.id}`) && href.includes(`logistics_product_id=${matrixColumn.id}`);
    });
    expect(cellLink).toBeDefined();
    const rowHead = within(matrix).getByRole("link", { name: matrixRow.name });
    expect(rowHead).toHaveAttribute("href", `/?customer_segment_id=${matrixRow.id}`);
    const columnHead = within(matrix).getByRole("link", { name: matrixColumn.name });
    expect(columnHead).toHaveAttribute("href", `/?logistics_product_id=${matrixColumn.id}`);
  });
});
