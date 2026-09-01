import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import oracle from "../../../fixtures/expected/dashboard_overview_v1.json";
import { DashboardApp } from "../components/dashboard/dashboard-app";
import type { DashboardResponse } from "../lib/api/client";

const dashboard = oracle as DashboardResponse;

describe("Dashboard accessibility structure", () => {
  it("has one page heading and named landmark/content regions", async () => {
    render(<DashboardApp loadDashboard={async () => dashboard} />);

    expect(
      await screen.findByRole("heading", { name: "Finance BP 经营驾驶舱", level: 1 }),
    ).toBeVisible();
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByRole("main")).toBeVisible();
    expect(screen.getByRole("navigation", { name: "FLOW 工作流" })).toBeVisible();
    expect(screen.getByRole("region", { name: "核心经营指标" })).toBeVisible();
    expect(screen.getByRole("region", { name: "重点经营发现" })).toBeVisible();
  });
});
