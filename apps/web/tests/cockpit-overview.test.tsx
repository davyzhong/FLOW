import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { CockpitOverviewApp } from "../components/cockpit/cockpit-overview-app";
import type { CockpitOverviewResponse } from "../components/cockpit/cockpit-types";

function value(
  exact: string | null,
  display: string,
  direction: "positive" | "negative" | "neutral" = "positive",
) {
  return {
    status: (exact === null ? "unavailable" : "available") as
      | "available"
      | "unavailable"
      | "degraded",
    exact_value: exact,
    display_value: display,
    semantic_direction: direction,
    unavailable_code: exact === null ? "not_published" : undefined,
    unavailable_message: exact === null ? "未发布" : undefined,
  };
}

function overview(
  overrides: Partial<CockpitOverviewResponse> = {},
): CockpitOverviewResponse {
  return {
    state: "ready",
    context: {
      batch_id: "b1",
      import_version_id: "i1",
      metric_snapshot_id: "ms-12345678-rest",
      analysis_run_id: "ar1",
      as_of_month: "2026-06",
      metric_definition_set_id: "v1.2",
      metric_definition_set_hash: "a".repeat(64),
      metric_engine_version: "1.2.0",
      analysis_policy_id: "default",
      analysis_policy_hash: "b".repeat(64),
      analysis_engine_version: "1.2.0",
      generated_at: "2026-06-30T00:00:00Z",
    },
    data_status: {
      batch_status: "ready",
      import_status: "ready",
      quality_status: "passed",
      blocking_issue_count: 0,
      warning_issue_count: 0,
      acknowledged_warning_count: 0,
      reconciliation_status: "passed",
      metric_snapshot_status: "published",
      analysis_run_status: "published",
      freshness_status: "fresh",
    },
    kpi_cards: [
      {
        metric_code: "revenue",
        title: "营业收入",
        category: "收入",
        unit: "万元",
        primary: value("126895", "126,895"),
        comparisons: {
          yoy: value("112.6", "+12.6%"),
          mom: value(null, "—", "neutral"),
          percentile: value(null, "—", "neutral"),
        },
        polarity: "positive",
        control_status: "not_ready",
        control_line: null,
        caliber_note: "营业收入 · 由指标字典 v1.2 计算",
        source_label: "同比 +12.6%",
        snapshot_id: "ms-12345678-rest",
      },
    ],
    trends: [
      {
        status: "complete",
        unit: "万元",
        series: [
          {
            key: "revenue",
            title: "营业收入",
            unit: "万元",
            points: [
              { period: "2026-05", value: 90000, display_value: "90,000", status: "ready" },
              { period: "2026-06", value: 100000, display_value: "100,000", status: "ready" },
            ],
          },
        ],
        degradation_message: null,
      },
    ],
    conclusion: {
      text: "本期关注 1 项已终审发现：收入结构变化。",
      findings: [
        { id: "f-12345678", title: "收入结构变化", investigation_path: "/investigations/f-1" },
      ],
      tone: "neutral",
    },
    source_notice: "当前数据源为演示数据（大麦物流合成财报）。",
    ...overrides,
  };
}

