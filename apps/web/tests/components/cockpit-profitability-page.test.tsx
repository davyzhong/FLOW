import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("../../components/cockpit/charts/echarts-base", () => ({
  ChartBox: ({ testId, title, ariaLabel, option }: { testId?: string; title: string; ariaLabel?: string; option?: unknown }) => <div data-testid={testId} data-chart-option={JSON.stringify(option)}>{title}<span role="img" aria-label={ariaLabel} /></div>,
  CHART_THEME: { blue: "#2563eb", navyLight: "#60a5fa", green: "#16a34a", red: "#dc2626", warn: "#d97706", gold: "#b45309", gray: "#b0b0b0", ink: "#0f172a", mut: "#64748b", line: "#e2e8f0", emerald: "#0d9488", sand: "#d9a441", navyDeep: "#1e3a5f", font: "test-sans" },
  SERIES_PALETTE: ["#2563eb", "#b45309", "#0d9488", "#60a5fa", "#d9a441", "#1e3a5f"],
  AXIS: {},
  TOOLTIP: {},
  legend: () => ({}),
}));

import { CockpitProfitabilityPage } from "../../components/cockpit/profitability-page";
import * as client from "../../lib/api/client";
import type { CockpitProfitabilityResponse } from "../../lib/api/client";

const metric = (code: string, value: string) => ({
  metric_code: code,
  status: "available",
  value,
  unit: code === "net_margin" || code === "roe" ? "%" : "倍",
  formula: `${code} 的已登记口径`,
  definition_version: "flow.metric_dictionary.v1",
  report_id: "report-current",
  snapshot_id: "snapshot-current",
  source_facts: code === "net_margin" ? [{
    item_id: "is.net_profit", row_id: "row-net-profit", statement_type: "income_statement",
    item_name: "净利润", page_number: 12, page_anchor: "table-cell", role: "flow", value: "15",
  }] : [],
});

const fixture: CockpitProfitabilityResponse = {
  module: "profitability",
  title: "盈利能力与杜邦分析",
  source_notice: "大麦物流演示数据。",
  periods: [
    {
      period: "FY2022",
      report_id: "report-prior",
      snapshot_id: "snapshot-prior",
      snapshot_version: 1,
      source_ref: "fixtures/damai/FY2022.yaml",
      metrics: [metric("roe", "0.20"), metric("net_margin", "0.10"), metric("total_asset_turnover", "1.00"), metric("equity_multiplier", "2.00")],
      consistency: { status: "passed", difference: "0", tolerance: "0.00000001" },
    },
    {
      period: "FY2023",
      report_id: "report-current",
      snapshot_id: "snapshot-current",
      snapshot_version: 1,
      source_ref: "fixtures/damai/FY2023.yaml",
      metrics: [metric("roe", "0.30"), metric("net_margin", "0.15"), metric("total_asset_turnover", "1.00"), metric("equity_multiplier", "2.00")],
      consistency: { status: "passed", difference: "0", tolerance: "0.00000001" },
    },
  ],
  unavailable: [],
};

describe("CockpitProfitabilityPage", () => {
  it("盈利能力图表保留合法的零值并与明细一致", async () => {
    const zeroFixture = structuredClone(fixture);
    const currentMargin = zeroFixture.periods?.[1].metrics?.find((item) => item.metric_code === "net_margin");
    if (currentMargin) currentMargin.value = "0";
    vi.spyOn(client.flowApi, "getCockpitProfitability").mockResolvedValue(zeroFixture);
    render(<CockpitProfitabilityPage />);

    expect(await screen.findAllByText("0.00%")).toHaveLength(2);
    const chart = screen.getByTestId("cockpit-profitability-roe-comparison");
    expect(chart.getAttribute("data-chart-option")).toContain('"data":[10,0]');
  });

  it("shows DuPont chart, period values, frozen lineage and metric deep links", async () => {
    const fetchSpy = vi.spyOn(client.flowApi, "getCockpitProfitability").mockResolvedValue(fixture);
    render(<CockpitProfitabilityPage />);

    expect(await screen.findAllByText("30.00%")).toHaveLength(2);
    expect(screen.getByTestId("cockpit-profitability-dupont")).toBeVisible();
    expect(screen.getByRole("img", { name: /杜邦关系图，期间FY2023.*单位百分比.*单位次.*单位倍/ })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /ROE 和净利率.*期间FY2022、FY2023，单位百分比/ })).toBeInTheDocument();
    expect(screen.getAllByText(/snapshot-current/).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: "指标口径与关系" }).map((link) => link.getAttribute("href"))).toContain("/metric-library?focus=net_margin");
    expect(screen.getAllByRole("link", { name: "来源财报" })).toHaveLength(8);
    expect(screen.getAllByRole("link", { name: "净利润行" })[0]).toHaveAttribute(
      "href", "/statements?report=report-prior#stmt-row-income_statement-净利润",
    );
    expect(fetchSpy).toHaveBeenCalledOnce();
  });
});
