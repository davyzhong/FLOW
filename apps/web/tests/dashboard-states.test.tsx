import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it, vi } from "vitest";

import oracle from "../../../fixtures/expected/dashboard_overview_v1.json";
import { DashboardApp } from "../components/dashboard/dashboard-app";
import type { DashboardResponse } from "../lib/api/client";

const ready = oracle as DashboardResponse;

describe("Dashboard application states", () => {
  it("keeps financial calculation and raw-data access outside the browser", () => {
    const source = [
      "dashboard-app.tsx",
      "dashboard-state.tsx",
      "dashboard-format.ts",
    ]
      .map((file) =>
        readFileSync(join(process.cwd(), "components/dashboard", file), "utf8"),
      )
      .join("\n");

    expect(source).not.toMatch(/variance|grossProfit|calculateMetric/i);
    expect(source).not.toMatch(/source-record|canonical|metric-values/i);
  });

  it("keeps stable loading geometry until the dashboard resolves", () => {
    render(<DashboardApp loadDashboard={() => new Promise(() => undefined)} />);

    expect(screen.getByRole("status", { name: "正在加载经营驾驶舱" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Finance BP 经营驾驶舱" })).toBeVisible();
  });

  it("renders ready, empty, stale, and degraded states explicitly", async () => {
    const { rerender } = render(
      <DashboardApp loadDashboard={async () => ready} />,
    );
    expect(await screen.findByText("已发布经营数据")).toBeVisible();

    rerender(
      <DashboardApp
        loadDashboard={async () => ({ ...ready, state: "empty" })}
      />,
    );
    expect(await screen.findByText("尚无可展示的经营数据")).toBeVisible();

    rerender(
      <DashboardApp
        loadDashboard={async () => ({ ...ready, state: "stale" })}
      />,
    );
    expect(await screen.findByText("数据已陈旧，请检查最新发布批次")).toBeVisible();

    rerender(
      <DashboardApp
        loadDashboard={async () => ({ ...ready, state: "degraded" })}
      />,
    );
    expect(await screen.findByText("部分分析面板已降级")).toBeVisible();
  });

  it("shows a safe error and retries the same typed request", async () => {
    const load = vi
      .fn()
      .mockRejectedValueOnce(new Error("database details must stay private"))
      .mockResolvedValueOnce(ready);
    render(<DashboardApp loadDashboard={load} />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "经营驾驶舱暂时无法加载",
    );
    expect(screen.queryByText("database details must stay private")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "重试" }));

    await waitFor(() => expect(load).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("已发布经营数据")).toBeVisible();
  });
});