describe("CockpitOverviewApp", () => {
  it("渲染驾驶舱结构：KPI 卡 + 趋势 + 结论条", async () => {
    const load = vi.fn().mockResolvedValue(overview());
    render(<CockpitOverviewApp load={load} />);
    await screen.findByTestId("cockpit-kpi");
    expect(screen.getByText("集团财务总览")).toBeTruthy();
    expect(screen.getByTestId("cockpit-trend")).toBeTruthy();
    expect(screen.getByTestId("cockpit-conclusion")).toBeTruthy();
  });

  it("展示演示数据源提示（不解除 C 级门禁）", async () => {
    const load = vi.fn().mockResolvedValue(overview());
    render(<CockpitOverviewApp load={load} />);
    const notice = await screen.findByTestId("cockpit-source-notice");
    expect(notice.textContent).toContain("演示数据");
  });

  it("KPI 卡展示三基准与口径注", async () => {
    const load = vi.fn().mockResolvedValue(overview());
    render(<CockpitOverviewApp load={load} />);
    await screen.findByTestId("cockpit-kpi");
    expect(screen.getByText("同比")).toBeTruthy();
    expect(screen.getByText("环比")).toBeTruthy();
    expect(screen.getByText("行业分位")).toBeTruthy();
    expect(screen.getByText(/指标字典 v1.2/)).toBeTruthy();
  });

  it("unavailable 基准显示为「—」而不是 0", async () => {
    const load = vi.fn().mockResolvedValue(overview());
    render(<CockpitOverviewApp load={load} />);
    await screen.findByTestId("cockpit-kpi");
    const card = screen.getByTestId("cockpit-kpi");
    expect(card.textContent).not.toContain("0.0%");
    expect(card.textContent?.includes("—")).toBe(true);
  });

  it("点击 KPI 卡打开穿透抽屉并显示快照 ID", async () => {
    const load = vi.fn().mockResolvedValue(overview());
    render(<CockpitOverviewApp load={load} />);
    const card = await screen.findByTestId("cockpit-kpi");
    fireEvent.click(screen.getByRole("button", { name: /营业收入/ }));
    const drawer = await screen.findByTestId("cockpit-drill");
    expect(drawer.textContent).toContain("ms-12345678-rest");
  });

  it("Esc 关闭穿透抽屉", async () => {
    const load = vi.fn().mockResolvedValue(overview());
    render(<CockpitOverviewApp load={load} />);
    await screen.findByTestId("cockpit-kpi");
    fireEvent.click(screen.getByRole("button", { name: /营业收入/ }));
    await screen.findByTestId("cockpit-drill");
    fireEvent.keyDown(window, { key: "Escape" });
    await waitFor(() => expect(screen.queryByTestId("cockpit-drill")).toBeNull());
  });

  it("无 snapshot_id 的 KPI 拒绝渲染数值（可追溯铁律）", async () => {
    const base = overview();
    const first = (base.kpi_cards ?? [])[0];
    const bad = overview({
      kpi_cards: first ? [{ ...first, snapshot_id: "" }] : [],
    });
    const load = vi.fn().mockResolvedValue(bad);
    render(<CockpitOverviewApp load={load} />);
    const el = await screen.findByTestId("cockpit-kpi-untraceable");
    expect(el.textContent).toContain("不可追溯");
  });

  it("empty 态提示不补零", async () => {
    const load = vi.fn().mockResolvedValue(overview({ kpi_cards: [], state: "empty" }));
    render(<CockpitOverviewApp load={load} />);
    const el = await screen.findByTestId("cockpit-empty");
    expect(el.textContent).toContain("不补零");
  });

  it("error 态提供重试", async () => {
    const load = vi.fn().mockRejectedValue(new Error("boom"));
    render(<CockpitOverviewApp load={load} />);
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("加载失败");
    expect(screen.getByRole("button", { name: "重试" })).toBeTruthy();
  });

  it("趋势不可用时显式提示而非画假线", async () => {
    const data = overview();
    data.trends = [
      {
        status: "degraded",
        unit: "万元",
        series: [
          {
            key: "revenue",
            title: "营业收入",
            unit: "万元",
            points: [],
          },
        ],
        degradation_message: null,
      },
    ];
    const load = vi.fn().mockResolvedValue(data);
    render(<CockpitOverviewApp load={load} />);
    const el = await screen.findByTestId("cockpit-trend-unavailable");
    expect(el.textContent).toContain("不补零");
  });

  it("筛选变更会写回 URL（可分享/可回链）", async () => {
    const load = vi.fn().mockResolvedValue(overview());
    render(<CockpitOverviewApp load={load} />);
    await screen.findByTestId("cockpit-kpi");
    const period = screen.getByLabelText("期间") as HTMLSelectElement;
    fireEvent.change(period, { target: { value: "month" } });
    await waitFor(() => expect(load).toHaveBeenCalledTimes(2));
    expect(window.location.search).toContain("period_view=month");
  });
});
