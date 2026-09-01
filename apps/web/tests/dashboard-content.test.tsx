import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import oracle from "../../../fixtures/expected/dashboard_overview_v1.json";
import { DashboardLoaded } from "../components/dashboard/dashboard-state";
import type { DashboardResponse } from "../lib/api/client";

const dashboard = oracle as DashboardResponse;

describe("Finance BP dashboard content", () => {
  it("renders the approved dense information architecture", () => {
    render(<DashboardLoaded dashboard={dashboard} />);

    expect(screen.getByRole("navigation", { name: "FLOW 工作流" })).toBeVisible();
    expect(screen.getByText("数据接入")).toBeVisible();
    expect(screen.getByText("经营总览")).toBeVisible();
    expect(screen.getByText("分析与归因")).toBeVisible();
    expect(screen.getByText("报告与导出")).toBeVisible();
    expect(screen.getAllByTestId("metric-card")).toHaveLength(8);
    expect(screen.getByRole("img", { name: "近 12 个月经营趋势" })).toBeVisible();
    expect(screen.getByRole("region", { name: "经营利润变动桥" })).toBeVisible();
    expect(screen.getAllByRole("link", { name: /进入调查/ })).toHaveLength(4);
    expect(screen.getByRole("table", { name: "产品经营表现" })).toBeVisible();
    expect(screen.getByRole("table", { name: "客户群与产品毛利矩阵" })).toBeVisible();
  });

  it("preserves filters, chart alternatives, and table anatomy", () => {
    render(<DashboardLoaded dashboard={dashboard} />);

    for (const label of ["期间", "组织", "客户群", "物流产品", "区域"]) {
      expect(screen.getByLabelText(label)).toBeVisible();
    }
    const trendTable = screen.getByRole("table", { name: "趋势数据明细" });
    expect(within(trendTable).getAllByRole("row")).toHaveLength(13);
    const productTable = screen.getByRole("table", { name: "产品经营表现" });
    expect(within(productTable).getAllByRole("row")).toHaveLength(9);
    expect(screen.getByText("同比口径")).toBeVisible();
  });
});
