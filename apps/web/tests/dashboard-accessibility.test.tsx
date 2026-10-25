import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("../components/cockpit/charts/echarts-base", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../components/cockpit/charts/echarts-base")>()),
  ChartBox: ({ title }: { title: string }) => <div>{title}</div>,
}));

import oracle from "../../../fixtures/expected/dashboard_overview_v1.json";
import { AppShell } from "../components/shell/app-shell";
import { DashboardApp } from "../components/dashboard/dashboard-app";
import type { DashboardResponse } from "../lib/api/client";

const dashboard = oracle as DashboardResponse;

describe("Dashboard accessibility structure", () => {
  it("has one page heading and named landmark/content regions", async () => {
    render(
      <AppShell>
        <DashboardApp loadDashboard={async () => dashboard} />
      </AppShell>,
    );

    expect(await screen.findByRole("navigation", { name: "FLOW 工作流" })).toBeVisible();
    const skipLink = screen.getByRole("link", { name: "跳到主要内容" });
    expect(skipLink).toHaveAttribute("href", "#main-content");
    expect(screen.getByRole("main")).toHaveAttribute("id", "main-content");
    expect(
      screen.getByRole("heading", { name: "Finance BP 经营驾驶舱", level: 1 }),
    ).toBeVisible();
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByRole("main")).toBeVisible();
    expect(screen.getByRole("region", { name: "核心经营指标" })).toBeVisible();
    expect(screen.getByRole("region", { name: "重点经营发现" })).toBeVisible();
  });
});
