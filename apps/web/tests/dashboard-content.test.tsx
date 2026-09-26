import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import oracle from "../../../fixtures/expected/dashboard_overview_v1.json";
import { AppShell } from "../components/shell/app-shell";
import { DashboardLoaded } from "../components/dashboard/dashboard-state";
import type { DashboardResponse } from "../lib/api/client";

const dashboard = oracle as DashboardResponse;

describe("Finance BP dashboard content", () => {
  it("renders the approved dense information architecture", () => {
    render(
      <AppShell>
        <DashboardLoaded dashboard={dashboard} />
      </AppShell>,
    );

    expect(screen.getByRole("navigation", { name: "FLOW 工作流" })).toBeVisible();
    expect(screen.getByText("内部经营分析")).toBeVisible();
    expect(screen.getByText("数据接入")).toBeVisible();
    expect(screen.getByText("经营总览")).toBeVisible();
    expect(screen.getByText("调查归因")).toBeVisible();
    expect(screen.getByText("报告与导出")).toBeVisible();
    expect(screen.getAllByTestId("metric-card")).toHaveLength(8);
    expect(screen.getByRole("img", { name: "近 12 个月经营趋势" })).toBeVisible();
    expect(screen.getByRole("region", { name: "经营利润变动桥" })).toBeVisible();
    expect(screen.getAllByRole("link", { name: /进入调查/ })).toHaveLength(4);
    expect(screen.getByRole("table", { name: "产品经营表现" })).toBeVisible();
    expect(screen.getByRole("table", { name: "客户群与产品毛利矩阵" })).toBeVisible();
  });

  it("preserves filters, chart alternatives, and table anatomy", () => {
    render(
      <AppShell>
        <DashboardLoaded dashboard={dashboard} />
      </AppShell>,
    );

    for (const label of ["期间", "组织", "客户群", "物流产品", "区域"]) {
      expect(screen.getByLabelText(label)).toBeVisible();
    }
    const trendTable = screen.getByRole("table", { name: "趋势数据明细" });
    expect(within(trendTable).getAllByRole("row")).toHaveLength(13);
    const productTable = screen.getByRole("table", { name: "产品经营表现" });
    expect(within(productTable).getAllByRole("row")).toHaveLength(9);
    expect(screen.getByText(/毛利实际覆盖 16\/16 格（客群 2\/2，产品 8\/8）/)).toBeVisible();
  });

  it("shows snapshot coverage when the master catalog contains unused dimensions", () => {
    const response: DashboardResponse = {
      ...dashboard,
      filter_options: {
        ...dashboard.filter_options,
        dimensions: dashboard.filter_options.dimensions.map((dimension) => {
          if (dimension.dimension === "logistics_product") {
            return {
              ...dimension,
              options: [
                ...dimension.options,
                { id: "unused-product", code: "P-99", name: "未纳入该快照的产品" },
              ],
            };
          }
          if (dimension.dimension === "customer_segment") {
            return {
              ...dimension,
              options: [
                ...dimension.options,
                { id: "unused-segment", code: "SEG-99", name: "未纳入该快照的客群" },
              ],
            };
          }
          return dimension;
        }),
      },
    };

    render(
      <AppShell>
        <DashboardLoaded dashboard={response} />
      </AppShell>,
    );

    expect(screen.getByText("有经营事实 8/9 个产品 · 比较：同比")).toBeVisible();
    expect(
      screen.getByText("比较：同比 · 毛利实际覆盖 16/27 格（客群 2/3，产品 8/9）"),
    ).toBeVisible();
  });

  it("explains empty dimension panels instead of rendering blank tables", () => {
    const response: DashboardResponse = {
      ...dashboard,
      product_table: {
        ...dashboard.product_table,
        status: "degraded",
        comparison_label: "不可用",
        rows: [],
        degradation_message: "当前已发布快照未提供产品经营事实",
      },
      margin_matrix: {
        ...dashboard.margin_matrix,
        status: "degraded",
        comparison_label: "不可用",
        rows: [],
        columns: [],
        cells: [],
        degradation_message: "当前已发布快照未提供客户群×产品毛利事实",
      },
    };

    render(
      <AppShell>
        <DashboardLoaded dashboard={response} />
      </AppShell>,
    );

    expect(screen.getByText("当前已发布快照未提供产品经营事实")).toBeVisible();
    expect(screen.getByText("当前已发布快照未提供客户群×产品毛利事实")).toBeVisible();
  });
});
